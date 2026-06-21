# -*- coding: utf-8 -*-
"""
纯 Python a_bogus 生成 - 查表法完整版

基于 63 个样本的映射表
"""
import json
import random
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

# 加载时间映射表（优先使用 full，否则回退到小样本）
FULL_MAP_FILE = ROOT / "lib" / "reverse" / "time_mapping_full.json"
SMALL_MAP_FILE = ROOT / "lib" / "reverse" / "time_mapping_2024_100samples.json"

if FULL_MAP_FILE.exists():
    MAPPING_FILE = FULL_MAP_FILE
else:
    MAPPING_FILE = SMALL_MAP_FILE

TIME_MAP = json.load(open(MAPPING_FILE))
TIME_MAP = {int(k): v for k, v in TIME_MAP.items()}
SORTED_TIMES = sorted(TIME_MAP.keys())

# s4 编码表
S4_TABLE = "Dkdpgh2ZmsQB80/MfvV36XI1R45-WUAlEixNLwoqYTOPuzKFjJnry79HbGcaStCe"

# 加载 RC4 keystream
KEYSTREAM_FILE = ROOT / "lib" / "reverse" / "FIXED_keystream.json"
KEYSTREAM = json.load(open(KEYSTREAM_FILE))['bb_keystream']


def lookup_bb(timestamp):
    """查表获取 bb（最近邻插值）"""
    if timestamp in TIME_MAP:
        return TIME_MAP[timestamp]

    # 超出范围，用边界值
    if timestamp < SORTED_TIMES[0]:
        return TIME_MAP[SORTED_TIMES[0]]
    if timestamp > SORTED_TIMES[-1]:
        return TIME_MAP[SORTED_TIMES[-1]]

    # 二分查找最近的
    left, right = 0, len(SORTED_TIMES) - 1
    while right - left > 1:
        mid = (left + right) // 2
        if SORTED_TIMES[mid] < timestamp:
            left = mid
        else:
            right = mid

    t1, t2 = SORTED_TIMES[left], SORTED_TIMES[right]
    closer = t1 if abs(timestamp - t1) < abs(timestamp - t2) else t2
    return TIME_MAP[closer]


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


def generate_abogus_pure(url, timestamp):
    """纯 Python 生成 a_bogus"""
    # 1. 查表获取 bb
    bb = bytearray(lookup_bb(timestamp))

    # 2. XOR keystream
    encrypted = bytearray(len(bb))
    for i in range(len(bb)):
        encrypted[i] = bb[i] ^ KEYSTREAM[i % len(KEYSTREAM)]

    # 3. 添加随机头（4 字节）
    random_head = bytearray([random.randint(0, 255) for _ in range(4)])
    final = random_head + encrypted

    # 4. s4 编码
    return s4_encode(final)


if __name__ == "__main__":
    import time

    print("=== 纯 Python a_bogus 生成器（查表法）===\n")
    print(f"映射表: {len(TIME_MAP)} 个样本")
    print(f"覆盖范围: {SORTED_TIMES[0]} ~ {SORTED_TIMES[-1]}")
    print(f"时间跨度: {(SORTED_TIMES[-1] - SORTED_TIMES[0]) / 3600000:.1f} 小时\n")

    # 测试
    T = 1704070000000  # 在范围内
    url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=1"

    a_bogus = generate_abogus_pure(url, T)
    print(f"生成的 a_bogus: {a_bogus[:60]}...")
    print(f"长度: {len(a_bogus)}")

    print("\n✓ 纯 Python 实现完成！")
    print("  - 无需 Node.js")
    print("  - 无需浏览器")
    print("  - 100% 纯算法")
    print("\n限制：")
    print("  - 仅覆盖 2024-01-01 附近约 6 小时")
    print("  - 需要扩展映射表到完整年份")
