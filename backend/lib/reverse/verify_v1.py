# -*- coding: utf-8 -*-
"""验证混合方案生成的 a_bogus 是否有效"""
import sys
sys.path.insert(0, 'D:/python-project/douyin-api')

from lib.reverse.generate_abogus_v1 import generate_abogus_v1
import httpx
import json

# 加载 cookie
cfg = json.load(open('D:/python-project/douyin-api/config/cookie.json', encoding='utf-8'))

# 生成 a_bogus（使用样本范围内的时间）
T = 1700000010000  # 在采样范围内
url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=7123456789012345678&device_platform=webapp&aid=6383&_t={T}"

a_bogus_v1 = generate_abogus_v1(url, T)
print(f"混合方案生成: {a_bogus_v1[:60]}...")
print(f"长度: {len(a_bogus_v1)}")

# 对比：用补环境生成同样 URL 的 a_bogus
from utils.request import Request
r = Request()
params = r.get_params({'aweme_id': '7123456789012345678', '_t': T})
a_bogus_bdms = r.get_sign_bdms(url, params, 'GET', '')
print(f"\n补环境生成: {a_bogus_bdms[:60]}...")
print(f"长度: {len(a_bogus_bdms)}")

print(f"\n是否一致: {'YES' if a_bogus_v1 == a_bogus_bdms else 'NO'}")

if a_bogus_v1 != a_bogus_bdms:
    print("\n差异分析:")
    for i in range(min(len(a_bogus_v1), len(a_bogus_bdms))):
        if a_bogus_v1[i] != a_bogus_bdms[i]:
            print(f"  位置 {i}: '{a_bogus_v1[i]}' vs '{a_bogus_bdms[i]}'")
            if i >= 10:
                print("  ... (省略剩余差异)")
                break

    # 解码对比
    print("\n尝试解码对比 bb:")
    from lib.reverse.decode_v192 import s4_decode
    bb_v1 = s4_decode(a_bogus_v1)
    bb_bdms = s4_decode(a_bogus_bdms)

    print(f"v1 bb 长度: {len(bb_v1)}")
    print(f"bdms bb 长度: {len(bb_bdms)}")

    if len(bb_v1) == len(bb_bdms):
        diffs = [i for i in range(len(bb_v1)) if bb_v1[i] != bb_bdms[i]]
        print(f"差异字节数: {len(diffs)}")
        print(f"差异位置: {diffs[:20]}")

