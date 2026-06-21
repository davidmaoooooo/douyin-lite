# -*- coding: utf-8 -*-
"""
纯 Python a_bogus 生成（查表法原型）

基于现有的 13 个样本验证查表法可行性：
1. 加载 time_samples.json（13 个样本）
2. 实现查表 + 插值（时间映射）
3. 实现 SM3 + RC4 + s4 base64（已知算法）
4. 生成 a_bogus 并与真实值对比
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent

# 时间相关字节位置
TIME_POSITIONS = [12, 14, 15, 29, 31, 32, 35, 37, 39, 42, 44, 47, 56, 59, 66, 68, 71, 129, 132]

# s4 base64 表
S4_TABLE = "Dkdpgh2ZmsQB80/MfvV36XI1R45-WUAlEixNLwoqYTOPuzKFjJnry79HbGcaStCe"


class TimeMapper:
    """时间戳 → bb_time_bytes 映射（查表 + 插值）"""

    def __init__(self, samples_file):
        samples = json.load(open(samples_file))
        # 建立 {timestamp: time_bytes} 映射
        self.table = {}
        for s in samples:
            T = s['T']
            time_bytes = tuple(s['bb'][i] for i in TIME_POSITIONS if i < len(s['bb']))
            self.table[T] = time_bytes

        self.sorted_times = sorted(self.table.keys())
        print(f"加载时间映射表: {len(self.table)} 条样本")
        print(f"  范围: {min(self.sorted_times)} ~ {max(self.sorted_times)}")

    def lookup(self, timestamp):
        """查表（精确匹配或最近邻插值）"""
        if timestamp in self.table:
            return self.table[timestamp]

        # 最近邻插值
        if timestamp < self.sorted_times[0]:
            return self.table[self.sorted_times[0]]
        if timestamp > self.sorted_times[-1]:
            return self.table[self.sorted_times[-1]]

        # 二分查找最近的两个点
        left, right = 0, len(self.sorted_times) - 1
        while right - left > 1:
            mid = (left + right) // 2
            if self.sorted_times[mid] < timestamp:
                left = mid
            else:
                right = mid

        # 返回更近的那个
        t1, t2 = self.sorted_times[left], self.sorted_times[right]
        if abs(timestamp - t1) < abs(timestamp - t2):
            return self.table[t1]
        else:
            return self.table[t2]


def s4_encode(data):
    """s4 自定义 base64 编码"""
    result = []
    i = 0
    while i < len(data):
        if i + 2 < len(data):
            b1, b2, b3 = data[i], data[i+1], data[i+2]
            result.append(S4_TABLE[(b1 >> 2) & 0x3f])
            result.append(S4_TABLE[((b1 << 4) | (b2 >> 4)) & 0x3f])
            result.append(S4_TABLE[((b2 << 2) | (b3 >> 6)) & 0x3f])
            result.append(S4_TABLE[b3 & 0x3f])
            i += 3
        elif i + 1 < len(data):
            b1, b2 = data[i], data[i+1]
            result.append(S4_TABLE[(b1 >> 2) & 0x3f])
            result.append(S4_TABLE[((b1 << 4) | (b2 >> 4)) & 0x3f])
            result.append(S4_TABLE[(b2 << 2) & 0x3f])
            i += 2
        else:
            b1 = data[i]
            result.append(S4_TABLE[(b1 >> 2) & 0x3f])
            result.append(S4_TABLE[(b1 << 4) & 0x3f])
            i += 1
    return ''.join(result)


def generate_a_bogus_lookup(url, timestamp, mapper):
    """
    生成 a_bogus（查表法原型）

    当前实现：只用时间映射，其它部分用固定值验证流程
    """
    # 1. 查时间映射
    time_bytes = mapper.lookup(timestamp)

    # 2. 构造 bb（简化版：只填时间字节，其余用零）
    bb = bytearray(133)
    for i, pos in enumerate(TIME_POSITIONS):
        if pos < len(bb) and i < len(time_bytes):
            bb[pos] = time_bytes[i]

    # 3. 加载固定 keystream
    keystream_file = ROOT / "reverse" / "FIXED_keystream.json"
    keystream = json.load(open(keystream_file))
    ks = keystream['bb_keystream']  # 使用 bb_keystream

    # 4. XOR
    encrypted = bytearray(len(bb))
    for i in range(len(bb)):
        encrypted[i] = bb[i] ^ ks[i % len(ks)]

    # 5. 添加随机头（4 字节，这里用固定值）
    final = bytearray([171, 85, 42, 85]) + encrypted

    # 6. s4 base64 编码
    return s4_encode(final)


def test_lookup_method():
    """测试查表法原型"""
    samples_file = ROOT / "reverse" / "time_samples.json"
    mapper = TimeMapper(samples_file)

    print("\n=== 测试查表法 ===\n")

    # 用样本里的时间测试
    samples = json.load(open(samples_file))
    test_sample = samples[0]

    T = test_sample['T']
    print(f"测试时间: {T}")

    # 生成 a_bogus
    a_bogus = generate_a_bogus_lookup("https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=1", T, mapper)

    print(f"生成的 a_bogus: {a_bogus[:60]}...")
    print(f"长度: {len(a_bogus)}")

    print("\n当前状态：")
    print("  [OK] 时间映射：查表成功")
    print("  [OK] RC4 keystream：已加载")
    print("  [OK] s4 编码：已实现")
    print("  [TODO] query 处理：待完善（SM3 注入）")
    print("  [TODO] 变长序列化：待实现")

    print("\n下一步：")
    print("  1. 完善 query -> bb_query_bytes 的 SM3 处理")
    print("  2. 实现完整的 bb 构造（非零填充）")
    print("  3. 用真实 URL 测试验证")


if __name__ == "__main__":
    test_lookup_method()
