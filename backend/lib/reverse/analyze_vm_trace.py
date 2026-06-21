# -*- coding: utf-8 -*-
"""分析 JSVMP trace，找出生成 bb 的关键逻辑

策略：
1. 找到操作输出数组的指令（push/append）
2. 追踪时间戳的传播路径
3. 识别位运算/编码逻辑
"""
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent.parent
vm = json.load(open(ROOT / "lib" / "reverse" / "vm_bbtrace.json"))
trace = vm['trace']
bb = vm['bb']

print(f"=== JSVMP Trace 分析 ===")
print(f"总指令: {len(trace):,}")
print(f"输出 bb 长度: {len(bb)}\n")

# 统计所有 opcode
opcode_freq = defaultdict(int)
for ins in trace:
    opcode_freq[ins[0]] += 1

print("Opcode 频率（前 20）:")
for op, cnt in sorted(opcode_freq.items(), key=lambda x: -x[1])[:20]:
    pct = cnt / len(trace) * 100
    print(f"  opcode {op:3d}: {cnt:6,} ({pct:5.2f}%)")

# 分析指令序列模式
print(f"\n=== 寻找输出模式 ===")
print(f"bb 有 {len(bb)} 个字节，需要找 133 次输出操作\n")

# 假设：连续出现的某个 opcode 可能是输出循环
print("连续重复的 opcode 序列:")
prev_op = None
repeat_count = 1
max_repeats = []

for i, ins in enumerate(trace):
    op = ins[0]
    if op == prev_op:
        repeat_count += 1
    else:
        if repeat_count > 50:  # 连续超过 50 次
            max_repeats.append((prev_op, repeat_count, i - repeat_count))
        repeat_count = 1
        prev_op = op

for op, cnt, start_idx in sorted(max_repeats, key=lambda x: -x[1])[:5]:
    print(f"  opcode {op:3d}: 连续 {cnt} 次，起始位置 {start_idx}")

# 检查特定模式：位运算相关的 opcode
print(f"\n=== 位运算相关指令 ===")
bitwise_ops = {8: 'shift?', 14: 'and?', 18: 'or?', 11: 'xor?'}
for op, name in bitwise_ops.items():
    if op in opcode_freq:
        print(f"  opcode {op:3d} ({name}): {opcode_freq[op]:,} 次")

print("\n下一步：")
print("  1. 反汇编 opcode 含义（参考 JSVMP 虚拟机规范）")
print("  2. 追踪时间戳数据流")
print("  3. 识别核心编码循环")
