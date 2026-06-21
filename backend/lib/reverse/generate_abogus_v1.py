# -*- coding: utf-8 -*-
"""
纯 Python a_bogus 生成 - 混合方案第一版

实现：
1. 固定字节硬编码
2. 时间字节从样本插值
3. RC4 XOR
4. s4 编码
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

# 固定字节（从 10 个样本验证）
FIXED_BYTES = {
    11: 217, 19: 52, 39: 107, 43: 160, 47: 7, 51: 3, 55: 186, 59: 95,
    63: 128, 71: 200, 75: 121, 79: 74, 83: 250, 87: 82, 91: 103, 95: 133,
    99: 223, 103: 158, 107: 56, 111: 235, 115: 178, 119: 98, 123: 84,
    127: 71, 131: 41
}

# s4 编码表
S4_TABLE = "Dkdpgh2ZmsQB80/MfvV36XI1R45-WUAlEixNLwoqYTOPuzKFjJnry79HbGcaStCe"


class TimeLookup:
    """时间戳查表（最近邻插值）"""
    def __init__(self):
        samples_file = ROOT / "lib" / "reverse" / "samples_140byte.json"
        samples = json.load(open(samples_file))
        self.table = {s['T']: s['bb'] for s in samples}
        self.sorted_times = sorted(self.table.keys())

    def lookup(self, timestamp):
        if timestamp in self.table:
            return self.table[timestamp]
        # 最近邻
        if timestamp < self.sorted_times[0]:
            return self.table[self.sorted_times[0]]
        if timestamp > self.sorted_times[-1]:
            return self.table[self.sorted_times[-1]]
        # 二分查找
        left, right = 0, len(self.sorted_times) - 1
        while right - left > 1:
            mid = (left + right) // 2
            if self.sorted_times[mid] < timestamp:
                left = mid
            else:
                right = mid
        t1, t2 = self.sorted_times[left], self.sorted_times[right]
        return self.table[t1 if abs(timestamp - t1) < abs(timestamp - t2) else t2]


def s4_encode(data):
    """s4 base64 编码"""
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


def generate_abogus_v1(url, timestamp):
    """生成 a_bogus（混合方案 v1）"""
    # 1. 查表获取时间相关的 bb
    lookup = TimeLookup()
    ref_bb = lookup.lookup(timestamp)

    # 2. 构造 bb（固定字节 + 时间字节）
    bb = bytearray(140)
    for i in range(140):
        if i in FIXED_BYTES:
            bb[i] = FIXED_BYTES[i]
        else:
            bb[i] = ref_bb[i]  # 时间字节从查表结果复制

    # 3. 加载 RC4 keystream
    keystream_file = ROOT / "lib" / "reverse" / "FIXED_keystream.json"
    keystream = json.load(open(keystream_file))
    ks = keystream['bb_keystream']

    # 4. XOR
    encrypted = bytearray(len(bb))
    for i in range(len(bb)):
        encrypted[i] = bb[i] ^ ks[i % len(ks)]

    # 5. 添加随机头（固定值测试）
    final = bytearray([171, 85, 42, 85]) + encrypted

    # 6. s4 编码
    return s4_encode(final)


# 测试
if __name__ == "__main__":
    import time
    T = int(time.time() * 1000)
    url = "https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=1"

    a_bogus = generate_abogus_v1(url, T)
    print(f"生成 a_bogus: {a_bogus[:60]}...")
    print(f"长度: {len(a_bogus)}")
    print(f"\n当前实现: 基于 10 个样本的查表法")
    print(f"覆盖范围: {1700000002000} ~ {1700000018000}")
    print(f"精度: 时间戳超出范围会用边界值（不准确）")
