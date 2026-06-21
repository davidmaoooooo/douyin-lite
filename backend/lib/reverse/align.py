# -*- coding: utf-8 -*-
"""深度分析 bb vs fin：逐字节对比、相同位、差异模式。
重点验证 agent 的洞察 fin[0]==bb[0]，看变换性质。
"""
import json
from cdp import CDP, get_douyin_page_ws

JS = r"""
(async function(){
  const _on=Date.now,_or=Math.random,_OD=Date,_op=performance.now;
  Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
  window.Date=class extends _OD{constructor(...a){if(a.length===0)super(1700000000000);else super(...a);}static now(){return 1700000000000;}};
  const arr=[]; const origCCA=String.prototype.charCodeAt;
  String.prototype.charCodeAt=function(i){
    try{const s=this.toString(); if(s.length>=120&&s.length<=145&&i===0){ arr.push(Array.from(s).map(c=>c.charCodeAt(0)).filter(x=>x<256)); }}catch(e){}
    return origCCA.call(this,i);
  };
  const base='https://www.douyin.com/aweme/v1/web/aweme/detail/';
  await new Promise((r)=>{const x=new XMLHttpRequest();x.open('GET',base+'?q=1',true);let d=false;x.onreadystatechange=function(){const fu=x.responseURL||'';if(!d&&fu.indexOf('a_bogus=')!==-1){d=true;r();try{x.abort();}catch(e){}}else if(x.readyState===4&&!d){d=true;r();}};x.send(null);setTimeout(()=>{if(!d){d=true;r();}},6000);});
  String.prototype.charCodeAt=origCCA;
  Date.now=_on;Math.random=_or;window.Date=_OD;performance.now=_op;
  const bb=arr.find(a=>a[0]===171&&a[1]===85);
  const fin=arr.find(a=>a[0]===171&&a[1]===87);
  return JSON.stringify({bb,fin,allFirsts:arr.map(a=>[a.length,a[0],a[1]])});
})()
"""

if __name__ == "__main__":
    ws_url, _ = get_douyin_page_ws()
    cdp = CDP(ws_url); cdp.send("Runtime.enable")
    raw = cdp.eval(JS, await_promise=True, timeout_ms=20000)
    cdp.close()
    o = json.loads(raw)
    bb, fin = o["bb"], o["fin"]
    print(f"bb len={len(bb)} fin len={len(fin)}")
    print("all captured:", o["allFirsts"])
    # 逐字节对比（对齐 offset 0）
    same = [i for i in range(min(len(bb), len(fin))) if bb[i] == fin[i]]
    print(f"\nsame-position bytes (offset0): {len(same)}/{min(len(bb),len(fin))} at {same[:30]}")
    # 尝试对齐 offset: fin 比 bb 多4，试 fin[4:] vs bb
    for off in range(0, 8):
        s = sum(1 for i in range(min(len(bb), len(fin)-off)) if bb[i] == fin[off+i])
        print(f"  fin[{off}:] vs bb same={s}/{min(len(bb),len(fin)-off)}")
    print("\nbb[:16] :", bb[:16])
    print("fin[:16]:", fin[:16])
    print("bb[-8:] :", bb[-8:])
    print("fin[-8:]:", fin[-8:])
    json.dump(o, open("lib/abogus_rebuild/bbfin_aligned.json", "w"))
