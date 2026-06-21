# -*- coding: utf-8 -*-
"""
分析 query 变化对 bb 的影响

策略：固定 time，只变 query，diff bb 找出 query 相关字节
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent


def hex_dump(bb, highlight=None):
    """16进制显示 bb，高亮指定字节"""
    lines = []
    for i in range(0, len(bb), 16):
        chunk = bb[i:i+16]
        hex_part = ' '.join(
            f'\033[93m{b:02x}\033[0m' if highlight and i+j in highlight else f'{b:02x}'
            for j, b in enumerate(chunk)
        )
        lines.append(f'{i:03d}  {hex_part}')
    return '\n'.join(lines)


def diff_bb(bb1, bb2):
    """返回两个 bb 差异的字节索引"""
    min_len = min(len(bb1), len(bb2))
    diffs = [i for i in range(min_len) if bb1[i] != bb2[i]]
    if len(bb1) != len(bb2):
        diffs.append('LENGTH_DIFF')
    return diffs


def analyze_query_impact():
    """分析 query 对 bb 的影响"""

    # 使用已有的样本（需要先运行采样脚本生成）
    sample_file = ROOT / "lib" / "reverse" / "bb_varlen_samples.json"
    if not sample_file.exists():
        print(f"样本文件不存在: {sample_file}")
        print("需要先运行采样脚本:")
        print("  1. 启动浏览器调试: edge --remote-debugging-port=9222")
        print("  2. 打开抖音任意页面")
        print("  3. python lib/reverse/sample_varlen_bb.py")
        return

    samples = json.load(open(sample_file))
    print(f"=== 加载了 {len(samples)} 条样本 ===\n")

    # 按长度分组
    by_len = {}
    for s in samples:
        length = s['len']
        by_len.setdefault(length, []).append(s)

    print("长度分布:")
    for length in sorted(by_len.keys()):
        print(f"  {length}: {len(by_len[length])} 条")

    # 同长度样本对比（找 query 相关字节）
    if 133 in by_len and len(by_len[133]) >= 2:
        print("\n=== 133 长度样本对比 ===")
        s1, s2 = by_len[133][0], by_len[133][1]
        print(f"样本1 query: {s1['query'][:60]}")
        print(f"样本2 query: {s2['query'][:60]}")
        diffs = diff_bb(s1['bb'], s2['bb'])
        print(f"\n差异字节位置 ({len(diffs)} 个): {diffs[:20]}")
        print("\n样本1 bb (差异高亮):")
        print(hex_dump(s1['bb'], set(diffs)))

    # 不同长度样本对比（找变长机制）
    lens = sorted(by_len.keys())
    if len(lens) >= 2:
        print(f"\n=== 长度变化分析 ({lens[0]} vs {lens[1]}) ===")
        s1 = by_len[lens[0]][0]
        s2 = by_len[lens[1]][0]
        print(f"{lens[0]}长 query: {s1['query'][:60]}")
        print(f"{lens[1]}长 query: {s2['query'][:60]}")
        print(f"长度差: {abs(lens[1] - lens[0])} 字节")

        # 找公共前缀和后缀
        prefix_len = 0
        for i in range(min(len(s1['bb']), len(s2['bb']))):
            if s1['bb'][i] == s2['bb'][i]:
                prefix_len += 1
            else:
                break

        suffix_len = 0
        for i in range(1, min(len(s1['bb']), len(s2['bb'])) + 1):
            if s1['bb'][-i] == s2['bb'][-i]:
                suffix_len += 1
            else:
                break

        print(f"\n公共前缀: {prefix_len} 字节")
        print(f"公共后缀: {suffix_len} 字节")
        print(f"变化区域: [{prefix_len}, {lens[0]-suffix_len})")

        print(f"\n{lens[0]}长 变化区域:")
        print(hex_dump(s1['bb'][prefix_len:lens[0]-suffix_len]))
        print(f"\n{lens[1]}长 变化区域:")
        print(hex_dump(s2['bb'][prefix_len:lens[1]-suffix_len]))


if __name__ == "__main__":
    analyze_query_impact()
