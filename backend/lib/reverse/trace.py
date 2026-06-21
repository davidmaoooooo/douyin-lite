# -*- coding: utf-8 -*-
"""在 Edge 抖音页面注入 hook，捕获 RC4 的完整 (输入,密钥,输出) 配对。
策略：hook Array.prototype.join（RC4 输出 cipher.join('')）和 charCodeAt（输入遍历），
配合时序，重建 bb->final 串联。
"""
import json
from cdp import CDP, get_douyin_page_ws

HOOK_JS = r"""
(async function(){
  const _on=Date.now,_or=Math.random,_OD=Date,_op=performance.now;
  Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
  window.Date=class extends _OD{constructor(...a){if(a.length===0)super(1700000000000);else super(...a);}static now(){return 1700000000000;}};

  let seq=0;
  const events=[];
  // hook Array.join 捕获 RC4 输出(字符数组 join(''))
  const origJoin=Array.prototype.join;
  Array.prototype.join=function(sep){
    try{
      if((sep===''||sep===undefined)&&this.length>=20&&this.length<=260&&this.every(x=>typeof x==='string'&&x.length<=1)){
        events.push({seq:seq++,type:'join',len:this.length,codes:this.map(c=>c.charCodeAt(0))});
      }
    }catch(e){}
    return origJoin.apply(this,arguments);
  };
  // hook charCodeAt 捕获被逐字符遍历的串(RC4/编码 输入)，带调用栈首帧
  const seen=new Set();
  const origCCA=String.prototype.charCodeAt;
  String.prototype.charCodeAt=function(i){
    try{
      const s=this.toString();
      if(s.length>=20&&s.length<=260&&i===0&&!seen.has(s)){
        seen.add(s);
        events.push({seq:seq++,type:'cca',len:s.length,codes:Array.from(s).map(c=>c.charCodeAt(0))});
      }
    }catch(e){}
    return origCCA.call(this,i);
  };

  const base='https://www.douyin.com/aweme/v1/web/aweme/detail/';
  await new Promise((r)=>{const x=new XMLHttpRequest();x.open('GET',base+'?q=1',true);let d=false;x.onreadystatechange=function(){const fu=x.responseURL||'';if(!d&&fu.indexOf('a_bogus=')!==-1){d=true;r();try{x.abort();}catch(e){}}else if(x.readyState===4&&!d){d=true;r();}};x.send(null);setTimeout(()=>{if(!d){d=true;r();}},6000);});

  Array.prototype.join=origJoin;
  String.prototype.charCodeAt=origCCA;
  Date.now=_on;Math.random=_or;window.Date=_OD;performance.now=_op;

  // === 在浏览器内直接验证 bb -> s4输入 的RC4关系 ===
  function rc4(data,key){var S=[];for(var i=0;i<256;i++)S[i]=i;var j=0;for(var i=0;i<256;i++){j=(j+S[i]+key[i%key.length])%256;var t=S[i];S[i]=S[j];S[j]=t;}var out=[];i=0;j=0;for(var k=0;k<data.length;k++){i=(i+1)%256;j=(j+S[i])%256;var t=S[i];S[i]=S[j];S[j]=t;out.push(data[k]^S[(S[i]+S[j])%256]);}return out;}
  const bb=events.find(e=>e.codes[0]===171&&e.codes[1]===85);
  const fin=events.find(e=>e.codes[0]===171&&e.codes[1]===87);
  const verify={bb_len:bb&&bb.len, fin_len:fin&&fin.len, hits:[]};
  if(bb&&fin){
    // 试 fin = head(N) + rc4(bb, key)  N=0..6, 多key
    const keys=[[0,1,8],[0,1,14],[0,1,0],[121],[0,1,2],[1,0,8]];
    for(const key of keys){
      const enc=rc4(bb.codes,key);
      for(let N=0;N<=6;N++){
        let ok=true;
        for(let i=0;i<enc.length;i++){ if(N+i>=fin.codes.length||fin.codes[N+i]!==enc[i]){ok=false;break;} }
        if(ok) verify.hits.push({key,N,note:'fin=head('+N+')+rc4(bb,'+key+')'});
      }
    }
    // 反过来: bb = rc4(fin部分)? 或 fin[N:] XOR rc4keystream
    // 也试 fin整体 = rc4(head++bb)? 先记录两端
    verify.bb_full=bb.codes; verify.fin_full=fin.codes;
  }
  return JSON.stringify({events, verify});
})()
"""

if __name__ == "__main__":
    ws_url, url = get_douyin_page_ws()
    cdp = CDP(ws_url)
    cdp.send("Runtime.enable")
    raw = cdp.eval(HOOK_JS, await_promise=True, timeout_ms=20000)
    cdp.close()
    if isinstance(raw, dict) and "__error__" in raw:
        print("JS ERROR:", json.dumps(raw, ensure_ascii=False)[:500])
    else:
        obj = json.loads(raw)
        events = obj["events"]
        verify = obj["verify"]
        print(f"captured {len(events)} events:")
        for e in events:
            print(f"  seq{e['seq']:2} {e['type']:5} len={e['len']:3} head={e['codes'][:10]}")
        print("\n=== RC4 verify bb->fin ===")
        print("bb_len:", verify.get("bb_len"), "fin_len:", verify.get("fin_len"))
        print("HITS:", json.dumps(verify.get("hits"), ensure_ascii=False))
        json.dump(obj, open("edge_trace.json", "w"), indent=1)
        print("saved edge_trace.json")
