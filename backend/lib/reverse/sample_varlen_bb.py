# -*- coding: utf-8 -*-
"""
采集变长 bb 样本，覆盖 133/134/136 等不同长度

策略：
1. 固定 Date.now()（控制变量）
2. 变化 URL query（触发不同长度）
3. 抓取 bb 并记录 {T, query, bb, len}
"""
import json
import time
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from lib.reverse.cdp2 import CDP, get_ws


def ev(cdp, expr, timeout=30):
    r = cdp.cmd("Runtime.evaluate",
                {"expression": expr, "returnByValue": True},
                timeout=timeout)
    return r.get("result", {}).get("result", {}).get("value")


# Hook String.fromCharCode 抓 bb
SETUP = """(function(){
if(window.__bb_hook)return;
window.__bbcaps=[];
var o=String.fromCharCode;
String.fromCharCode=function(){
  try{
    if(arguments.length>=128&&arguments.length<=145)
      window.__bbcaps.push(Array.prototype.slice.call(arguments));
  }catch(e){}
  return o.apply(String,arguments);
};
window.__bb_hook=1;
})()"""


def grab_bb(cdp, T, query):
    """抓取给定 time + query 的 bb"""
    ev(cdp, "window.__bbcaps=[];")
    js = f"""(function(){{
Date.now=()=>{T};
Math.random=()=>0.5;
if(performance)performance.now=()=>12345;
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
    time.sleep(0.6)
    caps = json.loads(ev(cdp, "JSON.stringify(window.__bbcaps)") or "[]")
    for c in caps:
        if 130 <= len(c) <= 145:
            return c
    return None


def main():
    print("=== 变长 bb 采样器 ===\n")

    cdp = CDP(get_ws())
    cdp.cmd("Runtime.enable")
    ev(cdp, SETUP)
    print("已连接 CDP 并注入 hook\n")

    # 固定时间戳（避免 time 变化干扰）
    BASE_T = 1700000000000

    # 不同 query 组合（触发变长）
    queries = [
        "aweme_id=1",
        "aweme_id=12345",
        "aweme_id=7123456789012345678",
        "aweme_id=1&aid=6383",
        "aweme_id=1&device_platform=webapp",
        "aweme_id=1&aid=6383&channel=channel_pc_web",
        "aweme_id=1&aid=6383&channel=channel_pc_web&version_code=190500",
        # 超长 query
        "aweme_id=7123456789012345678&aid=6383&channel=channel_pc_web&version_code=190500&version_name=19.5.0&cookie_enabled=true&screen_width=2560",
        # 包含特殊字符
        "aweme_id=1&search_keyword=hello",
        "aweme_id=1&search_keyword=%E4%B8%AD%E6%96%87",
        # 不同参数数量
        "a=1",
        "a=1&b=2&c=3",
        "a=1&b=2&c=3&d=4&e=5&f=6&g=7&h=8&i=9&j=10",
    ]

    samples = []
    lens_count = {}

    for i, query in enumerate(queries):
        print(f"[{i+1}/{len(queries)}] query: {query[:60]}...")
        bb = grab_bb(cdp, BASE_T, query)
        if bb:
            length = len(bb)
            lens_count[length] = lens_count.get(length, 0) + 1
            samples.append({
                "T": BASE_T,
                "query": query,
                "bb": bb,
                "len": length
            })
            print(f"  ✓ len={length}")
        else:
            print(f"  ✗ 未抓到")
        time.sleep(0.3)

    cdp.close()

    # 保存
    out_path = ROOT / "lib" / "reverse" / "bb_varlen_samples.json"
    json.dump(samples, open(out_path, "w"), indent=2)

    print(f"\n=== 采样完成 ===")
    print(f"总计: {len(samples)} 条")
    print(f"长度分布: {lens_count}")
    print(f"已保存: {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
