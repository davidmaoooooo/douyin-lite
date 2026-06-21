# -*- coding: utf-8 -*-
"""
数学建模方案：用现有 10 个样本拟合 time → bb 的映射函数

策略：
1. 分析时间相关的 115 个字节的变化规律
2. 尝试线性拟合
3. 建立预测模型
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
samples = json.load(open(ROOT / "lib" / "reverse" / "samples_140byte.json"))

print("=== 数学建模：time → bb 映射 ===\n")
print(f"样本数: {len(samples)}\n")

# 固定字节位置
FIXED = {11, 19, 39, 43, 47, 51, 55, 59, 63, 71, 75, 79, 83, 87, 91, 95, 99, 103, 107, 111, 115, 119, 123, 127, 131}

# 提取时间和对应的字节值
times = [s['T'] for s in samples]
bbs = [s['bb'] for s in samples]

print("时间范围:")
print(f"  最小: {min(times)}")
print(f"  最大: {max(times)}")
print(f"  跨度: {(max(times) - min(times)) / 1000:.1f} 秒\n")

# 简单线性拟合函数
def linear_fit(xs, ys):
    """最小二乘法拟合 y = ax + b"""
    n = len(xs)
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xx = sum(x*x for x in xs)
    sum_xy = sum(x*y for x, y in zip(xs, ys))

    denom = n * sum_xx - sum_x * sum_x
    if abs(denom) < 1e-10:
        return None, None

    a = (n * sum_xy - sum_x * sum_y) / denom
    b = (sum_y - a * sum_x) / n
    return a, b

# 分析前 10 个位置
print("分析每个字节位置的变化规律:\n")

for pos in range(10):
    if pos in FIXED:
        print(f"位置 [{pos:3d}]: 固定字节")
        continue

    values = [bb[pos] for bb in bbs]

    print(f"位置 [{pos:3d}]:")
    print(f"  值: {values}")
    print(f"  范围: {min(values):3d} ~ {max(values):3d}")

    # 线性拟合
    a, b = linear_fit(times, values)
    if a is not None:
        predicted = [a * t + b for t in times]
        errors = [abs(p - v) for p, v in zip(predicted, values)]
        mae = sum(errors) / len(errors)

        print(f"  线性: y = {a:.2e} * t + {b:.2f}, MAE={mae:.2f}")

        if mae < 5:
            print(f"  ✓ 可用线性拟合")
    print()
