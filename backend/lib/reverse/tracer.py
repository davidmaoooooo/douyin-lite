# -*- coding: utf-8 -*-
"""VM opcode tracer: 在主循环分发点记录 opcode 序列。
用全局标志: 当 charCodeAt 遍历过 bb(171,85) 后开始记录 opcode t + 栈顶若干元素,
直到记录够 N 条或 fin 出现。揭示 bb->fin 的字节码运算。

注意: 不用断点(太慢), 改用注入式 tracer——重写 VM 用的关键操作不可行,
所以用 CDP Debugger 在主循环下断点, 但只在标志期记录, 用 condition 控制。
"""
import json, time
from cdp2 import CDP, get_ws

def ev(cdp, cfid, expr):
    r = cdp.cmd("Debugger.evaluateOnCallFrame", {"callFrameId": cfid, "expression": expr, "returnByValue": True}, timeout=8)
    return r.get("result", {}).get("result", {}).get("value")

if __name__ == "__main__":
    cdp = CDP(get_ws())
    cdp.cmd("Runtime.enable"); cdp.cmd("Debugger.enable")
    sid=None; end=time.time()+8
    while time.time()<end and not sid:
        e=cdp.wait_event("Debugger.scriptParsed",timeout=2)
        if e and "bdms_1.0.1.19_fix.js" in e["params"].get("url",""): sid=e["params"]["scriptId"]
    print("scriptId:",sid)

    # 先用全局标志记录"bb已出现". 注入一个 charCodeAt hook 设置 window.__bbseen
    # (只读, 安全) — 在签名前注入
    setup = """
      window.__bbseen=0; window.__finseen=0;
      if(!window.__ccaHooked){window.__ccaHooked=1;
        var o=String.prototype.charCodeAt;
        String.prototype.charCodeAt=function(i){
          try{if(i===0){var s=this;if(s.length>=120&&s.length<=145){
            if(s.charCodeAt(0)===171&&s.charCodeAt(1)===85)window.__bbseen=(window.__bbseen||0)+1;
            if(s.charCodeAt(0)===171&&s.charCodeAt(1)===87)window.__finseen=(window.__finseen||0)+1;
          }}}catch(e){}
          return o.call(this,i);
        };
      }
    """
    cdp.cmd("Runtime.evaluate", {"expression": setup}, timeout=5)

    # 主循环断点, 条件: bb已出现 且 fin未出现 (即在 bb->fin 之间)
    cond = "window.__bbseen>0 && window.__finseen===0"
    bp=cdp.cmd("Debugger.setBreakpoint",{"location":{"scriptId":sid,"lineNumber":1,"columnNumber":131626},"condition":cond})
    print("bp:",json.dumps(bp.get("result",{}),ensure_ascii=False)[:120])

    cdp.cmd("Runtime.evaluate",{"expression":"""
      (function(){Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
       var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);x.send(null);})()
    ""","awaitPromise":False},timeout=2)

    trace=[]
    for step in range(150):
        pe=cdp.wait_event("Debugger.paused",timeout=8)
        if not pe: break
        cfid=pe["params"]["callFrames"][0]["callFrameId"]
        # 读 opcode t (即将执行的), 指令指针a, 栈顶3元素摘要
        info=ev(cdp,cfid,"(function(){try{return JSON.stringify({t:o[a],a:a,p:p,"
              "top:(function(){var r=[];for(var z=Math.max(0,p-2);z<=p;z++){var it=v[z];"
              "if(it==null)r.push('null');else if(typeof it==='number')r.push('n'+it);"
              "else if(typeof it==='string')r.push('s'+it.length);"
              "else if(it.length!=null)r.push('a'+it.length);else r.push('o');}return r;})()});}catch(e){return 'err:'+e;}})()")
        trace.append(info)
        cdp.cmd("Debugger.resume",timeout=4)

    json.dump(trace,open("lib/abogus_rebuild/opcode_trace.json","w"),ensure_ascii=False,indent=1)
    cdp.cmd("Debugger.disable"); cdp.close()
    print(f"traced {len(trace)} opcodes")
    for t in trace[:50]: print(" ", t)
