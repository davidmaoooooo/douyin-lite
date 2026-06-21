# -*- coding: utf-8 -*-
"""
JSVMP 深度分析 - 寻找 bb 生成的核心模式

策略：
1. 分析最后阶段的指令序列
2. 识别可能的数组写入模式
3. 尝试还原算法片段
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).parent.parent.parent
vm = json.load(open(ROOT / "lib" / "reverse" / "vm_bbtrace.json"))
trace = vm['trace']
bb_output = vm['bb']

print("=== JSVMP 深度模式分析 ===\n")

# 分析最后 1000 条指令的模式
last_n = 1000
last_trace = trace[-last_n:]

print(f"分析最后 {last_n} 条指令...\n")

# 1. 找出最频繁的 opcode 序列（3-gram）
print("1. 最频繁的 3 条指令序列:")
trigrams = []
for i in range(len(last_trace) - 2):
    seq = (last_trace[i][0], last_trace[i+1][0], last_trace[i+2][0])
    trigrams.append(seq)

trigram_freq = Counter(trigrams)
for seq, count in trigram_freq.most_common(10):
    print(f"  {seq} → 出现 {count} 次")

# 2. 分析参数范围（可能是数组索引）
print("\n2. 参数值分布（可能包含索引）:")
param_values = []
for ins in last_trace:
    for arg in ins[1:]:
        if isinstance(arg, int) and 0 <= arg <= 200:
            param_values.append(arg)

value_freq = Counter(param_values)
print("  0-132 范围内的值（可能是 bb 索引）:")
for val in range(0, 133, 10):
    count = sum(value_freq[v] for v in range(val, min(val+10, 133)))
    if count > 0:
        print(f"    [{val:3d}-{min(val+9, 132):3d}]: {count:3d} 次")

# 3. 寻找连续索引访问模式
print("\n3. 连续索引访问模式:")
consecutive_sequences = []
for i in range(len(last_trace) - 10):
    indices = []
    for j in range(10):
        ins = last_trace[i+j]
        for arg in ins[1:]:
            if isinstance(arg, int) and 0 <= arg <= 132:
                indices.append(arg)
                break

    # 检查是否连续
    if len(indices) == 10:
        diffs = [indices[k+1] - indices[k] for k in range(9)]
        if all(d == 1 for d in diffs):  # 完全连续
            consecutive_sequences.append((i, indices[0], indices[-1]))

if consecutive_sequences:
    print(f"  发现 {len(consecutive_sequences)} 个连续访问序列:")
    for idx, start, end in consecutive_sequences[:5]:
        print(f"    指令 {idx}: 索引 {start}→{end}")
else:
    print("  未发现明显的连续访问")

# 4. 尝试识别循环结构
print("\n4. 循环结构识别:")
# 检查重复的指令序列
window_size = 50
for offset in range(0, last_n - window_size * 2, 100):
    pattern = [ins[0] for ins in last_trace[offset:offset+window_size]]

    # 在后续查找相同模式
    for search_offset in range(offset + window_size, last_n - window_size):
        candidate = [ins[0] for ins in last_trace[search_offset:search_offset+window_size]]
        if pattern == candidate:
            print(f"  发现重复模式: 指令 {offset}→{offset+window_size} == {search_offset}→{search_offset+window_size}")
            print(f"    可能是循环，间隔 {search_offset - offset} 条指令")
            break
    else:
        continue
    break
else:
    print("  未发现明显的循环结构")

print("\n5. 关键发现总结:")
print("  - VM 最后阶段有大量重复操作")
print("  - 参数中包含 0-132 范围的值（疑似 bb 索引）")
print("  - 需要动态追踪才能确定具体写入位置")
print("\n下一步:")
print("  - 使用 Node.js inspector 动态追踪")
print("  - 或修改 bdms.js 插入日志")
print("  - 或使用符号执行工具（angr）")
