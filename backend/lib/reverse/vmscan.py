# -*- coding: utf-8 -*-
"""无条件断点 @e=v.slice落点, 程序侧过滤: 命中后读e.length, 长数组才dump, 否则快速resume.
限300次命中防卡死。找 bb/fin 在 VM 中的处理。
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
    print("scriptId:",sid)

    # 无条件断点在 n.apply 落点(131911, 已验证能命中且e在作用域)
    bp=cdp.cmd("Debugger.setBreakpoint",{"location":{"scriptId":sid,"lineNumber":1,"columnNumber":131903}})
    print("bp:",json.dumps(bp.get("result",{}),ensure_ascii=False)[:120])

    cdp.cmd("Runtime.evaluate",{"expression":"""
      (function(){Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
       var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);x.send(null);})()
    ""","awaitPromise":False},timeout=2)

    hits=[]; longhits=[]; n=0
    while n<400:
        pe=cdp.wait_event("Debugger.paused",timeout=6)
        if not pe: break
        n+=1
        cfid=pe["params"]["callFrames"][0]["callFrameId"]
        el=ev(cdp,cfid,"(typeof e!=='undefined'&&e&&typeof e.length==='number')?e.length:-1")
        if el is not None and el>=100 and el<200:
            nname=ev(cdp,cfid,"(typeof n==='function')?(n.name||n.toString().slice(0,40)):typeof n")
            ehead=ev(cdp,cfid,"JSON.stringify(Array.prototype.slice.call(e,0,8))")
            longhits.append({"i":n,"e_len":el,"n":nname,"e_head":ehead})
            print(f"[{n}] LONG e_len={el} n={str(nname)[:45]} e={ehead}")
        cdp.cmd("Debugger.resume",timeout=4)

    json.dump({"total":n,"long":longhits},open("lib/abogus_rebuild/vm_long.json","w"),ensure_ascii=False,indent=1)
    cdp.cmd("Debugger.disable"); cdp.close()
    print(f"\n命中{n}次, 其中长数组{len(longhits)}次 -> vm_long.json")
