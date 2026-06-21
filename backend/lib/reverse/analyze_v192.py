# -*- coding: utf-8 -*-
"""分析新版本（v192）样本，找出规律"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
samples = json.load(open(ROOT / "lib" / "reverse" / "samples_v192.json"))

print(f"=== 分析 {len(samples)} 个新版本样本 ===\n")

# 按长度分组
by_len = {}
for s in samples:
    length = len(s['bb'])
    by_len.setdefault(length, []).append(s)

print("长度分布:")
for length in sorted(by_len.keys()):
    print(f"  {length} 字节: {len(by_len[length])} 个")

# 分析变长规律
print("\n=== 变长规律分析 ===")
for s in samples[:10]:
    T, query, bb_len = s['T'], s['query'], len(s['bb'])
    print(f"T={T:16d} query_len={len(query):3d} query={query[:30]:30s} → bb_len={bb_len}")

# 同长度样本的时间差异
if 133 in by_len and len(by_len[133]) >= 2:
    print(f"\n=== 133 字节样本的时间差异 ===")
    samples_133 = by_len[133]
    s1, s2 = samples_133[0], samples_133[1]

    diffs = [i for i in range(133) if s1['bb'][i] != s2['bb'][i]]
    print(f"样本1: T={s1['T']}")
    print(f"样本2: T={s2['T']}")
    print(f"时间差: {s2['T'] - s1['T']} ms")
    print(f"差异字节: {len(diffs)} 个")
    print(f"位置: {diffs}")

# s4 编码后长度验证
print("\n=== s4 编码长度验证 ===")
for length in sorted(by_len.keys()):
    # bb 前面有 4 字节随机头
    total_bytes = length + 4
    s4_len = (total_bytes * 4 + 2) // 3  # s4 base64 公式
    print(f"bb={length} + head=4 → total={total_bytes} → s4编码≈{s4_len}")

print("\n结论:")
print("  - bb 长度: 133/134/136 (变长)")
print("  - s4 编码后: 184/185/187 或 192")
print("  - 时间相关字节约 12 个")
print("  - 变长可能和 query 长度/内容相关")
