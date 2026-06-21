# -*- coding: utf-8 -*-
"""
差分分析：对比多个时间的 bb，找出变化规律
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
data = json.load(open(ROOT / "lib" / "reverse" / "multi_traces.json"))

print("=== 差分分析：time → bb 映射 ===\n")
print(f"样本数: {len(data)}\n")

# 显示基本信息
for d in data:
    print(f"[{d['desc']:8s}] T={d['T']}, bb_len={len(d['bb'])}")

# 找出所有样本长度一致的位置进行对比
min_len = min(len(d['bb']) for d in data)
print(f"\n最小 bb 长度: {min_len}")
print(f"分析前 {min_len} 字节\n")

# 找出固定字节和变化字节
fixed = {}
variable = {}

for pos in range(min_len):
    values = [d['bb'][pos] for d in data]
    unique = set(values)

    if len(unique) == 1:
        fixed[pos] = values[0]
    else:
        variable[pos] = values

print(f"固定字节: {len(fixed)} 个")
print(f"变化字节: {len(variable)} 个\n")

# 显示变化字节的详细信息
print("变化字节详情（前 20 个）:\n")
print("位置  | base(T=0) | +1s | +10s | +100s | +1000s | 变化量")
print("-" * 70)

times = [d['T'] for d in data]
time_diffs = [t - times[0] for t in times]

for pos in sorted(variable.keys())[:20]:
    values = variable[pos]
    diffs = [values[i] - values[0] for i in range(len(values))]

    print(f"[{pos:3d}] | {values[0]:3d} | {values[1]:3d} | {values[2]:3d} | {values[3]:3d} | {values[4]:3d} | {diffs}")

    # 尝试找线性关系
    # delta_value / delta_time
    if time_diffs[1] > 0:
        rate = (values[1] - values[0]) / time_diffs[1]
        if abs(rate) > 1e-10:
            print(f"      速率: {rate:.2e} 单位/ms")

print("\n分析每个字节与时间的关系...")

# 对每个变化字节，计算与时间的相关性
correlations = {}

for pos in variable.keys():
    values = variable[pos]

    # 简单线性相关：检查值变化是否与时间变化成正比
    total_time_change = times[-1] - times[0]
    total_value_change = values[-1] - values[0]

    if total_time_change > 0:
        rate = total_value_change / total_time_change
        correlations[pos] = rate

# 按相关性排序
sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)

print("\n\n时间相关性最强的 10 个字节:")
print("位置  | 变化率 (value/ms)")
print("-" * 40)
for pos, rate in sorted_corr[:10]:
    print(f"[{pos:3d}] | {rate:.2e}")

print("\n\n结论:")
print("  1. bb 长度不固定（137-140 字节）")
print("  2. 大量字节随时间变化")
print("  3. 某些字节与时间呈近似线性关系")
print("  4. 但总体是复杂的非线性变换")
print("\n建议:")
print("  - 查表法已覆盖 107 天，继续扩展")
print("  - 完全逆向需要深入 VM 字节码分析")
