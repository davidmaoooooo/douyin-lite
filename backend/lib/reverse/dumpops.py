# -*- coding: utf-8 -*-
"""静态反编译第1步: dump VM opcode 执行序列。
技巧: 日志断点——condition表达式记录 (opcode t, 指针a, 栈深p) 到全局数组, 返回false不暂停。
VM全速执行, 事后读全局数组得到完整 opcode trace。
"""
import json, time
from cdp2 import CDP, get_ws

if __name__ == "__main__":
    cdp = CDP(get_ws())
    cdp.cmd("Runtime.enable"); cdp.cmd("Debugger.enable")
    sid=None; end=time.time()+8
    while time.time()<end and not sid:
        e=cdp.wait_event("Debugger.scriptParsed",timeout=2)
        if e and "bdms_1.0.1.19_fix.js" in e["params"].get("url",""): sid=e["params"]["scriptId"]
    print("scriptId:",sid)

    # 初始化全局记录数组(在页面里)
    cdp.cmd("Runtime.evaluate", {"expression": "window.__trace=[]; window.__rec=true;"}, timeout=5)

    # 日志断点在 VM 主循环 var t=o[a++] @line1 col131626
    # condition: 记录 [o[a], a, p] 再返回false (不暂停)。限记录量防爆内存。
    cond = ("(function(){try{if(window.__rec&&window.__trace.length<200000){"
            "window.__trace.push([o[a],a,p]);}}catch(e){}return false;})()")
    bp = cdp.cmd("Debugger.setBreakpoint", {"location": {"scriptId": sid, "lineNumber": 1, "columnNumber": 131626}, "condition": cond})
    print("logpoint:", bp.get("result", {}).get("breakpointId"))

    # 触发签名(同步等完成)
    r = cdp.cmd("Runtime.evaluate", {"expression": """
      (async function(){Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
       window.__rec=true;
       return await new Promise((res)=>{var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);
       var d=false;x.onreadystatechange=function(){var fu=x.responseURL||'';if(!d&&fu.indexOf('a_bogus=')!==-1){d=true;window.__rec=false;res('OK:'+window.__trace.length);try{x.abort();}catch(e){}}else if(x.readyState===4&&!d){d=true;window.__rec=false;res('DONE:'+window.__trace.length);}};x.send(null);setTimeout(()=>{if(!d){d=true;window.__rec=false;res('TO:'+window.__trace.length);}},10000);});})()
    """, "awaitPromise": True, "returnByValue": True}, timeout=30)
    print("sign result:", r.get("result", {}).get("result", {}).get("value"))

    # 移除断点, 取回 trace
    cdp.cmd("Debugger.removeBreakpoint", {"breakpointId": bp["result"]["breakpointId"]})
    cnt = cdp.cmd("Runtime.evaluate", {"expression": "window.__trace.length", "returnByValue": True}, timeout=5)
    total = cnt.get("result", {}).get("result", {}).get("value", 0)
    print("trace length:", total)

    # 分批取(太大一次取不回)
    trace = []
    CHUNK = 20000
    for off in range(0, min(total, 200000), CHUNK):
        c = cdp.cmd("Runtime.evaluate", {"expression": f"JSON.stringify(window.__trace.slice({off},{off+CHUNK}))", "returnByValue": True}, timeout=15)
        part = c.get("result", {}).get("result", {}).get("value")
        if part:
            trace.extend(json.loads(part))
    print("fetched:", len(trace))
    json.dump(trace, open("lib/abogus_rebuild/opcode_dump.json", "w"))
    # opcode 频次统计
    from collections import Counter
    ops = Counter(t[0] for t in trace)
    print("opcode 频次(top20):", ops.most_common(20))
    cdp.cmd("Debugger.disable"); cdp.close()
