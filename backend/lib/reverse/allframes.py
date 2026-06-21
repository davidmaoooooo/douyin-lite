# -*- coding: utf-8 -*-
"""重打法: hook charCodeAt, 遇到 fin(171,87长串) 时触发 debugger 暂停。
命中后遍历 ALL callFrames 的 ALL scopes, 找 bb/fin 承载变量及来源函数。
"""
import json, time
from cdp2 import CDP, get_ws

def get_props(cdp, objid, limit=60):
    r = cdp.cmd("Runtime.getProperties", {"objectId": objid, "ownProperties": True}, timeout=8)
    out = []
    for p in r.get("result", {}).get("result", [])[:limit]:
        v = p.get("value", {})
        out.append((p["name"], v.get("type"), v.get("description", v.get("value", "")), v.get("objectId")))
    return out

if __name__ == "__main__":
    cdp = CDP(get_ws())
    cdp.cmd("Runtime.enable"); cdp.cmd("Debugger.enable")

    # 注入 hook: fin出现时 debugger; (只触发一次)
    setup = """
      window.__trap=0;
      (function(){
        var oc=String.prototype.charCodeAt;
        String.prototype.charCodeAt=function(i){
          try{ if(i===0 && !window.__trap){ var s=this;
            if(s.length>=135&&s.length<=138&&s.charCodeAt(0)===171&&s.charCodeAt(1)===87){
              window.__trap=1; String.prototype.charCodeAt=oc; debugger;
            }
          }}catch(e){}
          return oc.call(this,i);
        };
      })();
    """
    cdp.cmd("Runtime.evaluate", {"expression": setup}, timeout=5)

    # 触发签名
    cdp.cmd("Runtime.evaluate", {"expression": """
      (function(){Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
       var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);x.send(null);})()
    """, "awaitPromise": False}, timeout=2)

    pe = cdp.wait_event("Debugger.paused", timeout=15)
    if not pe:
        print("debugger 未触发(fin未被charCodeAt遍历或长度不符)")
    else:
        frames = pe["params"]["callFrames"]
        print(f"命中! 调用栈深度 {len(frames)} 帧")
        # 找第一个非 charCodeAt 的帧(真正的调用者)
        print("\n=== 各帧函数名(找非charCodeAt的真实调用者) ===")
        for fi, fr in enumerate(frames):
            fn = fr.get("functionName") or "(anon)"
            if "charCodeAt" not in fn:
                loc = fr.get("location", {})
                url = ""
                print(f"帧{fi}: {fn} @line{loc.get('lineNumber')} col{loc.get('columnNumber')}")
                if fi > 30:
                    break
        # dump 第一个非charCodeAt帧的作用域
        target = None
        for fi, fr in enumerate(frames):
            if "charCodeAt" not in (fr.get("functionName") or ""):
                target = (fi, fr); break
        report = []
        if target:
            fi, fr = target
            print(f"\n=== 真实调用者 帧{fi} {fr.get('functionName')} 的作用域 ===")
            for sc in fr.get("scopeChain", []):
                objid = sc.get("object", {}).get("objectId")
                if not objid: continue
                props = get_props(cdp, objid)
                for (nm, typ, desc, oid) in props:
                    d = str(desc)
                    if oid and ("Array(" in d or typ == "string"):
                        ln = cdp.cmd("Runtime.callFunctionOn", {"objectId": oid, "functionDeclaration": "function(){return (this&&this.length)||0}", "returnByValue": True}, timeout=5)
                        L = ln.get("result", {}).get("result", {}).get("value", 0)
                        if isinstance(L, int) and L >= 20:
                            h = cdp.cmd("Runtime.callFunctionOn", {"objectId": oid, "functionDeclaration": "function(){try{return (typeof this==='string')?[this.charCodeAt(0),this.charCodeAt(1),this.length]:[this[0],this[1],this.length]}catch(e){return []}}", "returnByValue": True}, timeout=5)
                            head = h.get("result", {}).get("result", {}).get("value", [])
                            print(f"  [{sc.get('type')}] {nm}: len={L} head={head}")
                            report.append({"scope": sc.get("type"), "name": nm, "len": L, "head": head})
        json.dump(report, open("lib/abogus_rebuild/allframes.json", "w"), ensure_ascii=False, indent=1)
        print("\nsaved allframes.json")
        cdp.cmd("Debugger.resume", timeout=3)
    cdp.cmd("Debugger.disable"); cdp.close()
