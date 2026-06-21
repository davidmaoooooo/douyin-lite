# -*- coding: utf-8 -*-
"""严格同次签名内配对 bb/fin，彻底穷举 bb<->fin 变换。
含: random_head 可能在 bb 或 fin；RC4 key 候选扩大；正反向；result_encrypt。
"""
import json
from cdp import CDP, get_douyin_page_ws

JS = r"""
(async function(){
  const _on=Date.now,_or=Math.random,_OD=Date,_op=performance.now;
  Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
  window.Date=class extends _OD{constructor(...a){if(a.length===0)super(1700000000000);else super(...a);}static now(){return 1700000000000;}};

  // 同次签名内按序抓所有120-145长度串
  const arr=[]; const origCCA=String.prototype.charCodeAt;
  String.prototype.charCodeAt=function(i){
    try{const s=this.toString(); if(s.length>=120&&s.length<=145&&i===0){ arr.push(Array.from(s).map(c=>c.charCodeAt(0)).filter(x=>x<256)); }}catch(e){}
    return origCCA.call(this,i);
  };
  const base='https://www.douyin.com/aweme/v1/web/aweme/detail/';
  await new Promise((r)=>{const x=new XMLHttpRequest();x.open('GET',base+'?q=1',true);let d=false;x.onreadystatechange=function(){const fu=x.responseURL||'';if(!d&&fu.indexOf('a_bogus=')!==-1){d=true;r();try{x.abort();}catch(e){}}else if(x.readyState===4&&!d){d=true;r();}};x.send(null);setTimeout(()=>{if(!d){d=true;r();}},6000);});
  String.prototype.charCodeAt=origCCA;
  Date.now=_on;Math.random=_or;window.Date=_OD;performance.now=_op;

  function rc4core(data,key){var S=[];for(var i=0;i<256;i++)S[i]=i;var j=0;for(var i=0;i<256;i++){j=(j+S[i]+key[i%key.length])%256;var t=S[i];S[i]=S[j];S[j]=t;}var out=[];i=0;j=0;for(var k=0;k<data.length;k++){i=(i+1)%256;j=(j+S[i])%256;var t=S[i];S[i]=S[j];S[j]=t;out.push(data[k]^S[(S[i]+S[j])%256]);}return out;}

  const bb=arr.find(a=>a[0]===171&&a[1]===85);
  const fin=arr.find(a=>a[0]===171&&a[1]===87);
  if(!bb||!fin) return JSON.stringify({err:1,count:arr.length,firsts:arr.map(a=>a.slice(0,3))});

  const hits=[];
  // key候选: 1-3字节, 含常见
  const keys=[];
  for(const k of [0,1,2,8,14,121,160]) keys.push([k]);
  keys.push([0,1,8],[0,1,14],[0,1,0],[0,1,2],[1,0,8],[8,1,0],[0,1,8,0,1,14]);
  // A: fin = fin[0..N-1](head) + rc4(bb[M..], key)
  for(const key of keys) for(let N=0;N<=6;N++) for(let M=0;M<=6;M++){
    const src=bb.slice(M); const enc=rc4core(src,key);
    let ok=N+enc.length<=fin.length+2 && Math.abs((N+enc.length)-fin.length)<=2;
    let mm=0; for(let i=0;i<enc.length&&N+i<fin.length;i++){ if(fin[N+i]===enc[i]) mm++; }
    if(mm>=enc.length-1 && enc.length>100) hits.push('A N='+N+' M='+M+' key=['+key+'] match='+mm+'/'+enc.length);
  }
  // B: bb = bb[0..N-1] + rc4(fin[M..], key)  (反向)
  for(const key of keys) for(let N=0;N<=6;N++) for(let M=0;M<=6;M++){
    const src=fin.slice(M); const enc=rc4core(src,key);
    let mm=0; for(let i=0;i<enc.length&&N+i<bb.length;i++){ if(bb[N+i]===enc[i]) mm++; }
    if(mm>=Math.min(enc.length,bb.length-N)-1 && enc.length>100) hits.push('B N='+N+' M='+M+' key=['+key+'] match='+mm);
  }
  return JSON.stringify({bb_len:bb.length, fin_len:fin.length, bb, fin, hits, arrCount:arr.length});
})()
"""

if __name__ == "__main__":
    ws_url, _ = get_douyin_page_ws()
    cdp = CDP(ws_url); cdp.send("Runtime.enable")
    raw = cdp.eval(JS, await_promise=True, timeout_ms=25000)
    cdp.close()
    if isinstance(raw, dict) and "__error__" in raw:
        print("ERR:", json.dumps(raw)[:500])
    else:
        o = json.loads(raw)
        print(json.dumps({k: v for k, v in o.items() if k not in ("bb", "fin")}, ensure_ascii=False))
        json.dump(o, open("lib/abogus_rebuild/bb_fin2.json", "w"), indent=1)
