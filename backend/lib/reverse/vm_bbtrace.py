# -*- coding: utf-8 -*-
"""读 VM 字节码反推 bb 序列化:
策略: hook String.fromCharCode 捕获 bb, 同时在 VM 主循环用日志断点记录
带操作数与栈顶的完整指令流 [op, a, p, stacktop2]。
然后定位 bb 各字节是哪条 push/store 产生、经过哪些位运算。
"""
import json, time
from cdp2 import CDP, get_ws

def ev(cdp, expr, awaitp=True, timeout=30):
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

    # 1) hook fromCharCode 捕获 bb
    ev(cdp, """
    (function(){
      if(window.__bb2) return;
      window.__bbcaps=[];
      var ofc=String.fromCharCode;
      String.fromCharCode=function(){
        try{if(arguments.length>=128&&arguments.length<=140)window.__bbcaps.push(Array.prototype.slice.call(arguments));}catch(e){}
        return ofc.apply(String,arguments);
      };
      window.__bb2=1;
    })()
    """, awaitp=False)

    # 2) VM 主循环日志断点: 记录 [op, a, p, v[p], v[p-1]]
    # 限量, 只记录后段(bb构造在末尾). 用 __rec 控制 + 限 250000
    cond=("(function(){try{if(window.__rec&&window.__trace.length<250000){"
          "window.__trace.push([o[a],a,p,v[p],p>0?v[p-1]:null]);}}catch(e){}return false;})()")
    ev(cdp,"window.__trace=[];window.__rec=false;",awaitp=False)
    bp=cdp.cmd("Debugger.setBreakpoint",{"location":{"scriptId":sid,"lineNumber":1,"columnNumber":131626},"condition":cond})
    print("logpoint:",bp.get("result",{}).get("breakpointId"))

    # 3) 触发(开启记录)
    r=ev(cdp,"""
    (async function(){
      Date.now=()=>1700000000000;Math.random=()=>0.5;if(performance)performance.now=()=>12345;
      window.__bbcaps=[];window.__trace=[];window.__rec=true;
      return await new Promise(function(res){
        var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);
        var d=false;
        x.onreadystatechange=function(){
          if(!d&&(x.responseURL||'').indexOf('a_bogus=')!==-1){d=true;window.__rec=false;res('OK:'+window.__trace.length);try{x.abort();}catch(e){}}
          else if(x.readyState===4&&!d){d=true;window.__rec=false;res('DONE:'+window.__trace.length);}
        };
        x.send(null);
        setTimeout(function(){if(!d){d=true;window.__rec=false;res('TO:'+window.__trace.length);}},10000);
      });
    })()
    """, timeout=40)
    print("trigger:",r)

    cdp.cmd("Debugger.removeBreakpoint",{"breakpointId":bp["result"]["breakpointId"]})
    # 取 bb
    caps=json.loads(ev(cdp,"JSON.stringify(window.__bbcaps)") or "[]")
    bb=None
    for c in caps:
        if 130<=len(c)<=140: bb=c;break
    print("bb len:", len(bb) if bb else None)
    total=ev(cdp,"window.__trace.length")
    print("trace total:",total)

    # 分批取 trace
    trace=[]; CH=15000
    for off in range(0,min(total or 0,250000),CH):
        part=ev(cdp,"JSON.stringify(window.__trace.slice(%d,%d))"%(off,off+CH),timeout=20)
        if part: trace.extend(json.loads(part))
    print("fetched trace:",len(trace))

    json.dump({"bb":bb,"trace":trace}, open("vm_bbtrace.json","w"))
    print("saved vm_bbtrace.json")
    cdp.cmd("Debugger.disable"); cdp.close()
