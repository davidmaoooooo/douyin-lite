# -*- coding: utf-8 -*-
"""精确时间差分: 用133hook, 固定query=q=1, 扫描多个精确 T 值, 抓 bb。
解出时间字节的编码函数。"""
import json, time
from cdp2 import CDP, get_ws

def ev(cdp, expr, timeout=30):
    r = cdp.cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True}, timeout=timeout)
    return r.get("result", {}).get("result", {}).get("value")

SETUP="""(function(){if(window.__bb5)return;window.__bbcaps=[];var o=String.fromCharCode;
 String.fromCharCode=function(){try{if(arguments.length>=128&&arguments.length<=140)window.__bbcaps.push(Array.prototype.slice.call(arguments));}catch(e){}return o.apply(String,arguments);};window.__bb5=1;})()"""

def grab(cdp, T):
    ev(cdp,"window.__bbcaps=[];")
    ev(cdp,"""(function(){Date.now=()=>%d;Math.random=()=>0.5;if(performance)performance.now=()=>12345;
      var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);
      x.onreadystatechange=function(){if((x.responseURL||'').indexOf('a_bogus=')!==-1){try{x.abort();}catch(e){}}};x.send(null);})()"""%T)
    time.sleep(1.2)
    caps=json.loads(ev(cdp,"JSON.stringify(window.__bbcaps)") or "[]")
    for c in caps:
        if 130<=len(c)<=140: return c
    return None

if __name__=="__main__":
    cdp=CDP(get_ws()); cdp.cmd("Runtime.enable")
    print("setup:",ev(cdp,SETUP))
    base=1700000000000
    Ts={
      "base":base, "p1":base+1, "p2":base+2, "p16":base+16,
      "p256":base+256, "p4096":base+4096, "p65536":base+65536,
      "p1M":base+1048576, "p16M":base+16777216, "p256M":base+268435456,
    }
    out={}
    for name,T in Ts.items():
        bb=grab(cdp,T)
        out[name]={"T":T,"bb":bb}
        print(name, "ok" if bb else "FAIL", "len", len(bb) if bb else 0)
    json.dump(out, open("time_precise.json","w"))
    print("saved time_precise.json")
    cdp.close()
