# -*- coding: utf-8 -*-
"""采集随机/多样 time 样本(覆盖所有32+bit变化), 用于求解每个 time 派生 bb 字节的
完整仿射函数 bb[i] = f(time_bits)。配合 query 固定=q=1。"""
import json, time
from cdp2 import CDP, get_ws

def ev(cdp, expr, timeout=30):
    r = cdp.cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True}, timeout=timeout)
    return r.get("result", {}).get("result", {}).get("value")

SETUP="""(function(){if(window.__bb7)return;window.__bbcaps=[];var o=String.fromCharCode;
 String.fromCharCode=function(){try{if(arguments.length>=128&&arguments.length<=140)window.__bbcaps.push(Array.prototype.slice.call(arguments));}catch(e){}return o.apply(String,arguments);};window.__bb7=1;})()"""

def grab(cdp,T):
    ev(cdp,"window.__bbcaps=[];")
    ev(cdp,"""(function(){Date.now=()=>%d;Math.random=()=>0.5;if(performance)performance.now=()=>12345;
      var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);
      x.onreadystatechange=function(){if((x.responseURL||'').indexOf('a_bogus=')!==-1){try{x.abort();}catch(e){}}};x.send(null);})()"""%T)
    time.sleep(0.9)
    caps=json.loads(ev(cdp,"JSON.stringify(window.__bbcaps)") or "[]")
    for c in caps:
        if 130<=len(c)<=140: return c
    return None

if __name__=="__main__":
    cdp=CDP(get_ws()); cdp.cmd("Runtime.enable"); ev(cdp,SETUP)
    base=1700000000000
    # 一批多样化时间: 覆盖各字节多种取值
    Ts=[base]
    # 各种规整值
    for v in [1,2,3,5,7,10,100,255,256,1000,65535,65536,1000000,16777215,
              1700000000001,1700000012345,1699999999999,1234567890123,
              1800000000000,1500000000000,1700050000000,1700000050000,1700000000050]:
        Ts.append(v if v>1e12 else base+v)
    Ts=sorted(set(Ts))
    out=[]
    for T in Ts:
        bb=grab(cdp,T)
        if bb and len(bb)==133:
            out.append({"T":T,"bb":bb})
        print("T=",T,"->",("ok" if bb and len(bb)==133 else ("len%d"%len(bb) if bb else "FAIL")))
    json.dump(out,open("time_samples.json","w"))
    print("saved",len(out),"samples")
    cdp.close()
