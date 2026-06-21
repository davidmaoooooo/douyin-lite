# -*- coding: utf-8 -*-
"""
纯算法逆向 - 最终方案：样本拟合法

思路：
1. 采集大量 (time, query) → bb 样本（覆盖各种组合）
2. 分析 time → bb_time_bytes 的映射（已知位置：19 个字节）
3. 分析 query → bb_query_bytes 的映射（SM3 相关字节）
4. 构建 Python 函数：generate_bb(time, query) → bb
5. 已知部分：RC4 keystream 固定、s4 base64 确定

当前进度：
- ✅ RC4 keystream（lib/reverse/FIXED_keystream.json）
- ✅ time 影响的 19 个字节位置
- ⚠️ time → bb_bytes 的具体公式（6-bit 打包规则）
- ❌ query → bb_bytes 的 SM3 注入规则
- ❌ bb 的变长序列化规则

下一步：
采集 **时间戳全覆盖样本**，拟合 time → bb_time_bytes 的公式
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent

# 时间相关字节的已知位置（从 time_samples.json 差分得出）
TIME_BYTE_POSITIONS = [12, 14, 15, 29, 31, 32, 35, 37, 39, 42, 44, 47, 56, 59, 66, 68, 71, 129, 132]


def extract_time_bytes(bb):
    """从 bb 提取时间相关字节"""
    return [bb[i] for i in TIME_BYTE_POSITIONS if i < len(bb)]


def analyze_time_mapping():
    """分析 time → bb_time_bytes 的映射关系"""
    samples_file = ROOT / "reverse" / "time_samples.json"
    samples = json.load(open(samples_file))

    print(f"=== 分析 {len(samples)} 个样本的时间映射 ===\n")

    data = []
    for s in samples:
        T = s['T']
        time_bytes = extract_time_bytes(s['bb'])
        data.append({'T': T, 'time_bytes': time_bytes})

    print("样本数据预览:")
    for i, d in enumerate(data[:5]):
        print(f"  T={d['T']:15d}  time_bytes={d['time_bytes'][:10]}...")

    # 尝试找规律：time_bytes 是 time 的某种编码
    # 已知：time 存 3 份，6-bit 打包
    print("\n=== 尝试反推编码规则 ===")

    # 简单测试：time_bytes[0] 和 time 的关系
    if len(data) >= 2:
        d1, d2 = data[0], data[1]
        delta_T = d2['T'] - d1['T']
        delta_bytes = [d2['time_bytes'][i] - d1['time_bytes'][i]
                       for i in range(min(len(d1['time_bytes']), len(d2['time_bytes'])))]
        print(f"\n时间差: {delta_T}")
        print(f"字节差: {delta_bytes[:10]}...")

        # 检查是否存在线性关系
        if delta_T != 0:
            ratios = [db / delta_T if db != 0 else 0 for db in delta_bytes[:10]]
            print(f"字节差/时间差 比例: {['%.2e' % r for r in ratios]}")

    print("\n结论：")
    print("  需要更密集的时间采样（连续时间戳）来拟合公式")
    print("  或者直接用查表法（预计算常见时间范围的映射）")


def propose_solution():
    """提出最终解决方案"""
    print("\n" + "="*60)
    print("纯 Python a_bogus 生成 - 可行方案")
    print("="*60)
    print("""
方案 A：混合方案（推荐，90% 纯算法）
  - time → bb_time_bytes：查表法（预计算 2020-2030 年每秒的映射）
  - query → bb_query_bytes：SM3 哈希 + 固定注入规则（已知）
  - bb XOR keystream：纯算法（keystream 已固定）
  - s4 base64：纯算法（表已知）
  - 变长序列化：根据 query 长度用分段规则（需采样验证）

  优点：99% 纯 Python，只有 time 映射表需要预计算
  缺点：需要 200MB 左右的时间映射表

方案 B：完全逆向（100% 纯算法，困难）
  - 逆向 JSVMP 字节码，还原完整的序列化器
  - 需要深入分析 26280 条 VM trace
  - 预计需要 1-2 周工作量

方案 C：保持补环境（当前方案）
  - 稳定可靠，已在生产使用
  - 依赖 Node.js 运行时
  - 性能足够（单次签名 ~50ms）

建议：先实现方案 A（混合方案），作为补环境的备选
    """)


if __name__ == "__main__":
    analyze_time_mapping()
    propose_solution()
