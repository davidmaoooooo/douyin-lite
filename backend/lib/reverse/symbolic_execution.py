# -*- coding: utf-8 -*-
"""
符号执行方案：用 Z3 求解 time → bb 的映射函数

已知：
- 10 个样本的 (time, bb) 对
- bb 有 25 个固定字节，115 个时间相关字节

目标：
- 用 Z3 建模找出 time → bb 的函数关系
"""

# 检查是否安装 z3
try:
    from z3 import *
    print("Z3 已安装")
except ImportError:
    print("Z3 未安装")
    print("\n安装方法:")
    print("  pip install z3-solver")
    print("\n继续使用纯数学方法...")

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
samples = json.load(open(ROOT / "lib" / "reverse" / "samples_140byte.json"))

print(f"\n=== 符号执行建模 ===\n")
print(f"样本数: {len(samples)}")

# 固定字节位置
FIXED = {11, 19, 39, 43, 47, 51, 55, 59, 63, 71, 75, 79, 83, 87, 91, 95, 99, 103, 107, 111, 115, 119, 123, 127, 131}

# 尝试用多项式拟合每个字节
print("尝试用多项式建模 time → bb[i]:\n")

def try_polynomial_fit(times, values, degree=2):
    """尝试多项式拟合"""
    # 简化：用最小二乘法拟合 y = a*t^2 + b*t + c
    n = len(times)

    # 归一化时间（避免数值溢出）
    t_min, t_max = min(times), max(times)
    t_norm = [(t - t_min) / (t_max - t_min) for t in times]

    # 构造矩阵 [t^2, t, 1]
    A = []
    for t in t_norm:
        A.append([t*t, t, 1])

    # 最小二乘法求解
    from numpy import array, linalg
    try:
        A = array(A)
        b = array(values)
        coef = linalg.lstsq(A, b, rcond=None)[0]

        # 验证误差
        pred = [coef[0]*t*t + coef[1]*t + coef[2] for t in t_norm]
        mae = sum(abs(p - v) for p, v in zip(pred, values)) / len(values)

        return coef, mae
    except:
        return None, float('inf')

times = [s['T'] for s in samples]
bbs = [s['bb'] for s in samples]

success_count = 0
models = {}

for pos in range(10):  # 前 10 个位置
    if pos in FIXED:
        continue

    values = [bb[pos] for bb in bbs]
    coef, mae = try_polynomial_fit(times, values)

    if coef is not None and mae < 10:
        success_count += 1
        models[pos] = (coef, mae)
        print(f"位置[{pos:3d}]: MAE={mae:.2f} ✓ 可用多项式")
    else:
        print(f"位置[{pos:3d}]: MAE={mae:.2f} ✗ 不可用")

print(f"\n可用多项式建模: {success_count}/10")

if success_count < 5:
    print("\n结论：多项式拟合效果差")
    print("原因：bb 字节是通过复杂位运算生成，不是简单数学函数")
    print("\n最终建议：")
    print("  1. 查表法已经可用（3359 样本）")
    print("  2. 继续扩展映射表到完整年份")
    print("  3. JSVMP 完全逆向需要专业工具（IDA Pro/Ghidra + 数周时间）")
