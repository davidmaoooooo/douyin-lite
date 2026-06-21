# -*- coding: utf-8 -*-
"""反向分析：从最终 bb 的每个字节，找它是在哪条指令生成的

策略：
假设 bb[i] 是在某条指令执行后写入的，找到这些写入指令
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
vm = json.load(open(ROOT / "lib" / "reverse" / "vm_bbtrace.json"))
trace = vm['trace']
bb = vm['bb']

print(f"=== 反向分析 bb 生成过程 ===\n")
print(f"bb 长度: {len(bb)}")
print(f"bb 前 20 字节: {bb[:20]}")
print(f"bb 后 20 字节: {bb[-20:]}\n")

# 查找可能的数组写入操作
# 通常 VM 的数组写入 opcode 会有索引参数
print("查找可能的数组写入指令（参数包含 0-132 的小数字）:\n")

# 统计 arg1/arg2 在 0-132 范围内的指令
array_write_candidates = []
for i, ins in enumerate(trace):
    opcode = ins[0]
    # 检查参数是否像数组索引（0-132）
    for arg_idx in [1, 2, 3]:
        if len(ins) > arg_idx and isinstance(ins[arg_idx], int):
            arg_val = ins[arg_idx]
            if 0 <= arg_val < 133:
                array_write_candidates.append((i, opcode, arg_idx, arg_val, ins))

print(f"找到 {len(array_write_candidates)} 条可能的数组操作指令\n")

# 按 opcode 分组
from collections import defaultdict
by_opcode = defaultdict(list)
for idx, opcode, arg_idx, arg_val, ins in array_write_candidates:
    by_opcode[opcode].append((idx, arg_idx, arg_val))

print("按 opcode 分组（可能的数组写入）:")
for opcode in sorted(by_opcode.keys()):
    items = by_opcode[opcode]
    print(f"  opcode {opcode:3d}: {len(items):4,} 次")
    # 显示前 5 个
    for trace_idx, arg_idx, val in items[:5]:
        print(f"    trace[{trace_idx:5d}] arg{arg_idx}={val}")

# 重点：查看 opcode 32（通常是 STORE/SET 操作）
if 32 in by_opcode:
    print(f"\n=== Opcode 32 详细分析（可能是数组赋值）===")
    op32_items = by_opcode[32]
    print(f"总共 {len(op32_items)} 次")

    # 检查是否覆盖 0-132
    indices = sorted(set(item[2] for item in op32_items))
    print(f"涉及的索引: {indices[:20]}... (共 {len(indices)} 个)")

    if len(indices) == 133:
        print("✓ 完美匹配！opcode 32 写入了全部 133 个字节")
