# -*- coding: utf-8 -*-
"""核心：在 VM 原生调用点下条件断点，dump 处理长数组(bb/fin)时的 n(函数)/e(参数)。
揭示 bb->fin 经过的原生运算。
"""
import json
import time
from cdp2 import CDP, get_ws


def get_bdms_script(cdp):
    cdp.cmd("Runtime.enable")
    cdp.cmd("Debugger.enable")
    sid = None
    end = time.time() + 8
    while time.time() < end and not sid:
        ev = cdp.wait_event("Debugger.scriptParsed", timeout=2)
        if ev and "bdms_1.0.1.19_fix.js" in ev["params"].get("url", ""):
            sid = ev["params"]["scriptId"]
    return sid


def eval_on_frame(cdp, call_frame_id, expr):
    r = cdp.cmd("Debugger.evaluateOnCallFrame", {
        "callFrameId": call_frame_id, "expression": expr, "returnByValue": True
    })
    return r.get("result", {}).get("result", {}).get("value")


if __name__ == "__main__":
    cdp = CDP(get_ws())
    sid = get_bdms_script(cdp)
    print("scriptId:", sid)

    # 条件断点：仅当 e 是长度120-200的数组(处理 bb/fin)
    # bdms.js 有2行(行0是23字符注释)，n.apply 在 line=1 col=131903
    bp = cdp.cmd("Debugger.setBreakpoint", {
        "location": {"scriptId": sid, "lineNumber": 1, "columnNumber": 131903},
        "condition": "typeof e!=='undefined'&&e&&e.length>=120&&e.length<=200"
    })
    print("bp:", json.dumps(bp.get("result", {}), ensure_ascii=False)[:150])

    # 触发签名（不等返回，异步，让断点能在执行中命中）
    cdp.cmd("Runtime.evaluate", {"expression": """
      (function(){
        Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
        var x=new XMLHttpRequest();
        x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);
        x.send(null);
      })()
    """, "awaitPromise": False}, timeout=3)

    # 收集断点命中
    hits = []
    for _ in range(12):
        ev = cdp.wait_event("Debugger.paused", timeout=8)
        if not ev:
            break
        frames = ev["params"]["callFrames"]
        top = frames[0]
        cfid = top["callFrameId"]
        # 读 n(函数源码前80字符) 和 e(参数数组前后片段)
        n_src = eval_on_frame(cdp, cfid, "(typeof n==='function')?n.toString().slice(0,80):String(n)")
        e_len = eval_on_frame(cdp, cfid, "(e&&e.length)||0")
        e_head = eval_on_frame(cdp, cfid, "JSON.stringify((e||[]).slice(0,8))")
        hits.append({"n": n_src, "e_len": e_len, "e_head": e_head})
        print(f"HIT {len(hits)}: e_len={e_len} e_head={e_head} n={str(n_src)[:70]}")
        cdp.cmd("Debugger.resume", timeout=5)

    json.dump(hits, open("lib/abogus_rebuild/bp_hits.json", "w"), ensure_ascii=False, indent=1)
    cdp.cmd("Debugger.disable")
    cdp.close()
    print(f"\n共 {len(hits)} 次命中，已存 bp_hits.json")
