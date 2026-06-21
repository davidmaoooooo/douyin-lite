# -*- coding: utf-8 -*-
"""抓 VM 在 bb(132,以171,85开头) 出现后到 fin(136,171,87开头) 之间，
执行的所有原生函数调用(Function.prototype.apply/call 的方法名+参数特征)。
揭示 bb->fin 经过哪些运算。
"""
import json
from cdp import CDP, get_douyin_page_ws

JS = r"""
(async function(){
  const _on=Date.now,_or=Math.random,_OD=Date,_op=performance.now;
  Date.now=()=>1700000000000;Math.random=()=>0.5;performance.now=()=>12345;
  window.Date=class extends _OD{constructor(...a){if(a.length===0)super(1700000000000);else super(...a);}static now(){return 1700000000000;}};

  let recording=false, stop=false;
  const log=[];
  // 标记: 当 charCodeAt 命中 bb(171,85开头) 开始记录, 命中 fin(171,87) 停止
  const origCCA=String.prototype.charCodeAt;
  String.prototype.charCodeAt=function(i){
    try{const s=this.toString();
      if(i===0&&s.length>=120&&s.length<=145){
        if(s.charCodeAt(0)===171&&s.charCodeAt(1)===85){ recording=true; log.push({mark:'BB_START',len:s.length}); }
        if(s.charCodeAt(0)===171&&s.charCodeAt(1)===87){ if(recording){log.push({mark:'FIN_SEEN',len:s.length}); stop=true;} }
      }
    }catch(e){}
    return origCCA.call(this,i);
  };
  // hook 常见原生方法, 记录被调用(在recording期间)
  function wrap(obj, name, label){
    const orig=obj[name];
    obj[name]=function(){
      if(recording&&!stop){
        try{
          let info={fn:label, argc:arguments.length};
          if(name==='apply'){ const a=arguments[1]; info.applyArgc=a&&a.length; }
          if(arguments.length>=1 && typeof arguments[0]==='number') info.arg0=arguments[0];
          log.push(info);
        }catch(e){}
      }
      return orig.apply(this, arguments);
    };
    return ()=>{obj[name]=orig;};
  }
  const restores=[];
  // SM3 用位运算(hook不到), 但 RC4/数组操作可hook
  restores.push(wrap(Array.prototype,'slice','arr.slice'));
  restores.push(wrap(Array.prototype,'concat','arr.concat'));
  restores.push(wrap(Array.prototype,'push','arr.push'));
  restores.push(wrap(Array.prototype,'join','arr.join'));
  restores.push(wrap(String.prototype,'charAt','str.charAt'));
  restores.push(wrap(window,'encodeURIComponent','encodeURIComponent'));

  const base='https://www.douyin.com/aweme/v1/web/aweme/detail/';
  await new Promise((r)=>{const x=new XMLHttpRequest();x.open('GET',base+'?q=1',true);let d=false;x.onreadystatechange=function(){const fu=x.responseURL||'';if(!d&&fu.indexOf('a_bogus=')!==-1){d=true;r();try{x.abort();}catch(e){}}else if(x.readyState===4&&!d){d=true;r();}};x.send(null);setTimeout(()=>{if(!d){d=true;r();}},6000);});

  restores.forEach(f=>f());
  String.prototype.charCodeAt=origCCA;
  Date.now=_on;Math.random=_or;window.Date=_OD;performance.now=_op;

  // 压缩log: 统计各fn调用次数 + 顺序摘要
  const summary={};
  for(const e of log){ if(e.fn){ summary[e.fn]=(summary[e.fn]||0)+1; } }
  return JSON.stringify({total:log.length, summary, seq: log.slice(0,80)});
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
        print("total events:", o["total"])
        print("summary:", json.dumps(o["summary"], ensure_ascii=False))
        print("\nseq (bb->fin native calls):")
        for e in o["seq"][:60]:
            print(" ", json.dumps(e, ensure_ascii=False))
        json.dump(o, open("lib/abogus_rebuild/bb_to_fin_ops.json", "w"), indent=1)
