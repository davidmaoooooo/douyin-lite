# -*- coding: utf-8 -*-
"""单独取回已记录在页面的 __trace 与 __bbcaps。"""
import json, time
from cdp2 import CDP, get_ws

def ev(cdp, expr, timeout=20):
    r = cdp.cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True}, timeout=timeout)
    return r.get("result", {}).get("result", {}).get("value")

if __name__ == "__main__":
    cdp = CDP(get_ws())
    cdp.cmd("Runtime.enable")
    total = ev(cdp, "window.__trace ? window.__trace.length : -1")
    print("trace total:", total)
    caps = json.loads(ev(cdp, "window.__bbcaps?JSON.stringify(window.__bbcaps):'[]'") or "[]")
    bb=None
    for c in caps:
        if 130<=len(c)<=140: bb=c;break
    print("bb len:", len(bb) if bb else None, "ncaps", len(caps))

    trace=[]; CH=12000
    for off in range(0, total, CH):
        part = ev(cdp, "JSON.stringify(window.__trace.slice(%d,%d))"%(off,off+CH), timeout=25)
        if part: trace.extend(json.loads(part))
        print("  fetched", len(trace))
    json.dump({"bb":bb,"trace":trace}, open("vm_bbtrace.json","w"))
    print("saved, trace len", len(trace))
    cdp.close()
