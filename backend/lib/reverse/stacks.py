# -*- coding: utf-8 -*-
"""抓 bb(133) 和 fin(137) 的 charCodeAt 调用栈，理清它们属于哪个函数阶段。
关键：fin 比 bb 多4字节，可能 fin = 某变换(bb)。看栈能知道 fin 的来源。
"""
import json
from cdp import CDP, get_douyin_page_ws

HOOK_JS = r"""
(async function(){
  const _on=Date.now,_or=Math.random,_OD=Date,_op=performance.now;
  Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
  window.Date=class extends _OD{constructor(...a){if(a.length===0)super(1700000000000);else super(...a);}static now(){return 1700000000000;}};

  const grabbed={};
  const seen=new Set();
  const origCCA=String.prototype.charCodeAt;
  String.prototype.charCodeAt=function(i){
    try{
      const s=this.toString();
      if(s.length>=120&&s.length<=145&&i===0){
        const key='L'+s.length;
        if(!grabbed[key]){
          grabbed[key]={len:s.length, codes:Array.from(s).map(c=>c.charCodeAt(0)), stack:(new Error().stack||'').split('\n').slice(1,6).join(' || ')};
        }
      }
    }catch(e){}
    return origCCA.call(this,i);
  };

  const base='https://www.douyin.com/aweme/v1/web/aweme/detail/';
  await new Promise((r)=>{const x=new XMLHttpRequest();x.open('GET',base+'?q=1',true);let d=false;x.onreadystatechange=function(){const fu=x.responseURL||'';if(!d&&fu.indexOf('a_bogus=')!==-1){d=true;r();try{x.abort();}catch(e){}}else if(x.readyState===4&&!d){d=true;r();}};x.send(null);setTimeout(()=>{if(!d){d=true;r();}},6000);});

  String.prototype.charCodeAt=origCCA;
  Date.now=_on;Math.random=_or;window.Date=_OD;performance.now=_op;
  return JSON.stringify(grabbed);
})()
"""

if __name__ == "__main__":
    ws_url, url = get_douyin_page_ws()
    cdp = CDP(ws_url)
    cdp.send("Runtime.enable")
    raw = cdp.eval(HOOK_JS, await_promise=True, timeout_ms=20000)
    cdp.close()
    if isinstance(raw, dict) and "__error__" in raw:
        print("ERR:", json.dumps(raw)[:400])
    else:
        g = json.loads(raw)
        for k, v in sorted(g.items()):
            print(f"\n{k} (len={v['len']}) head={v['codes'][:8]}")
            print("  stack:", v['stack'][:400])
        json.dump(g, open("lib/abogus_rebuild/stacks.json", "w"), indent=1)
