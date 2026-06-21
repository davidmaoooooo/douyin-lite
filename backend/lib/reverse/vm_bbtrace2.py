# -*- coding: utf-8 -*-
"""一次完成: 触发签名记录 trace -> 立即在页面 JSON.stringify 成一个稳定字符串 ->
分块按字符串长度取回, 避免数组被后续请求清空。
"""
import json, time
from cdp2 import CDP, get_ws

def ev(cdp, expr, awaitp=False, timeout=40):
    r = cdp.cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": awaitp}, timeout=timeout)
    return r.get("result", {}).get("result", {}).get("value")

if __name__ == "__main__":
    cdp = CDP(get_ws())
    cdp.cmd("Runtime.enable"); cdp.cmd("Debugger.enable")
    sid=None; end=time.time()+8
    while time.time()<end and not sid:
        e=cdp.wait_event("Debugger.scriptParsed",timeout=2)
        if e and "bdms_1.0.1.19_fix.js" in e["params"].get("url",""): sid=e["params"]["scriptId"]
    print("scriptId:",sid)

    ev(cdp,"""(function(){if(window.__bb3)return;window.__bbcaps=[];var o=String.fromCharCode;
      String.fromCharCode=function(){try{if(arguments.length>=128&&arguments.length<=140)window.__bbcaps.push(Array.prototype.slice.call(arguments));}catch(e){}return o.apply(String,arguments);};window.__bb3=1;})()""")

    cond=("(function(){try{if(window.__rec&&window.__trace.length<260000){"
          "window.__trace.push([o[a],a,p,v[p],p>0?v[p-1]:null]);}}catch(e){}return false;})()")
    ev(cdp,"window.__trace=[];window.__rec=false;")
    bp=cdp.cmd("Debugger.setBreakpoint",{"location":{"scriptId":sid,"lineNumber":1,"columnNumber":131626},"condition":cond})
    print("logpoint:",bp.get("result",{}).get("breakpointId"))

    # 触发并在完成后立刻把 trace 冻结成字符串 window.__frozen
    r=ev(cdp,"""
    (async function(){
      Date.now=()=>1700000000000;Math.random=()=>0.5;if(performance)performance.now=()=>12345;
      window.__bbcaps=[];window.__trace=[];window.__rec=true;window.__frozen=null;
      var res= await new Promise(function(rs){
        var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);
        var d=false;
        x.onreadystatechange=function(){
          if(!d&&(x.responseURL||'').indexOf('a_bogus=')!==-1){d=true;window.__rec=false;rs('OK');try{x.abort();}catch(e){}}
          else if(x.readyState===4&&!d){d=true;window.__rec=false;rs('DONE');}
        };
        x.send(null);
        setTimeout(function(){if(!d){d=true;window.__rec=false;rs('TO');}},9000);
      });
      window.__frozen=JSON.stringify(window.__trace);
      window.__bbfrozen=JSON.stringify(window.__bbcaps);
      return res+':'+window.__trace.length+':'+window.__frozen.length;
    })()
    """, awaitp=True, timeout=45)
    print("trigger:",r)
    cdp.cmd("Debugger.removeBreakpoint",{"breakpointId":bp["result"]["breakpointId"]})

    flen = ev(cdp,"window.__frozen?window.__frozen.length:0")
    print("frozen str len:", flen)
    buf=""; CH=200000
    for off in range(0, flen, CH):
        part = ev(cdp, "window.__frozen.substr(%d,%d)"%(off,CH), timeout=30)
        if part is not None: buf+=part
    bbcaps=json.loads(ev(cdp,"window.__bbfrozen") or "[]")
    bb=None
    for c in bbcaps:
        if 130<=len(c)<=140: bb=c;break
    trace=json.loads(buf) if buf else []
    print("fetched trace:", len(trace), "bb:", len(bb) if bb else None)
    json.dump({"bb":bb,"trace":trace}, open("vm_bbtrace.json","w"))
    print("saved.")
    cdp.cmd("Debugger.disable"); cdp.close()
