# -*- coding: utf-8 -*-
"""单次签名抓齐配套: 完整query(从responseURL) + 3次SM3明文(EUC) + bb + fin。
确保都来自同一次签名, 用于Python端到端复现。
"""
import json
from cdp import CDP, get_douyin_page_ws

JS = r"""
(async function(){
  const _on=Date.now,_or=Math.random,_OD=Date,_op=performance.now;
  Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
  window.Date=class extends _OD{constructor(...a){if(a.length===0)super(1700000000000);else super(...a);}static now(){return 1700000000000;}};

  const euc=[]; const longs={};
  const oE=window.encodeURIComponent;
  window.encodeURIComponent=function(s){ if(typeof s==='string'&&s.length>2) euc.push(s); return oE.apply(this,arguments); };
  const oC=String.prototype.charCodeAt;
  String.prototype.charCodeAt=function(i){
    try{const s=this.toString();
      if(i===0&&s.length>=20&&s.length<=400){const k='L'+s.length+'_'+s.charCodeAt(0);if(!longs[k])longs[k]=Array.from(s).map(c=>c.charCodeAt(0));}
    }catch(e){}
    return oC.call(this,i);
  };

  const base='https://www.douyin.com/aweme/v1/web/aweme/detail/';
  // 用完整参数(含verifyFp/fp/msToken会被SDK自动加? 不,detail的query由我给)
  const q='device_platform=webapp&aid=6383&channel=channel_pc_web&aweme_id=7372484719365098803&pc_client_type=1&version_code=290100&version_name=29.1.0&cookie_enabled=true&platform=PC';
  let finalUrl='';
  await new Promise((r)=>{const x=new XMLHttpRequest();x.open('GET',base+'?'+q,true);let d=false;x.onreadystatechange=function(){const fu=x.responseURL||'';if(!d&&fu.indexOf('a_bogus=')!==-1){d=true;finalUrl=fu;r();try{x.abort();}catch(e){}}else if(x.readyState===4&&!d){d=true;r();}};x.send(null);setTimeout(()=>{if(!d){d=true;r();}},6000);});

  window.encodeURIComponent=oE; String.prototype.charCodeAt=oC;
  Date.now=_on;Math.random=_or;window.Date=_OD;performance.now=_op;
  return JSON.stringify({finalUrl, euc, longs});
})()
"""

if __name__ == "__main__":
    ws_url, _ = get_douyin_page_ws()
    cdp = CDP(ws_url)
    raw = cdp.eval(JS, await_promise=True, timeout_ms=20000)
    cdp.close()
    o = json.loads(raw)
    print("finalUrl:", o["finalUrl"][:120])
    a_bogus = ""
    import re
    m = re.search(r"a_bogus=([^&]+)", o["finalUrl"])
    if m:
        from urllib.parse import unquote
        a_bogus = unquote(m.group(1))
    print("a_bogus:", a_bogus[:40], "len", len(a_bogus))
    print("\nEUC(SM3明文):")
    for s in o["euc"]:
        print(f"  [{len(s)}] {s[:70]}")
    print("\nlongs(charCodeAt):")
    for k, v in o["longs"].items():
        print(f"  {k}: {v[:8]}")
    o["a_bogus"] = a_bogus
    json.dump(o, open("lib/abogus_rebuild/paired.json", "w"), ensure_ascii=False, indent=1)
    print("\nsaved paired.json")
