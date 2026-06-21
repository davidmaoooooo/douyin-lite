# -*- coding: utf-8 -*-
"""直接 hook String.fromCharCode, 捕获 bb 数组(长度130-134)。
固定 Date.now/Math.random, 用受控 query 触发签名, 抓 bb 原文数组。
只读 hook(不改返回值), 安全。返回真实 bb 字节, 用于精确拟合字段。
"""
import json, time
from cdp2 import CDP, get_ws

def ev(cdp, expr, by_value=True):
    r = cdp.cmd("Runtime.evaluate", {"expression": expr, "returnByValue": by_value, "awaitPromise": True}, timeout=30)
    return r.get("result", {}).get("result", {}).get("value")

SETUP = """
(function(){
  if(window.__bbhook) return 'already';
  window.__bbcaps = [];
  var ofc = String.fromCharCode;
  String.fromCharCode = function(){
    try{
      if(arguments.length>=128 && arguments.length<=140){
        window.__bbcaps.push(Array.prototype.slice.call(arguments));
      }
    }catch(e){}
    return ofc.apply(String, arguments);
  };
  window.__bbhook = 1;
  return 'hooked';
})()
"""

def trigger(cdp, query, T=1700000000000, rnd=0.5):
    # 清空捕获, 固定时间/随机, 发起请求
    cdp.cmd("Runtime.evaluate", {"expression": "window.__bbcaps=[];"}, timeout=5)
    expr = """
    (async function(){
      Date.now=()=>%d; Math.random=()=>%f; if(performance) performance.now=()=>12345;
      return await new Promise(function(res){
        var x=new XMLHttpRequest();
        x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?%s',true);
        var done=false;
        x.onreadystatechange=function(){
          if(!done && (x.responseURL||'').indexOf('a_bogus=')!==-1){done=true;res('OK');try{x.abort();}catch(e){}}
          else if(x.readyState===4 && !done){done=true;res('DONE');}
        };
        x.send(null);
        setTimeout(function(){if(!done){done=true;res('TO');}},8000);
      });
    })()
    """ % (T, rnd, query)
    ev(cdp, expr)
    time.sleep(0.3)
    caps = ev(cdp, "JSON.stringify(window.__bbcaps)")
    return json.loads(caps) if caps else []

if __name__ == "__main__":
    cdp = CDP(get_ws())
    cdp.cmd("Runtime.enable")
    print("setup hook:", ev(cdp, SETUP))

    out = {}
    # 基准 + 一组受控 query 变化
    cases = {
        "q1":      "q=1",
        "q2":      "q=2",
        "q1_dup":  "q=1",      # 复现确定性
        "qABC":    "aaa=bbb",
        "qlong":   "device_platform=webapp&aid=6383&q=1",
    }
    for name, q in cases.items():
        caps = trigger(cdp, q)
        # 取最长的(bb通常132, UA段125) -> 取132附近
        bb = None
        for c in caps:
            if 130 <= len(c) <= 134:
                bb = c; break
        if bb is None and caps:
            bb = max(caps, key=len)
        out[name] = {"q": q, "ncaps": len(caps), "lens": [len(c) for c in caps], "bb": bb}
        print(name, "caps=", len(caps), "lens=", [len(c) for c in caps], "bb_len=", len(bb) if bb else None)

    json.dump(out, open("grab_bb.json", "w"))
    print("saved grab_bb.json")
    cdp.close()
