# -*- coding: utf-8 -*-
"""断点抓 SM3 sum 的输出 u (真实哈希结果) + write 输入字节。
拼出精确的算法数据流，校准 Python 复现。
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

    # 两个断点: write入口(142304) 抓输入r, sum返回(143022) 抓输出u
    bp1=cdp.cmd("Debugger.setBreakpoint",{"location":{"scriptId":sid,"lineNumber":1,"columnNumber":142304}})
    bp2=cdp.cmd("Debugger.setBreakpoint",{"location":{"scriptId":sid,"lineNumber":1,"columnNumber":143022}})
    print("bp write:",bp1.get("result",{}).get("breakpointId"), "bp sum:",bp2.get("result",{}).get("breakpointId"))

    cdp.cmd("Runtime.evaluate",{"expression":"""
      (function(){Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
       var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);x.send(null);})()
    ""","awaitPromise":False},timeout=2)

    flow=[]
    for _ in range(40):
        pe=cdp.wait_event("Debugger.paused",timeout=6)
        if not pe: break
        cf=pe["params"]["callFrames"][0]
        cfid=cf["callFrameId"]
        col=cf["location"]["columnNumber"]
        if col<142400:  # write入口
            rlen=ev(cdp,cfid,"(r&&r.length)||0")
            rfull=ev(cdp,cfid,"JSON.stringify((r&&r.slice)?Array.prototype.slice.call(r,0):[])")
            flow.append({"t":"write","len":rlen,"bytes":json.loads(rfull) if rfull else []})
            print(f"WRITE len={rlen}")
        else:  # sum返回
            ufull=ev(cdp,cfid,"JSON.stringify((u&&u.slice)?Array.prototype.slice.call(u,0):[])")
            ub=json.loads(ufull) if ufull else []
            flow.append({"t":"sum_out","bytes":ub})
            print(f"SUM_OUT len={len(ub)} head={ub[:8]}")
        cdp.cmd("Debugger.resume",timeout=4)

    json.dump(flow,open("lib/abogus_rebuild/sm3_flow.json","w"),ensure_ascii=False,indent=1)
    cdp.cmd("Debugger.disable"); cdp.close()
    print(f"\n{len(flow)} events")
