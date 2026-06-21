# -*- coding: utf-8 -*-
"""
采集多个不同时间戳的 VM trace

策略：修改 bdms.js，在 VM 执行时记录完整 trace
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

print("=== 采集多个 VM trace ===\n")

# 准备不同的输入
test_cases = [
    {"T": 1700000000000, "query": "aweme_id=1"},
    {"T": 1700000001000, "query": "aweme_id=1"},  # +1秒
    {"T": 1700000100000, "query": "aweme_id=1"},  # +100秒
]

print("需要采集的 trace:")
for i, case in enumerate(test_cases):
    print(f"  [{i+1}] T={case['T']}, query={case['query']}")

print("\n实现步骤:")
print("1. 在 lib/runtime/bdms/ 中找到 VM 执行函数")
print("2. 插入日志记录每条指令")
print("3. 运行并保存多个 trace")
print("4. 差分分析找时间传播路径")

print("\n查找 VM 主循环...")

# 检查 bdms.js 中的关键字
bdms_file = ROOT / "lib" / "runtime" / "bdms" / "bdms.js"
if bdms_file.exists():
    content = open(bdms_file, encoding='utf-8').read()

    # 寻找 VM 执行相关的关键字
    keywords = ['function', 'switch', 'case', 'opcode', 'instruction', 'execute']
    print(f"\nbdms.js 大小: {len(content):,} 字节")

    for kw in keywords:
        count = content.count(kw)
        if count > 0:
            print(f"  '{kw}': {count} 次")

    # 查找函数定义数量
    func_count = content.count('function ')
    print(f"\n函数定义: {func_count} 个")

    print("\n建议：")
    print("  bdms.js 是混淆代码，难以直接修改")
    print("  改用 hook 方式：在 Node 运行时拦截关键调用")
else:
    print("bdms.js 未找到")
