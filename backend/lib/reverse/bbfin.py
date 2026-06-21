# -*- coding: utf-8 -*-
"""验证 fin = RC4(head + bb, key) 假设。head可能是random_head或时间字节。
穷举: key候选 + head来源 + 是否整体RC4。
同时尝试: fin = result_encrypt前的某中间, bb是更早中间。
"""
import json
from cdp import CDP, get_douyin_page_ws

JS = r"""
(async function(){
  const _on=Date.now,_or=Math.random,_OD=Date,_op=performance.now;
  Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
  window.Date=class extends _OD{constructor(...a){if(a.length===0)super(1700000000000);else super(...a);}static now(){return 1700000000000;}};

  const grab={};
  const origCCA=String.prototype.charCodeAt;
  String.prototype.charCodeAt=function(i){
    try{const s=this.toString();
      if(s.length>=120&&s.length<=145&&i===0&&!grab['L'+s.length]) grab['L'+s.length]=Array.from(s).map(c=>c.charCodeAt(0));
    }catch(e){}
    return origCCA.call(this,i);
  };
  const base='https://www.douyin.com/aweme/v1/web/aweme/detail/';
  await new Promise((r)=>{const x=new XMLHttpRequest();x.open('GET',base+'?q=1',true);let d=false;x.onreadystatechange=function(){const fu=x.responseURL||'';if(!d&&fu.indexOf('a_bogus=')!==-1){d=true;r();try{x.abort();}catch(e){}}else if(x.readyState===4&&!d){d=true;r();}};x.send(null);setTimeout(()=>{if(!d){d=true;r();}},6000);});
  String.prototype.charCodeAt=origCCA;
  Date.now=_on;Math.random=_or;window.Date=_OD;performance.now=_op;

  function rc4(data,key){var S=[];for(var i=0;i<256;i++)S[i]=i;var j=0;for(var i=0;i<256;i++){j=(j+S[i]+key[i%key.length])%256;var t=S[i];S[i]=S[j];S[j]=t;}var out=[];i=0;j=0;for(var k=0;k<data.length;k++){i=(i+1)%256;j=(j+S[i])%256;var t=S[i];S[i]=S[j];S[j]=t;out.push(data[k]^S[(S[i]+S[j])%256]);}return out;}

  // 真实长度(去掉charCodeAt越界尾)
  let bb=grab['L133']; let fin=grab['L137'];
  if(!bb||!fin) return JSON.stringify({err:'missing', keys:Object.keys(grab)});
  bb=bb.filter(x=>x<256); fin=fin.filter(x=>x<256);

  const keys=[[0,1,8],[0,1,14],[121],[0,1,0],[0,1,2],[1],[8],[0,1,8,0]];
  const hits=[];
  // 假设A: fin = head(N) + rc4(bb, key)
  for(const key of keys) for(let N=0;N<=5;N++){
    const enc=rc4(bb,key); let ok=enc.length+N<=fin.length;
    for(let i=0;ok&&i<enc.length;i++) if(fin[N+i]!==enc[i]) ok=false;
    if(ok) hits.push('A:head('+N+')+rc4(bb,['+key+'])');
  }
  // 假设B: fin = rc4(head(N)+bb, key)  head取fin前N字节明文未知,跳过
  // 假设C: bb = rc4(fin?, key) 反向
  for(const key of keys) for(let N=0;N<=5;N++){
    const enc=rc4(fin.slice(N),key); let ok=enc.length<=bb.length;
    for(let i=0;ok&&i<enc.length&&i<bb.length;i++) if(bb[i]!==enc[i]) ok=false;
    if(ok&&enc.length>=bb.length-2) hits.push('C:bb=rc4(fin['+N+':],['+key+'])');
  }
  // 假设D: fin = rc4(bb全, key), 等长部分匹配(fin多4在末尾?)
  for(const key of keys){
    const enc=rc4(bb,key); let m=0; for(let i=0;i<bb.length;i++) if(fin[i]===enc[i]) m++;
    if(m>bb.length*0.9) hits.push('D:fin~=rc4(bb,['+key+']) match='+m+'/'+bb.length);
  }
  return JSON.stringify({bb_len:bb.length, fin_len:fin.length, bb:bb, fin:fin, hits});
})()
"""

if __name__ == "__main__":
    ws_url, _ = get_douyin_page_ws()
    cdp = CDP(ws_url); cdp.send("Runtime.enable")
    raw = cdp.eval(JS, await_promise=True, timeout_ms=20000)
    cdp.close()
    if isinstance(raw, dict) and "__error__" in raw:
        print("ERR:", json.dumps(raw)[:500])
    else:
        o = json.loads(raw)
        print("bb_len:", o.get("bb_len"), "fin_len:", o.get("fin_len"))
        print("HITS:", json.dumps(o.get("hits"), ensure_ascii=False))
        json.dump(o, open("lib/abogus_rebuild/bb_fin.json", "w"), indent=1)
