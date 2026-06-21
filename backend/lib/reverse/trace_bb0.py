# -*- coding: utf-8 -*-
"""
手工追踪：从 bb 的一个字节反推生成它的指令序列

选择 bb[0] = 171，追踪它是如何生成的
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
vm = json.load(open(ROOT / "lib" / "reverse" / "vm_bbtrace.json"))
trace = vm['trace']
bb = vm['bb']

print("=== 手工追踪 bb[0] 的生成 ===\n")
print(f"目标: bb[0] = {bb[0]}\n")

# 171 的二进制
print(f"171 = 0b{bin(171)[2:]:0>8s} = 0x{hex(171)[2:]:0>2s}")
print(f"分解: 128 + 32 + 8 + 2 + 1\n")

# 在 trace 中寻找值 171 或接近的计算
print("在 trace 中搜索值 171:\n")

matches = []
for i, ins in enumerate(trace):
    for j, arg in enumerate(ins[1:], 1):
        if arg == 171:
            matches.append((i, j, ins))
            if len(matches) <= 5:
                print(f"  trace[{i:5d}] arg{j}=171  {ins}")

if not matches:
    print("  未找到直接的 171")

print(f"\n搜索 128, 32, 8, 2, 1 (171的组成):")
for val in [128, 32, 8, 2, 1]:
    count = sum(1 for ins in trace for arg in ins[1:] if arg == val)
    print(f"  值 {val:3d}: {count} 次")

# 搜索位运算 XOR 11（因为 171 XOR keystream 可能产生特定模式）
print(f"\n搜索 XOR 操作（opcode 11）:")
xor_ops = [ins for ins in trace if ins[0] == 11]
print(f"  总共 {len(xor_ops)} 条 XOR 指令")
print(f"  前 10 条:")
for ins in xor_ops[:10]:
    print(f"    {ins}")

print("\n推测：")
print("  bb[0]=171 可能是:")
print("  1. 随机生成（前4字节是随机头）")
print("  2. 或由时间戳经过复杂变换得到")
print("  3. 需要查看 VM 执行的最终阶段")
print("\n建议：分析 trace 的最后 500 条指令（输出阶段）")
