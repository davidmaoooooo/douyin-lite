# -*- coding: utf-8 -*-
"""单bit时间扫描: T = base + 2^k for k=0..40, 抓bb, 记录每个bit翻转影响哪些bb字节及xor。
据此完全解出 time -> bb 的位映射。"""
import json, time
from cdp2 import CDP, get_ws

def ev(cdp, expr, timeout=30):
    r = cdp.cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True}, timeout=timeout)
    return r.get("result", {}).get("result", {}).get("value")

SETUP="""(function(){if(window.__bb6)return;window.__bbcaps=[];var o=String.fromCharCode;
 String.fromCharCode=function(){try{if(arguments.length>=128&&arguments.length<=140)window.__bbcaps.push(Array.prototype.slice.call(arguments));}catch(e){}return o.apply(String,arguments);};window.__bb6=1;})()"""

def grab(cdp,T):
    ev(cdp,"window.__bbcaps=[];")
    ev(cdp,"""(function(){Date.now=()=>%d;Math.random=()=>0.5;if(performance)performance.now=()=>12345;
      var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);
      x.onreadystatechange=function(){if((x.responseURL||'').indexOf('a_bogus=')!==-1){try{x.abort();}catch(e){}}};x.send(null);})()"""%T)
    time.sleep(1.0)
    caps=json.loads(ev(cdp,"JSON.stringify(window.__bbcaps)") or "[]")
    for c in caps:
        if 130<=len(c)<=140: return c
    return None

if __name__=="__main__":
    cdp=CDP(get_ws()); cdp.cmd("Runtime.enable")
    ev(cdp,SETUP)
    base=1700000000000
    bbase=grab(cdp,base)
    print("base len",len(bbase))
    res={"base_T":base,"base_bb":bbase,"bits":{}}
    for k in range(0,41):
        T=base+(1<<k)
        bb=grab(cdp,T)
        if not bb or len(bb)!=len(bbase):
            res["bits"][k]={"err":True,"len":len(bb) if bb else 0}; print("bit",k,"ERR"); continue
        diff={i:[bbase[i],bb[i],bbase[i]^bb[i]] for i in range(len(bb)) if bbase[i]!=bb[i]}
        res["bits"][k]=diff
        print("bit %2d (+%d): %s" % (k,1<<k, {i:diff[i][2] for i in diff}))
    json.dump(res,open("time_bits.json","w"))
    print("saved time_bits.json")
    cdp.close()
