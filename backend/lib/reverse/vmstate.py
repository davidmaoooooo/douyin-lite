# -*- coding: utf-8 -*-
"""在 VM opcode0 取参数点 e=v.slice (line1 col131704) 下条件断点(e.length>120)。
命中时 dump: e(参数), n(函数名/源码), 以及 VM 栈 v 的长数组成员。
看 bb/fin 在 VM 执行中如何流转。
"""
import json, time
from cdp2 import CDP, get_ws

def ev(cdp, cfid, expr):
    r = cdp.cmd("Debugger.evaluateOnCallFrame", {"callFrameId": cfid, "expression": expr, "returnByValue": True}, timeout=8)
    res = r.get("result", {})
    if "exceptionDetails" in res: return "EXC:"+str(res.get("exceptionDetails",{}).get("text",""))[:40]
    return res.get("result", {}).get("value")

if __name__ == "__main__":
    cdp = CDP(get_ws())
    cdp.cmd("Runtime.enable"); cdp.cmd("Debugger.enable")
    sid=None; end=time.time()+8
    while time.time()<end and not sid:
        e=cdp.wait_event("Debugger.scriptParsed",timeout=2)
        if e and "bdms_1.0.1.19_fix.js" in e["params"].get("url",""): sid=e["params"]["scriptId"]
    print("scriptId:",sid)

    # 取参数点 e=v.slice @ line1 col131704
    bp=cdp.cmd("Debugger.setBreakpoint",{
        "location":{"scriptId":sid,"lineNumber":1,"columnNumber":131704},
        "condition":"typeof e!=='undefined'&&e&&e.length>120&&e.length<200"
    })
    print("bp:",json.dumps(bp.get("result",{}),ensure_ascii=False)[:140])

    cdp.cmd("Runtime.evaluate",{"expression":"""
      (function(){Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
       var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);x.send(null);})()
    ""","awaitPromise":False},timeout=2)

    hits=[]
    for _ in range(15):
        pe=cdp.wait_event("Debugger.paused",timeout=8)
        if not pe: break
        cfid=pe["params"]["callFrames"][0]["callFrameId"]
        n_name=ev(cdp,cfid,"(typeof n==='function')?(n.name||'anon'):typeof n")
        n_src=ev(cdp,cfid,"(typeof n==='function')?n.toString().slice(0,50):''")
        e_len=ev(cdp,cfid,"e.length")
        e_head=ev(cdp,cfid,"JSON.stringify(Array.prototype.slice.call(e,0,8))")
        # VM 栈 v 里所有长数组(找 bb/fin)
        v_info=ev(cdp,cfid,"(function(){try{var r=[];for(var k=0;k<v.length;k++){var it=v[k];if(it&&it.length>=120&&it.length<200&&typeof it!=='string')r.push(k+':arr'+it.length+':'+JSON.stringify(Array.prototype.slice.call(it,0,4)));else if(typeof it==='string'&&it.length>=120&&it.length<200)r.push(k+':str'+it.length);}return r.join(' | ');}catch(e){return 'verr'}})()")
        hits.append({"n_name":n_name,"n_src":n_src,"e_len":e_len,"e_head":e_head,"v":v_info})
        print(f"HIT{len(hits)} n={n_name} e_len={e_len} e={e_head}")
        print(f"   n_src={str(n_src)[:55]}")
        print(f"   v栈长数组: {str(v_info)[:200]}")
        cdp.cmd("Debugger.resume",timeout=5)

    json.dump(hits,open("lib/abogus_rebuild/vm_state.json","w"),ensure_ascii=False,indent=1)
    cdp.cmd("Debugger.disable"); cdp.close()
    print(f"\n{len(hits)} hits -> vm_state.json")
