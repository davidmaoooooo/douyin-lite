# -*- coding: utf-8 -*-
"""确认 bb->fin 是 RC4 (异或间隔恒为63)。
在 RC4 异或 opcode(70) 处断点, dump 栈和作用域, 抓 RC4 的 S盒/data/key。
异或opcode在指针a=271附近(从trace: [70,271,4])。
"""
import json, time
from cdp2 import CDP, get_ws

def ev(cdp, cfid, expr):
    r = cdp.cmd("Debugger.evaluateOnCallFrame", {"callFrameId": cfid, "expression": expr, "returnByValue": True}, timeout=8)
    return r.get("result", {}).get("result", {}).get("value")

if __name__ == "__main__":
    cdp = CDP(get_ws())
    cdp.cmd("Runtime.enable"); cdp.cmd("Debugger.enable")
    sid=None; end=time.time()+8
    while time.time()<end and not sid:
        e=cdp.wait_event("Debugger.scriptParsed",timeout=2)
        if e and "bdms_1.0.1.19_fix.js" in e["params"].get("url",""): sid=e["params"]["scriptId"]
    print("scriptId:",sid)

    # 异或 opcode 在 VM 主循环执行, opcode=70 的处理在 d() 里 "v[p]=v[p]^w" 那段
    # 找 ^w 的源码位置下断点
    src=open("lib/abogus_rebuild/bdms_1.0.1.19_fix.js",encoding="utf-8",errors="replace").read()
    # opcode70: 70===t?(w=v[p--],v[p]=v[p]^w)
    import re
    m=src.find("v[p]=v[p]^w")
    print("v[p]^w @",m)
    col=m-(src[:m].rfind(chr(10))+1)
    ln=src[:m].count(chr(10))
    print("line/col:",ln,col)

    # 条件断点: 仅在RC4段(异或处理长data时). 用全局标志在bb出现后激活
    cdp.cmd("Runtime.evaluate",{"expression":"window.__rc4=0;"},timeout=3)
    bp=cdp.cmd("Debugger.setBreakpoint",{"location":{"scriptId":sid,"lineNumber":ln,"columnNumber":col}})
    print("bp:",bp.get("result",{}).get("breakpointId"))

    cdp.cmd("Runtime.evaluate",{"expression":"""
      (function(){Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
       var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);x.send(null);})()
    ""","awaitPromise":False},timeout=2)

    # 抓前几次异或命中, dump 栈v和作用域(找S盒256数组/key)
    for hit in range(5):
        pe=cdp.wait_event("Debugger.paused",timeout=8)
        if not pe: break
        cfid=pe["params"]["callFrames"][0]["callFrameId"]
        # dump 当前帧+上层帧的256长度数组(S盒)和短数组(key)
        info=ev(cdp,cfid,"(function(){try{var r={vp:v[p],w:v[p-1]||null,p:p};"
                "for(var k=0;k<v.length;k++){var it=v[k];if(it&&it.length===256)r['Sbox@'+k]=Array.prototype.slice.call(it,0,8);"
                "if(it&&typeof it!=='string'&&it.length>=3&&it.length<=20)r['key?@'+k]=Array.prototype.slice.call(it,0);}return JSON.stringify(r);}catch(e){return 'err'+e;}})()")
        print(f"XOR hit{hit}: {str(info)[:300]}")
        cdp.cmd("Debugger.resume",timeout=4)

    cdp.cmd("Debugger.disable"); cdp.close()
