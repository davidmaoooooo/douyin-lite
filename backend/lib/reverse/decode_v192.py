# -*- coding: utf-8 -*-
"""反向解码 192 长度 a_bogus，找出实际字节结构"""
import sys
sys.path.insert(0, 'D:/python-project/douyin-api')
from utils.request import Request

# s4 解码表
S4_TABLE = "Dkdpgh2ZmsQB80/MfvV36XI1R45-WUAlEixNLwoqYTOPuzKFjJnry79HbGcaStCe"
S4_REVERSE = {c: i for i, c in enumerate(S4_TABLE)}


def s4_decode(encoded):
    """s4 base64 解码"""
    result = []
    for i in range(0, len(encoded), 4):
        chunk = encoded[i:i+4]
        if len(chunk) < 2:
            break

        b1 = S4_REVERSE.get(chunk[0], 0)
        b2 = S4_REVERSE.get(chunk[1], 0)

        result.append((b1 << 2) | (b2 >> 4))

        if len(chunk) > 2 and chunk[2] in S4_REVERSE:
            b3 = S4_REVERSE[chunk[2]]
            result.append(((b2 & 0x0f) << 4) | (b3 >> 2))

            if len(chunk) > 3 and chunk[3] in S4_REVERSE:
                b4 = S4_REVERSE[chunk[3]]
                result.append(((b3 & 0x03) << 6) | b4)

    return bytes(result)


# 生成一个 a_bogus
r = Request()
url = 'https://www.douyin.com/aweme/v1/web/aweme/detail/'
params = r.get_params({'aweme_id': '1'})
a_bogus = r.get_sign_bdms(url, params, 'GET', '')

print(f"生成的 a_bogus: {a_bogus}")
print(f"长度: {len(a_bogus)}")

# s4 解码
decoded = s4_decode(a_bogus)
print(f"\ns4 解码后字节数: {len(decoded)}")
print(f"前 20 字节: {list(decoded[:20])}")
print(f"后 20 字节: {list(decoded[-20:])}")

# 分析结构
print(f"\n结构分析:")
print(f"  随机头（前4字节）: {list(decoded[:4])}")
print(f"  核心 bb（剩余）: {len(decoded) - 4} 字节")

# 192 字符 s4 编码 → 实际字节数
expected_bytes = (192 * 3 + 3) // 4
print(f"\n理论字节数（192 s4字符）: {expected_bytes}")
print(f"实际字节数: {len(decoded)}")
print(f"差异: {expected_bytes - len(decoded)}")
