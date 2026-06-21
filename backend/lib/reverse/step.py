# -*- coding: utf-8 -*-
"""断在VM主循环, 条件:栈v上有长度~132的字符串(bb)出现。命中后单步stepInto若干次,
dump每步的opcode和栈摘要, 看bb之后VM做什么。
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

    # 主循环 var t=o[a++] @ line1 col131626. 条件: 栈v上有 bb(长度130-134字符串, 171,85开头)
    cond=("(function(){try{for(var k=0;k<v.length;k++){var it=v[k];"
          "if(typeof it==='string'&&it.length>=130&&it.length<=134&&it.charCodeAt(0)===171&&it.charCodeAt(1)===85)return true;}"
          "return false;}catch(e){return false;}})()")
    bp=cdp.cmd("Debugger.setBreakpoint",{"location":{"scriptId":sid,"lineNumber":1,"columnNumber":131626},"condition":cond})
    print("bp:",json.dumps(bp.get("result",{}),ensure_ascii=False)[:120])

    cdp.cmd("Runtime.evaluate",{"expression":"""
      (function(){Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
       var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);x.send(null);})()
    ""","awaitPromise":False},timeout=2)

    pe=cdp.wait_event("Debugger.paused",timeout=15)
    if not pe:
        print("未命中(bb未以字符串形式进栈)")
    else:
        print("命中bb! 单步追踪opcode...")
        cfid=pe["params"]["callFrames"][0]["callFrameId"]
        # dump 当前栈上所有长对象
        snap=ev(cdp,cfid,"(function(){var r=[];for(var k=0;k<v.length;k++){var it=v[k];if(!it)continue;"
                "if(typeof it==='string'&&it.length>=20)r.push(k+':str'+it.length+':'+it.charCodeAt(0)+','+it.charCodeAt(1));"
                "else if(it.length>=20&&typeof it!=='string')r.push(k+':arr'+it.length);}return r.join(' | ');})()")
        print("栈快照:",snap)
        # 单步 stepInto 30次, 看opcode流(每步dump o[a]即下一opcode)
        steps=[]
        for s in range(30):
            t=ev(cdp,cfid,"({op:o[a],a:a,p:p})")
            steps.append(t)
            cdp.cmd("Debugger.stepInto",timeout=4)
            pe2=cdp.wait_event("Debugger.paused",timeout=5)
            if not pe2: break
            cfid=pe2["params"]["callFrames"][0]["callFrameId"]
        print("opcode steps:",json.dumps(steps,ensure_ascii=False)[:500])
        json.dump({"snap":snap,"steps":steps},open("lib/abogus_rebuild/step_trace.json","w"),ensure_ascii=False,indent=1)
    cdp.cmd("Debugger.resume",timeout=3)
    cdp.cmd("Debugger.disable"); cdp.close()
