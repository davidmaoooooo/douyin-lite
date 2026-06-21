# -*- coding: utf-8 -*-
"""智能条件断点 @VM主循环 opcode分发点(line1 col131626):
condition 扫描栈 v, 仅当栈上出现 fin(171,87开头长数组) 时暂停。
命中即 dump 栈上所有长数组(bb/fin/中间态), 一次看清 bb->fin 全貌。
"""
import json, time
from cdp2 import CDP, get_ws

def ev(cdp, cfid, expr):
    r = cdp.cmd("Debugger.evaluateOnCallFrame", {"callFrameId": cfid, "expression": expr, "returnByValue": True}, timeout=10)
    res=r.get("result", {})
    if "exceptionDetails" in res: return "EXC:"+str(res.get("exceptionDetails",{}))[:60]
    return res.get("result", {}).get("value")

if __name__ == "__main__":
    cdp = CDP(get_ws())
    cdp.cmd("Runtime.enable"); cdp.cmd("Debugger.enable")
    sid=None; end=time.time()+8
    while time.time()<end and not sid:
        e=cdp.wait_event("Debugger.scriptParsed",timeout=2)
        if e and "bdms_1.0.1.19_fix.js" in e["params"].get("url",""): sid=e["params"]["scriptId"]
    print("scriptId:",sid)

    # 条件: 栈v上存在 fin — 可能是字符串(charCodeAt遍历)或字节数组, 检测两种, 首2字节171,87
    cond=("(function(){try{for(var k=0;k<v.length;k++){var it=v[k];if(!it)continue;"
          "if(typeof it==='string'&&it.length>=130&&it.length<200&&it.charCodeAt(0)===171&&it.charCodeAt(1)===87)return true;"
          "if(typeof it!=='string'&&it.length>=130&&it.length<200&&it[0]===171&&it[1]===87)return true;}"
          "return false;}catch(e){return false;}})()")
    bp=cdp.cmd("Debugger.setBreakpoint",{"location":{"scriptId":sid,"lineNumber":1,"columnNumber":131626},"condition":cond})
    print("bp:",json.dumps(bp.get("result",{}),ensure_ascii=False)[:130])

    cdp.cmd("Runtime.evaluate",{"expression":"""
      (function(){Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
       var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);x.send(null);})()
    ""","awaitPromise":False},timeout=2)

    pe=cdp.wait_event("Debugger.paused",timeout=15)
    if not pe:
        print("未命中(fin可能未进栈或条件错)")
    else:
        cfid=pe["params"]["callFrames"][0]["callFrameId"]
        print("命中! dump 栈上所有长数组:")
        # dump 栈 v 上所有 length>=20 的数组/字符串
        dump=ev(cdp,cfid,"(function(){var r=[];for(var k=0;k<v.length;k++){var it=v[k];if(!it)continue;"
               "if(typeof it==='string'&&it.length>=20&&it.length<300){var b=[];for(var z=0;z<it.length;z++)b.push(it.charCodeAt(z));r.push({idx:k,len:it.length,kind:'str',bytes:b});}"
               "else if(typeof it!=='string'&&typeof it.length==='number'&&it.length>=20&&it.length<300){r.push({idx:k,len:it.length,kind:'arr',bytes:Array.prototype.slice.call(it,0)});}}"
               "return JSON.stringify(r);})()")
        try:
            arrs=json.loads(dump)
            print(f"栈上 {len(arrs)} 个长对象:")
            for a in arrs:
                print(f"  v[{a['idx']}] {a['kind']}({a['len']}): {a['bytes'][:12]}")
            json.dump(arrs,open("lib/abogus_rebuild/vm_stack_dump.json","w"),ensure_ascii=False,indent=1)
            print("saved vm_stack_dump.json")
        except Exception as ex:
            print("dump parse err:",ex,"raw:",str(dump)[:200])
        cdp.cmd("Debugger.resume",timeout=3)
    cdp.cmd("Debugger.disable"); cdp.close()
