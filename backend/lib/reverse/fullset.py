# -*- coding: utf-8 -*-
"""一次签名抓全套: 3个SM3明文输入 + window_env串 + bb + fin。
用于 Python 正向构造 fin 并逐字节对比。
"""
import json
from cdp import CDP, get_douyin_page_ws

JS = r"""
(async function(){
  const _on=Date.now,_or=Math.random,_OD=Date,_op=performance.now;
  Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
  window.Date=class extends _OD{constructor(...a){if(a.length===0)super(1700000000000);else super(...a);}static now(){return 1700000000000;}};

  const euc=[]; const longs={};
  const origEUC=window.encodeURIComponent;
  window.encodeURIComponent=function(s){ if(typeof s==='string') euc.push(s); return origEUC.apply(this,arguments); };
  const origCCA=String.prototype.charCodeAt;
  String.prototype.charCodeAt=function(i){
    try{const s=this.toString();
      if(i===0&&s.length>=20&&s.length<=200){ const key='L'+s.length+'_'+s.charCodeAt(0)+'_'+s.charCodeAt(1); if(!longs[key]) longs[key]=Array.from(s).map(c=>c.charCodeAt(0)); }
    }catch(e){}
    return origCCA.call(this,i);
  };

  const base='https://www.douyin.com/aweme/v1/web/aweme/detail/';
  await new Promise((r)=>{const x=new XMLHttpRequest();x.open('GET',base+'?q=1',true);let d=false;x.onreadystatechange=function(){const fu=x.responseURL||'';if(!d&&fu.indexOf('a_bogus=')!==-1){d=true;window.__ab=decodeURIComponent((fu.match(/a_bogus=([^&]+)/)||[])[1]);r();try{x.abort();}catch(e){}}else if(x.readyState===4&&!d){d=true;r();}};x.send(null);setTimeout(()=>{if(!d){d=true;r();}},6000);});

  window.encodeURIComponent=origEUC; String.prototype.charCodeAt=origCCA;
  Date.now=_on;Math.random=_or;window.Date=_OD;performance.now=_op;
  return JSON.stringify({euc, longs, a_bogus: window.__ab});
})()
"""

if __name__ == "__main__":
    ws_url, _ = get_douyin_page_ws()
    cdp = CDP(ws_url)
    raw = cdp.eval(JS, await_promise=True, timeout_ms=20000)
    cdp.close()
    o = json.loads(raw)
    print("a_bogus:", str(o.get("a_bogus"))[:50], "... len", len(o.get("a_bogus") or ""))
    print("\nEUC调用(SM3明文输入):")
    for s in o["euc"]:
        print(f"  [{len(s)}] {s[:90]}")
    print("\n长字符串(charCodeAt遍历):")
    for k, v in o["longs"].items():
        print(f"  {k}: {v[:10]}")
    json.dump(o, open("lib/abogus_rebuild/fullset.json", "w"), ensure_ascii=False, indent=1)
    print("\nsaved fullset.json")
