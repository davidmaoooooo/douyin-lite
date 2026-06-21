# -*- coding: utf-8 -*-
"""大批量真实区间时间戳采样(保持133长), 求解 time->bb 仿射系统。
只用当前时间附近的真实戳(13位, 高位稳定), 覆盖低32位随机变化。"""
import json, time, random
from cdp2 import CDP, get_ws

def ev(cdp, expr, timeout=30):
    r = cdp.cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True}, timeout=timeout)
    return r.get("result", {}).get("result", {}).get("value")

SETUP="""(function(){if(window.__bb8)return;window.__bbcaps=[];var o=String.fromCharCode;
 String.fromCharCode=function(){try{if(arguments.length>=128&&arguments.length<=140)window.__bbcaps.push(Array.prototype.slice.call(arguments));}catch(e){}return o.apply(String,arguments);};window.__bb8=1;})()"""

def grab(cdp,T):
    ev(cdp,"window.__bbcaps=[];")
    ev(cdp,"""(function(){Date.now=()=>%d;Math.random=()=>0.5;if(performance)performance.now=()=>12345;
      var x=new XMLHttpRequest();x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1',true);
      x.onreadystatechange=function(){if((x.responseURL||'').indexOf('a_bogus=')!==-1){try{x.abort();}catch(e){}}};x.send(null);})()"""%T)
    time.sleep(0.55)
    caps=json.loads(ev(cdp,"JSON.stringify(window.__bbcaps)") or "[]")
    for c in caps:
        if 130<=len(c)<=140: return c
    return None

if __name__=="__main__":
    cdp=CDP(get_ws()); cdp.cmd("Runtime.enable"); ev(cdp,SETUP)
    # 固定一个确定性 PRNG(无 random 依赖问题) — 用线性序列覆盖低位
    base=1700000000000
    rng=random.Random(42)
    out=[]
    N=160
    for n in range(N):
        # 低32位随机 + 偶尔扰动高位
        T=base + rng.randint(0, 2**32-1)
        if n%7==0: T=base + rng.randint(0,2**40)
        bb=grab(cdp,T)
        if bb and len(bb)==133:
            out.append({"T":T,"bb":bb})
        if n%20==0: print(n,"collected",len(out))
    json.dump(out,open("time_big.json","w"))
    print("saved",len(out),"x133-len samples")
    cdp.close()
