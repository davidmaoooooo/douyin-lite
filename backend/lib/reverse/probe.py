# -*- coding: utf-8 -*-
"""最小侵入探针：hook VM 会用到的安全原生函数，只在 bb(171,85) 出现后、fin(171,87) 前记录调用。
关键：不改返回值，try-catch 保护，先确认签名仍成功(fin出现)。
目标：看 bb->fin 之间 VM 调用了哪些原生运算。
"""
import json
from cdp import CDP, get_douyin_page_ws

JS = r"""
(async function(){
  const _on=Date.now,_or=Math.random,_OD=Date,_op=performance.now;
  Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
  window.Date=class extends _OD{constructor(...a){if(a.length===0)super(1700000000000);else super(...a);}static now(){return 1700000000000;}};

  let rec=false, finSeen=false;
  const ops=[];
  const origCCA=String.prototype.charCodeAt;
  String.prototype.charCodeAt=function(i){
    try{const s=this.toString();
      if(i===0&&s.length>=120&&s.length<=145){
        if(s.charCodeAt(0)===171&&s.charCodeAt(1)===85&&!rec){rec=true;ops.push({M:'BB',len:s.length});}
        else if(s.charCodeAt(0)===171&&s.charCodeAt(1)===87&&rec&&!finSeen){finSeen=true;ops.push({M:'FIN',len:s.length});}
      }
    }catch(e){}
    return origCCA.call(this,i);
  };
  // 安全hook: fromCharCode(数组转字符串), 不改返回值
  const origFCC=String.fromCharCode;
  String.fromCharCode=function(){
    if(rec&&!finSeen){ try{ if(arguments.length>=20&&arguments.length<=200){ ops.push({op:'fromCharCode',n:arguments.length,head:Array.prototype.slice.call(arguments,0,6)}); } }catch(e){} }
    return origFCC.apply(String,arguments);
  };
  // 安全hook: charAt(result_encrypt查表)
  const origCharAt=String.prototype.charAt;
  let charAtCount=0;
  String.prototype.charAt=function(i){
    if(rec&&!finSeen){ charAtCount++; }
    return origCharAt.call(this,i);
  };
  // 安全hook: Array.from
  const origAF=Array.from;
  Array.from=function(){ if(rec&&!finSeen){try{const r=origAF.apply(Array,arguments); if(r&&r.length>=20&&r.length<=200) ops.push({op:'Array.from',n:r.length,head:r.slice(0,6)}); return r;}catch(e){}} return origAF.apply(Array,arguments); };

  const base='https://www.douyin.com/aweme/v1/web/aweme/detail/';
  await new Promise((r)=>{const x=new XMLHttpRequest();x.open('GET',base+'?q=1',true);let d=false;x.onreadystatechange=function(){const fu=x.responseURL||'';if(!d&&fu.indexOf('a_bogus=')!==-1){d=true;r();try{x.abort();}catch(e){}}else if(x.readyState===4&&!d){d=true;r();}};x.send(null);setTimeout(()=>{if(!d){d=true;r();}},6000);});

  String.prototype.charCodeAt=origCCA; String.fromCharCode=origFCC; String.prototype.charAt=origCharAt; Array.from=origAF;
  Date.now=_on;Math.random=_or;window.Date=_OD;performance.now=_op;
  return JSON.stringify({bbSeen:rec, finSeen, charAtCount, ops});
})()
"""

if __name__ == "__main__":
    ws_url, _ = get_douyin_page_ws()
    cdp = CDP(ws_url)
    raw = cdp.eval(JS, await_promise=True, timeout_ms=20000)
    cdp.close()
    if isinstance(raw, dict) and "__error__" in raw:
        print("ERR:", json.dumps(raw)[:400])
    else:
        o = json.loads(raw)
        print("bbSeen:", o["bbSeen"], "finSeen:", o["finSeen"], "(签名成功且bb<fin顺序正确)" if o["finSeen"] else "(!! fin未出现,可能被破坏)")
        print("charAt调用数(bb->fin间):", o["charAtCount"])
        print("ops between bb->fin:")
        for e in o["ops"]:
            print(" ", json.dumps(e, ensure_ascii=False))
