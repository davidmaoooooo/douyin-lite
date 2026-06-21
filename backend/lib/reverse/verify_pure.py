# -*- coding: utf-8 -*-
"""验证纯 Python 生成的 a_bogus 是否有效"""
import sys
sys.path.insert(0, 'D:/python-project/douyin-api')

from lib.reverse.generate_abogus_pure import generate_abogus_pure
import httpx
import json

# 加载 cookie
cfg = json.load(open('D:/python-project/douyin-api/config/cookie.json', encoding='utf-8'))

# 生成 a_bogus（使用映射表范围内的时间）
T = 1704070000000  # 在 2024-01-01 范围内
url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/"
params = {
    'aweme_id': '7123456789012345678',
    'device_platform': 'webapp',
    'aid': '6383',
    '_t': T
}

# 纯 Python 生成
query_str = '&'.join(f'{k}={v}' for k, v in params.items())
full_url = f"{url}?{query_str}"
a_bogus_pure = generate_abogus_pure(full_url, T)

print(f"纯 Python 生成: {a_bogus_pure[:60]}...")
print(f"长度: {len(a_bogus_pure)}")

# 实际请求测试
params['a_bogus'] = a_bogus_pure

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.douyin.com/",
}

print("\n发送请求测试...")
try:
    with httpx.Client(verify=False, timeout=10) as client:
        resp = client.get(url, params=params, headers=headers, cookies=cfg)

    print(f"HTTP {resp.status_code}")

    if resp.status_code == 200:
        try:
            data = resp.json()
            print(f"返回 keys: {list(data.keys())[:10]}")
            if 'aweme_detail' in data or 'status_code' in data:
                print("SUCCESS: 纯 Python a_bogus 有效！")
            else:
                print("FAIL: 返回数据异常")
                print(f"Body: {resp.text[:200]}")
        except:
            print(f"JSON 解析失败: {resp.text[:200]}")
    else:
        print(f"FAIL: HTTP {resp.status_code}")
        print(f"Body: {resp.text[:300]}")
except Exception as e:
    print(f"请求失败: {e}")
