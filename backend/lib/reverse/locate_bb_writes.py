# -*- coding: utf-8 -*-
"""
关键突破：定位 bb 数组写入指令

策略：
1. 从 VM trace 找出最终写入 bb 的指令
2. 反向追踪这些指令的数据来源
3. 找到时间戳的传播路径
"""
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent.parent
vm = json.load(open(ROOT / "lib" / "reverse" / "vm_bbtrace.json"))
trace = vm['trace']
bb = vm['bb']

print("=== 定位 bb 数组写入指令 ===\n")
print(f"目标：找到生成 bb[0..132] 的 133 条写入指令\n")

# 策略：bb 的每个字节值在 trace 中出现的位置
print("分析 bb 每个字节在 trace 中的出现位置:\n")

# 重点分析前 10 个字节
for i in range(10):
    target_val = bb[i]
    print(f"\nbb[{i}] = {target_val}")

    # 在 trace 中搜索这个值
    occurrences = []
    for t_idx, ins in enumerate(trace):
        for arg_idx, arg in enumerate(ins[1:], 1):
            if arg == target_val:
                occurrences.append((t_idx, arg_idx, ins))

    print(f"  在 trace 中出现 {len(occurrences)} 次")

    # 只显示最后 5 次（最可能是输出阶段）
    if len(occurrences) > 5:
        print(f"  最后 5 次出现:")
        for t_idx, arg_idx, ins in occurrences[-5:]:
            print(f"    [{t_idx:5d}] opcode={ins[0]:3d}, arg{arg_idx}={target_val}")
    else:
        print(f"  所有出现:")
        for t_idx, arg_idx, ins in occurrences:
            print(f"    [{t_idx:5d}] opcode={ins[0]:3d}, arg{arg_idx}={target_val}")

print("\n\n分析最后 500 条指令中的数组操作模式:")

# 在最后阶段查找连续的写入操作
last_500 = trace[-500:]

# 统计每个 opcode 的参数范围
opcode_arg_ranges = defaultdict(lambda: {'min': float('inf'), 'max': float('-inf'), 'count': 0})

for ins in last_500:
    opcode = ins[0]
    for arg in ins[1:]:
        if isinstance(arg, int):
            opcode_arg_ranges[opcode]['min'] = min(opcode_arg_ranges[opcode]['min'], arg)
            opcode_arg_ranges[opcode]['max'] = max(opcode_arg_ranges[opcode]['max'], arg)
            opcode_arg_ranges[opcode]['count'] += 1

print("\n最后 500 条指令的 opcode 参数范围（可能包含数组索引）:")
for opcode in sorted(opcode_arg_ranges.keys())[:15]:
    info = opcode_arg_ranges[opcode]
    print(f"  opcode {opcode:3d}: 参数范围 [{info['min']:6d}, {info['max']:6d}], 出现 {info['count']} 次")

print("\n\n关键发现:")
print("  bb 的每个字节值在 trace 中多次出现")
print("  无法直接通过值匹配定位写入指令")
print("\n需要更深入的方法:")
print("  1. 动态插桩 bdms.js 的 VM 执行器")
print("  2. 记录每条指令对内存/栈的影响")
print("  3. 追踪时间戳数据流")
