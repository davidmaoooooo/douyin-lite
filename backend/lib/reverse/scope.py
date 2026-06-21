# -*- coding: utf-8 -*-
"""无条件断点命中一次，dump 该作用域所有局部变量名+值预览，
确认 bb/fin 数据用哪个变量名承载。
"""
import json
import time
from cdp2 import CDP, get_ws


if __name__ == "__main__":
    cdp = CDP(get_ws())
    cdp.cmd("Runtime.enable")
    cdp.cmd("Debugger.enable")
    sid = None
    end = time.time() + 8
    while time.time() < end and not sid:
        ev = cdp.wait_event("Debugger.scriptParsed", timeout=2)
        if ev and "bdms_1.0.1.19_fix.js" in ev["params"].get("url", ""):
            sid = ev["params"]["scriptId"]
    print("scriptId:", sid)

    # 无条件断点
    bp = cdp.cmd("Debugger.setBreakpoint", {
        "location": {"scriptId": sid, "lineNumber": 1, "columnNumber": 131903},
    })
    print("bp:", json.dumps(bp.get("result", {}), ensure_ascii=False)[:150])

    # 触发签名
    cdp.cmd("Runtime.evaluate", {"expression": """
      (function(){Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
       var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);x.send(null);})()
    """, "awaitPromise": False}, timeout=2)

    # 命中第一次，dump scope
    ev = cdp.wait_event("Debugger.paused", timeout=10)
    if not ev:
        print("未命中断点！")
    else:
        top = ev["params"]["callFrames"][0]
        print("命中! 函数:", top.get("functionName", "?"))
        scopes = top.get("scopeChain", [])
        for sc in scopes[:3]:
            stype = sc.get("type")
            objid = sc.get("object", {}).get("objectId")
            if not objid:
                continue
            props = cdp.cmd("Runtime.getProperties", {"objectId": objid, "ownProperties": True})
            names = []
            for p in props.get("result", {}).get("result", [])[:40]:
                v = p.get("value", {})
                desc = v.get("description", v.get("value", ""))
                names.append(f"{p['name']}={str(desc)[:30]}")
            print(f"  scope[{stype}]: {names}")
    cdp.cmd("Debugger.resume", timeout=3)
    cdp.cmd("Debugger.disable")
    cdp.close()
