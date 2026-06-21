# -*- coding: utf-8 -*-
"""
JSVMP 反汇编器

策略：
1. 识别常见 opcode 的语义（通过模式匹配 + 参数分析）
2. 建立指令映射表
3. 反汇编关键代码段
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).parent.parent.parent
vm = json.load(open(ROOT / "lib" / "reverse" / "vm_bbtrace.json"))
trace = vm['trace']
bb = vm['bb']

print("=== JSVMP 反汇编器 ===\n")
print(f"指令数: {len(trace):,}")
print(f"输出 bb: {len(bb)} 字节\n")

# 通过模式推断 opcode 语义
OPCODE_MAP = {
    # 数据操作
    74: "LOAD/MOV",      # 最频繁，可能是数据移动
    38: "STORE?",
    54: "PUSH?",

    # 算术运算
    0: "ADD?",
    26: "SUB?",
    30: "MUL?",

    # 位运算
    8: "SHIFT",          # 移位
    14: "AND",           # 按位与
    18: "OR",            # 按位或
    11: "XOR",           # 按位异或

    # 控制流
    32: "JMP?",
    41: "CALL?",
    60: "RET?",

    # 数组/对象操作
    50: "ARRAY_GET?",
    53: "ARRAY_SET?",
    68: "PROP_GET?",
}

# 分析每个 opcode 的参数模式
print("分析 opcode 参数模式:\n")

for op in [74, 8, 14, 11, 38]:  # 重点分析高频 opcode
    samples = [ins for ins in trace if ins[0] == op][:100]

    print(f"Opcode {op:3d} ({OPCODE_MAP.get(op, '?')}): {len(samples)} 样本")

    # 参数类型统计
    arg_types = defaultdict(Counter)
    for ins in samples:
        for i in range(1, 5):
            if len(ins) > i and ins[i] is not None:
                arg_types[f'arg{i}'][type(ins[i]).__name__] += 1

    for arg_name in sorted(arg_types.keys()):
        print(f"  {arg_name}: {dict(arg_types[arg_name])}")

    # 显示前 3 个样本
    for i, ins in enumerate(samples[:3]):
        print(f"    [{i}] {ins}")
    print()

# 寻找特征指令序列（生成 bb 的循环）
print("=== 寻找生成 bb 的循环 ===\n")

# 假设：生成 133 字节需要有 133 次相似操作
# 寻找重复的指令模式
pattern_len = 5  # 寻找 5 条指令的重复模式
patterns = defaultdict(list)

for i in range(len(trace) - pattern_len):
    pattern = tuple(ins[0] for ins in trace[i:i+pattern_len])
    patterns[pattern].append(i)

# 找出重复次数接近 133 的模式
print("重复次数 > 50 的指令模式:")
for pattern, positions in sorted(patterns.items(), key=lambda x: -len(x))[:10]:
    if len(positions) > 50:
        print(f"  模式 {pattern}: 重复 {len(positions)} 次")
        print(f"    起始位置: {positions[:5]}...")

print("\n结论:")
print("  需要人工识别关键 opcode 的确切语义")
print("  建议：在 bdms.js 中插桩，记录每条 VM 指令执行时的")
print("        寄存器状态、栈状态、内存状态")
