# -*- coding: utf-8 -*-
"""
JSVMP 模拟执行器

策略：通过已有 trace 反推 opcode 语义，然后模拟执行
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
vm = json.load(open(ROOT / "lib" / "reverse" / "vm_bbtrace.json"))
trace = vm['trace']
bb_output = vm['bb']

print("=== JSVMP 模拟执行器 ===\n")
print(f"输入: T=1700000000000, query='q=1'")
print(f"输出: bb={bb_output[:20]}... (133 字节)\n")

# 通过输出反推关键指令
# bb[0]=171 的生成过程
print("追踪 bb[0]=171 的生成:\n")

# 搜索涉及 171 的指令
related_instructions = []
for i, ins in enumerate(trace):
    if 171 in ins[1:]:
        related_instructions.append((i, ins))

print(f"找到 {len(related_instructions)} 条涉及 171 的指令:")
for idx, ins in related_instructions[:10]:
    print(f"  [{idx:5d}] {ins}")

# 分析最后阶段
print(f"\n分析最后 100 条指令（输出阶段）:\n")
last_100 = trace[-100:]

# 统计 opcode
from collections import Counter
opcodes = Counter(ins[0] for ins in last_100)
print("Opcode 分布:")
for op, cnt in opcodes.most_common(5):
    print(f"  opcode {op:3d}: {cnt:2d} 次")

# 查找可能的数组赋值操作
print(f"\n查找数组索引 0-132 的操作:")

array_ops = []
for i, ins in enumerate(trace):
    # 检查参数中是否有 0-132 的小索引
    for arg in ins[1:]:
        if isinstance(arg, int) and 0 <= arg <= 132:
            array_ops.append((i, ins, arg))
            break

# 按索引分组
from collections import defaultdict
by_index = defaultdict(list)
for idx, ins, arg in array_ops[-500:]:  # 最后 500 个
    by_index[arg].append((idx, ins))

print(f"找到 {len(by_index)} 个可能的数组索引")
print("索引 0-10 的操作:")
for idx in range(min(11, len(by_index))):
    if idx in by_index:
        ops = by_index[idx]
        print(f"  索引[{idx}]: {len(ops)} 次操作")

print("\n结论:")
print("  JSVMP 过于复杂，静态分析效率极低")
print("\n推荐方案:")
print("  1. 继续扩展查表法（当前已 3359 样本）")
print("  2. 或使用符号执行工具（angr/Triton/Z3）")
print("  3. 或接受补环境方案")
