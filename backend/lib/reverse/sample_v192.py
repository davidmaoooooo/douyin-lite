# -*- coding: utf-8 -*-
"""
采集新版本（192长度）a_bogus 的 bb 样本

策略：
1. 固定 query，变化 time → 找时间相关字节
2. 固定 time，变化 query → 找 query 相关字节
3. 对比新旧版本差异（140 vs 133 字节）
"""
import json
import time
import sys
from pathlib import Path

# 设置正确的路径
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from lib.reverse.cdp2 import CDP, get_ws


def ev(cdp, expr, timeout=30):
    r = cdp.cmd("Runtime.evaluate",
                {"expression": expr, "returnByValue": True},
                timeout=timeout)
    return r.get("result", {}).get("result", {}).get("value")


SETUP = """(function(){
if(window.__bb_hook)return;
window.__bbcaps=[];
var o=String.fromCharCode;
String.fromCharCode=function(){
  try{
    if(arguments.length>=130)
      window.__bbcaps.push(Array.prototype.slice.call(arguments));
  }catch(e){}
  return o.apply(String,arguments);
};
window.__bb_hook=1;
})()"""


def grab_bb(cdp, T, query):
    """抓取指定 time + query 的 bb"""
    ev(cdp, "window.__bbcaps=[];")
    js = f"""(function(){{
Date.now=()=>{T};
Math.random=()=>0.5;
var x=new XMLHttpRequest();
x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?{query}',true);
x.onreadystatechange=function(){{
  if((x.responseURL||'').indexOf('a_bogus=')!==-1){{
    try{{x.abort();}}catch(e){{}}
  }}
}};
x.send(null);
}})()"""
    ev(cdp, js)
    time.sleep(1.0)  # 增加等待时间
    caps = json.loads(ev(cdp, "JSON.stringify(window.__bbcaps)") or "[]")
    for c in caps:
        if 130 <= len(c) <= 150:  # 新版本范围
            return c
    return None


def sample_new_version():
    """采集新版本样本"""
    print("=== 采集新版本（140字节 bb）样本 ===\n")

    cdp = CDP(get_ws())
    cdp.cmd("Runtime.enable")
    ev(cdp, SETUP)
    print("已连接 CDP\n")

    samples = []

    # 1. 固定 query，变化 time（找时间字节位置）
    print("[1/2] 采集时间变化样本（固定 query='aweme_id=1'）...")
    base_T = 1700000000000
    for i, delta in enumerate([0, 1, 10, 100, 1000, 10000, 100000, 1000000,
                               86400000, 86400000*30]):  # 0秒到30天
        T = base_T + delta
        bb = grab_bb(cdp, T, "aweme_id=1")
        if bb:
            samples.append({"T": T, "query": "aweme_id=1", "bb": bb, "type": "time_var"})
            print(f"  [{i+1}/10] T={T}, len={len(bb)}")
        time.sleep(0.3)

    # 2. 固定 time，变化 query（找 query 字节位置）
    print("\n[2/2] 采集 query 变化样本（固定 T=1700000000000）...")
    queries = [
        "aweme_id=1",
        "aweme_id=7123456789012345678",
        "aweme_id=1&aid=6383",
        "aweme_id=1&aid=6383&channel=channel_pc_web",
        "aweme_id=1&device_platform=webapp&aid=6383",
    ]
    for i, query in enumerate(queries):
        bb = grab_bb(cdp, base_T, query)
        if bb:
            samples.append({"T": base_T, "query": query, "bb": bb, "type": "query_var"})
            print(f"  [{i+1}/{len(queries)}] query={query[:40]}, len={len(bb)}")
        time.sleep(0.3)

    cdp.close()

    # 保存
    out_file = ROOT / "lib" / "reverse" / "samples_v192.json"
    json.dump(samples, open(out_file, "w"), indent=2)

    print(f"\n=== 完成 ===")
    print(f"采集: {len(samples)} 条样本")
    print(f"长度分布: {set(len(s['bb']) for s in samples)}")
    print(f"已保存: {out_file.relative_to(ROOT)}")


if __name__ == "__main__":
    sample_new_version()
