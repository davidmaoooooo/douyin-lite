# -*- coding: utf-8 -*-
"""
对比策略：生成两个不同输入的 trace，找差异

如果有多个 trace，可以：
1. 找出哪些指令参数随输入变化
2. 识别时间戳在 VM 中的传播路径
3. 定位输出操作
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

print("=== JSVMP 深度逆向 - 最终方案 ===\n")

print("当前问题：")
print("  1. 只有 1 个 trace（固定输入 T=1700000000000, query='q=1'）")
print("  2. 无法对比找出变化规律")
print("  3. 26280 条指令，人工分析需要数周\n")

print("解决方案：")
print("\n【方案 1】采集多个 trace（推荐）")
print("  - 生成不同时间戳的 trace（至少 3 个）")
print("  - 对比找出时间相关的指令和数据流")
print("  - 追踪时间戳如何转换为 bb 字节")
print("  工作量: 1-2 天")

print("\n【方案 2】插桩 bdms.js")
print("  - 在 VM 解释器中插入日志")
print("  - 记录每条指令的寄存器/栈/内存状态")
print("  - 通过状态变化理解指令语义")
print("  工作量: 2-3 天")

print("\n【方案 3】符号执行")
print("  - 将 VM 指令转换为符号表达式")
print("  - 用 Z3/SymPy 求解时间戳→bb 的映射")
print("  - 自动化程度高")
print("  工作量: 3-5 天（需要符号执行框架）")

print("\n【方案 4】机器学习拟合")
print("  - 采集大量 (time, query) → bb 样本")
print("  - 训练神经网络拟合映射")
print("  - 黑盒方案，不理解原理")
print("  工作量: 1 周（需要训练数据 + GPU）")

print("\n【方案 5】接受补环境")
print("  - 补环境方案已 100% 工作")
print("  - 维护成本低")
print("  - 算法升级自动跟随")
print("  工作量: 0（已完成）")

print("\n" + "="*60)
print("我的最终建议：")
print("="*60)
print("""
考虑到：
1. JSVMP 逆向难度极高（26280 条指令）
2. 算法频繁升级（133→140 字节，可能继续变化）
3. 补环境方案已经稳定工作
4. 投入产出比：数周工作 vs 已有可用方案

建议：
→ 保持补环境方案作为生产方案
→ JSVMP 逆向作为研究项目（长期）
→ 所有逆向资料保留在 lib/reverse/ 供参考

如果坚持纯算法逆向，建议从【方案 1】开始：
采集多个不同时间的 trace，通过差分找规律。
""")
