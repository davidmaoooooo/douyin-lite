# -*- coding: utf-8 -*-
"""在 SM3 write 入口断点, dump 每次 SM3 哈希的输入字节数组 r。
揭示 bb/fin 是否进 SM3, 以及完整哈希调用序列。
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

    # SM3 write 入口 this.size+=r.length @ line1 col142304, r是字节数组
    bp=cdp.cmd("Debugger.setBreakpoint",{"location":{"scriptId":sid,"lineNumber":1,"columnNumber":142304}})
    print("bp:",json.dumps(bp.get("result",{}),ensure_ascii=False)[:120])

    cdp.cmd("Runtime.evaluate",{"expression":"""
      (function(){Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
       var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);x.send(null);})()
    ""","awaitPromise":False},timeout=2)

    writes=[]
    for _ in range(60):
        pe=cdp.wait_event("Debugger.paused",timeout=6)
        if not pe: break
        cfid=pe["params"]["callFrames"][0]["callFrameId"]
        rlen=ev(cdp,cfid,"(r&&r.length)||0")
        rhead=ev(cdp,cfid,"JSON.stringify((r&&r.slice)?Array.prototype.slice.call(r,0,8):[])")
        size=ev(cdp,cfid,"this.size")
        writes.append({"r_len":rlen,"r_head":rhead,"size_before":size})
        print(f"WRITE r_len={rlen} size_before={size} r_head={rhead}")
        cdp.cmd("Debugger.resume",timeout=4)

    json.dump(writes,open("lib/abogus_rebuild/sm3_writes.json","w"),ensure_ascii=False,indent=1)
    cdp.cmd("Debugger.disable"); cdp.close()
    print(f"\n{len(writes)} SM3 writes")
