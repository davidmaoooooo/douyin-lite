# -*- coding: utf-8 -*-
"""无条件断点 + 程序侧过滤：命中后读 e.length，只对 e.length>=120 的详细dump n/e/d。
记录 bb/fin 处理时 VM 调用的原生函数 n。
"""
import json
import time
from cdp2 import CDP, get_ws


def evalframe(cdp, cfid, expr):
    r = cdp.cmd("Debugger.evaluateOnCallFrame",
                {"callFrameId": cfid, "expression": expr, "returnByValue": True}, timeout=8)
    return r.get("result", {}).get("result", {}).get("value")


if __name__ == "__main__":
    cdp = CDP(get_ws())
    cdp.cmd("Runtime.enable")
    cdp.cmd("Debugger.enable")
    # 限制断点命中开销：用 Debugger.setBreakpoint 带 condition 过滤 e.length
    sid = None
    end = time.time() + 8
    while time.time() < end and not sid:
        ev = cdp.wait_event("Debugger.scriptParsed", timeout=2)
        if ev and "bdms_1.0.1.19_fix.js" in ev["params"].get("url", ""):
            sid = ev["params"]["scriptId"]
    print("scriptId:", sid)

    # 条件断点：e 是长数组。条件在断点实际落点(131911)求值，e 在作用域(已验证)
    bp = cdp.cmd("Debugger.setBreakpoint", {
        "location": {"scriptId": sid, "lineNumber": 1, "columnNumber": 131903},
        "condition": "e&&e.length>120&&e.length<200"
    })
    print("bp:", json.dumps(bp.get("result", {}), ensure_ascii=False)[:140])

    cdp.cmd("Runtime.evaluate", {"expression": """
      (function(){Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
       var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);x.send(null);})()
    """, "awaitPromise": False}, timeout=2)

    hits = []
    for _ in range(20):
        ev = cdp.wait_event("Debugger.paused", timeout=8)
        if not ev:
            break
        cfid = ev["params"]["callFrames"][0]["callFrameId"]
        n_src = evalframe(cdp, cfid, "(typeof n==='function')?(n.name+'|'+n.toString().slice(0,60)):String(n)")
        e_len = evalframe(cdp, cfid, "e.length")
        e_head = evalframe(cdp, cfid, "JSON.stringify(Array.prototype.slice.call(e,0,6))")
        d_info = evalframe(cdp, cfid, "(d&&d.length)?('arr['+d.length+']'):(typeof d)")
        hits.append({"n": n_src, "e_len": e_len, "e_head": e_head, "d": d_info})
        print(f"HIT{len(hits)} e_len={e_len} e_head={e_head} d={d_info}\n   n={str(n_src)[:75]}")
        cdp.cmd("Debugger.resume", timeout=5)

    json.dump(hits, open("lib/abogus_rebuild/vm_hits.json", "w"), ensure_ascii=False, indent=1)
    cdp.cmd("Debugger.disable")
    cdp.close()
    print(f"\n{len(hits)} hits saved to vm_hits.json")
