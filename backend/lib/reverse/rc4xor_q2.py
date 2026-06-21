# -*- coding: utf-8 -*-
"""抓所有 RC4 异或的 (input, keystream, output) 三元组。
v[p]=v[p]^w: 断点时 w已出栈但=之前的v[p+1]? 实际 w=v[p--]执行后v[p]还在。
在异或语句, 操作数: 明文=v[p](异或前), keystream=w。抓 v[p](结果前) 和 w。
按明文分组: UA段(77,111..) vs bb段。keystream序列就是答案。
"""
import json, time
from cdp2 import CDP, get_ws

def ev(cdp, cfid, expr):
    r = cdp.cmd("Debugger.evaluateOnCallFrame", {"callFrameId": cfid, "expression": expr, "returnByValue": True}, timeout=6)
    return r.get("result", {}).get("result", {}).get("value")

if __name__ == "__main__":
    cdp = CDP(get_ws())
    cdp.cmd("Runtime.enable"); cdp.cmd("Debugger.enable")
    sid=None; end=time.time()+8
    while time.time()<end and not sid:
        e=cdp.wait_event("Debugger.scriptParsed",timeout=2)
        if e and "bdms_1.0.1.19_fix.js" in e["params"].get("url",""): sid=e["params"]["scriptId"]

    src=open("lib/abogus_rebuild/bdms_1.0.1.19_fix.js",encoding="utf-8",errors="replace").read()
    # opcode70 源码: 70===t?(w=v[p--],v[p]=v[p]^w):...
    # 断点设在 w=v[p-- 之前(即opcode70 case开始), 这样 v[p]=明文 v[p-1]?
    # 实际更简单: 断在 v[p]=v[p]^w, 此时 w已是keystream, v[p]是明文. 结果=明文^w
    m=src.find("v[p]=v[p]^w")
    col=m-(src[:m].rfind(chr(10))+1); ln=src[:m].count(chr(10))
    bp=cdp.cmd("Debugger.setBreakpoint",{"location":{"scriptId":sid,"lineNumber":ln,"columnNumber":col}})
    print("bp:",bp.get("result",{}).get("breakpointId"))

    cdp.cmd("Runtime.evaluate",{"expression":"""
      (function(){Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
       var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=2',true);x.send(null);})()
    ""","awaitPromise":False},timeout=2)

    xors=[]  # (plain, ks)
    for hit in range(400):
        pe=cdp.wait_event("Debugger.paused",timeout=6)
        if not pe: break
        cfid=pe["params"]["callFrames"][0]["callFrameId"]
        # v[p]=明文, w=keystream(已在局部变量w). 取 v[p] 和 w
        pair=ev(cdp,cfid,"JSON.stringify([v[p],w])")
        if pair:
            try: xors.append(json.loads(pair))
            except: pass
        cdp.cmd("Debugger.resume",timeout=3)

    cdp.cmd("Debugger.disable"); cdp.close()
    print("总异或次数:",len(xors))
    # 明文序列
    plains=[x[0] for x in xors]
    kss=[x[1] for x in xors]
    print("明文序列[:20]:",plains[:20])
    print("明文序列[-20:]:",plains[-20:])
    # 找 bb 段(明文以171,85开头)
    for i in range(len(plains)-1):
        if plains[i]==171 and plains[i+1]==85:
            print(f"\n>>> bb段从异或#{i}开始!")
            print("bb段明文[:20]:",plains[i:i+20])
            print("bb段keystream[:20]:",kss[i:i+20])
            break
    json.dump({"plains":plains,"kss":kss}, open("lib/abogus_rebuild/rc4_xors_q2.json","w"))
    print("\nsaved rc4_xors_q2.json")
