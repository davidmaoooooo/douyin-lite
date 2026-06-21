# -*- coding: utf-8 -*-
"""
简化策略：放弃完全逆向 JSVMP，改用混合方案

观察：
1. 新版本 bb 有 140 字节，98 个随时间变化
2. JSVMP trace 有 26280 条指令，完全逆向需要数周
3. 补环境方案已经稳定工作

新方案：**部分逆向 + 查表法**
- 只逆向 bb 的**固定部分**（42 个不变字节）
- 时间相关的 98 个字节用**预计算查表**
- 组合生成完整 bb

第一步：识别哪 42 个字节是固定的
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
samples = json.load(open(ROOT / "lib" / "reverse" / "samples_140byte.json"))

print("=== 识别固定字节 ===\n")
print(f"样本数: {len(samples)}\n")

# 找出所有样本都相同的字节位置
fixed_bytes = {}
for pos in range(140):
    values = [s['bb'][pos] for s in samples]
    if len(set(values)) == 1:  # 全部相同
        fixed_bytes[pos] = values[0]

print(f"固定字节: {len(fixed_bytes)} 个")
print(f"位置: {sorted(fixed_bytes.keys())}")
print(f"\n固定字节值:")
for pos in sorted(fixed_bytes.keys())[:20]:
    print(f"  bb[{pos:3d}] = {fixed_bytes[pos]:3d}")

# 时间相关字节
time_bytes = [i for i in range(140) if i not in fixed_bytes]
print(f"\n时间相关字节: {len(time_bytes)} 个")

print(f"\n=== 新方案总结 ===")
print(f"1. 固定部分: {len(fixed_bytes)} 字节（硬编码）")
print(f"2. 时间部分: {len(time_bytes)} 字节（查表）")
print(f"3. 查表规模: 2020-2030年每秒 = 约 315,360,000 条")
print(f"4. 存储优化: 压缩 + 插值 → 约 50-100MB")
print(f"\n实现难度: ★★☆☆☆（中等）")
print(f"维护成本: ★☆☆☆☆（低，算法升级需重新采样）")
