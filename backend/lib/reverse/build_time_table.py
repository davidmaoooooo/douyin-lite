# -*- coding: utf-8 -*-
"""
采集密集时间样本，建立 time → bb_time_bytes 映射表

策略：
1. 固定 query="aweme_id=1"（最短 query，避免长度变化干扰）
2. 采样连续时间戳（每秒 1 个样本，覆盖关键年份）
3. 提取 time 相关的 19 个字节
4. 保存为映射表供查询

采样范围：2020-2030 年（10 年 = 315,360,000 秒）
优化：每 10 秒采样 1 个（31,536,000 个样本，~50MB JSON）
"""
import json
import time
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from lib.reverse.cdp2 import CDP, get_ws

# 时间相关字节位置（从差分分析得出）
TIME_POSITIONS = [12, 14, 15, 29, 31, 32, 35, 37, 39, 42, 44, 47, 56, 59, 66, 68, 71, 129, 132]


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
    if(arguments.length>=128&&arguments.length<=145)
      window.__bbcaps.push(Array.prototype.slice.call(arguments));
  }catch(e){}
  return o.apply(String,arguments);
};
window.__bb_hook=1;
})()"""


def grab_bb(cdp, T):
    """抓取指定时间的 bb（固定 query）"""
    ev(cdp, "window.__bbcaps=[];")
    js = f"""(function(){{
Date.now=()=>{T};
Math.random=()=>0.5;
if(performance)performance.now=()=>12345;
var x=new XMLHttpRequest();
x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=1',true);
x.onreadystatechange=function(){{
  if((x.responseURL||'').indexOf('a_bogus=')!==-1){{
    try{{x.abort();}}catch(e){{}}
  }}
}};
x.send(null);
}})()"""
    ev(cdp, js)
    time.sleep(0.4)
    caps = json.loads(ev(cdp, "JSON.stringify(window.__bbcaps)") or "[]")
    for c in caps:
        if 130 <= len(c) <= 145:
            return c
    return None


def sample_time_range(cdp, start_year, end_year, step_seconds=10):
    """采样指定年份范围"""
    import datetime

    start_ts = int(datetime.datetime(start_year, 1, 1).timestamp() * 1000)
    end_ts = int(datetime.datetime(end_year, 1, 1).timestamp() * 1000)
    step_ms = step_seconds * 1000

    total = (end_ts - start_ts) // step_ms
    print(f"采样范围: {start_year}-{end_year}")
    print(f"步长: {step_seconds} 秒")
    print(f"预计样本数: {total:,}")

    mapping = {}
    count = 0
    failed = 0

    T = start_ts
    while T < end_ts:
        bb = grab_bb(cdp, T)
        if bb and len(bb) == 133:  # 只取固定长度的
            time_bytes = tuple(bb[i] for i in TIME_POSITIONS)
            mapping[str(T)] = list(time_bytes)
            count += 1

            if count % 100 == 0:
                progress = (T - start_ts) / (end_ts - start_ts) * 100
                print(f"  [{progress:5.2f}%] 已采集 {count:,} 个，失败 {failed}")
        else:
            failed += 1
            if failed % 10 == 0:
                print(f"  警告: 连续失败 {failed} 次")

        T += step_ms
        time.sleep(0.05)  # 防止过快

    return mapping


def main():
    print("=== 时间映射表采样器 ===\n")

    cdp = CDP(get_ws())
    cdp.cmd("Runtime.enable")
    ev(cdp, SETUP)
    print("已连接 CDP\n")

    # 先采样小范围测试（2024 年 1 个月，每 60 秒 1 个样本）
    print("开始测试采样（2024 年 1 月，每 60 秒）...\n")
    mapping = sample_time_range(cdp, 2024, 2024, step_seconds=60)

    cdp.close()

    # 保存
    out_file = ROOT / "lib" / "reverse" / "time_mapping_table.json"
    json.dump(mapping, open(out_file, "w"))

    print(f"\n=== 完成 ===")
    print(f"采集: {len(mapping):,} 条映射")
    print(f"保存: {out_file.relative_to(ROOT)}")
    print(f"\n下一步:")
    print("  1. 验证映射表准确性")
    print("  2. 扩展采样到 2020-2030（需要几小时）")
    print("  3. 实现查表法的 Python generate_a_bogus()")


if __name__ == "__main__":
    main()
