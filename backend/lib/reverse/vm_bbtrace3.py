# -*- coding: utf-8 -*-
"""非阻塞触发版: 设断点 -> 非阻塞发请求 -> sleep 等签名完成 -> 冻结 -> 取回。"""
import json, time
from cdp2 import CDP, get_ws

def ev(cdp, expr, timeout=30):
    r = cdp.cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True}, timeout=timeout)
    return r.get("result", {}).get("result", {}).get("value")

if __name__ == "__main__":
    cdp = CDP(get_ws())
    cdp.cmd("Runtime.enable"); cdp.cmd("Debugger.enable")
    sid=None; end=time.time()+8
    while time.time()<end and not sid:
        e=cdp.wait_event("Debugger.scriptParsed",timeout=2)
        if e and "bdms_1.0.1.19_fix.js" in e["params"].get("url",""): sid=e["params"]["scriptId"]
    print("scriptId:",sid)

    ev(cdp,"""(function(){if(window.__bb4)return;window.__bbcaps=[];var o=String.fromCharCode;
      String.fromCharCode=function(){try{if(arguments.length>=128&&arguments.length<=140)window.__bbcaps.push(Array.prototype.slice.call(arguments));}catch(e){}return o.apply(String,arguments);};window.__bb4=1;})()""")

    cond=("(function(){try{if(window.__rec&&window.__trace.length<260000){"
          "var tp=v[p],tq=p>0?v[p-1]:null;"
          "window.__trace.push([o[a],a,p,(typeof tp==='number'?tp:null),(typeof tq==='number'?tq:null)]);}}catch(e){}return false;})()")
    ev(cdp,"window.__trace=[];window.__rec=false;window.__frozen='';")
    bp=cdp.cmd("Debugger.setBreakpoint",{"location":{"scriptId":sid,"lineNumber":1,"columnNumber":131626},"condition":cond})
    print("logpoint set")

    # 非阻塞触发
    ev(cdp,"""
      (function(){Date.now=()=>1700000000000;Math.random=()=>0.5;if(performance)performance.now=()=>12345;
       window.__bbcaps=[];window.__trace=[];window.__rec=true;
       var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);
       x.onreadystatechange=function(){if((x.responseURL||'').indexOf('a_bogus=')!==-1){window.__rec=false;try{x.abort();}catch(e){}}};
       x.send(null);
       setTimeout(function(){window.__rec=false;},6000);})()
    """)
    print("triggered, waiting 7s...")
    time.sleep(7)
    cdp.cmd("Debugger.removeBreakpoint",{"breakpointId":bp["result"]["breakpointId"]})

    tlen = ev(cdp,"window.__trace.length")
    print("trace len:", tlen)
    # 直接分批 slice 数组(避免一次性 stringify 整个超大数组)
    trace=[]; CH=8000
    for off in range(0, tlen, CH):
        part=ev(cdp,"JSON.stringify(window.__trace.slice(%d,%d))"%(off,off+CH),timeout=30)
        if part: trace.extend(json.loads(part))
    bbcaps=json.loads(ev(cdp,"JSON.stringify(window.__bbcaps)") or "[]")
    bb=None
    for c in bbcaps:
        if 130<=len(c)<=140: bb=c;break
    print("fetched:",len(trace),"bb:",len(bb) if bb else None)
    json.dump({"bb":bb,"trace":trace},open("vm_bbtrace.json","w"))
    print("saved.")
    cdp.cmd("Debugger.disable"); cdp.close()
