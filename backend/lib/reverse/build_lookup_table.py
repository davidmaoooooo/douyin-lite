# -*- coding: utf-8 -*-
"""
最终方案：大规模生成 time → bb 映射表

策略：
1. 用补环境批量生成 a_bogus
2. 解码得到 bb
3. 建立密集映射表（每秒或每 10 秒）
4. 纯 Python 查表 + XOR + s4 编码
"""
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

# s4 解码
S4_TABLE = "Dkdpgh2ZmsQB80/MfvV36XI1R45-WUAlEixNLwoqYTOPuzKFjJnry79HbGcaStCe"
S4_REVERSE = {c: i for i, c in enumerate(S4_TABLE)}

def s4_decode(encoded):
    result = []
    for i in range(0, len(encoded), 4):
        chunk = encoded[i:i+4]
        if len(chunk) < 2:
            break
        b1, b2 = S4_REVERSE.get(chunk[0], 0), S4_REVERSE.get(chunk[1], 0)
        result.append((b1 << 2) | (b2 >> 4))
        if len(chunk) > 2 and chunk[2] in S4_REVERSE:
            b3 = S4_REVERSE[chunk[2]]
            result.append(((b2 & 0x0f) << 4) | (b3 >> 2))
            if len(chunk) > 3 and chunk[3] in S4_REVERSE:
                b4 = S4_REVERSE[chunk[3]]
                result.append(((b3 & 0x03) << 6) | b4)
    return list(result)

def generate_abogus_node(url):
    """调用补环境生成 a_bogus"""
    js_code = f'''
const {{ get_a_bogus }} = require("./lib/runtime/bdms/index.js");
const r = get_a_bogus({json.dumps(url)}, "");
if (global._process) global.process = global._process;
console.log(JSON.stringify({{a_bogus:r}}));
process.exit(0);
'''
    result = subprocess.run(['node', '-e', js_code],
                          capture_output=True, text=True, timeout=30,
                          cwd=str(ROOT))
    for line in result.stdout.strip().split('\n'):
        if line.startswith('{'):
            return json.loads(line).get('a_bogus', '')
    return ''

print("=== 大规模生成时间映射表 ===\n")

# 采样范围：2024-2025 年，每 60 秒 1 个样本
start_time = 1704067200000  # 2024-01-01 00:00:00
end_time = 1735689600000    # 2025-01-01 00:00:00
step = 60000  # 60 秒

total_samples = (end_time - start_time) // step
print(f"采样范围: 2024-2025 年")
print(f"步长: 60 秒")
print(f"预计样本数: {total_samples:,}")
print(f"预计时间: {total_samples * 0.5 / 3600:.1f} 小时（假设每个 0.5 秒）\n")

print("改为小范围测试：100 个样本\n")

# 小范围测试
mapping = {}
T = start_time

for i in range(100):
    url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=1&_t={T}"
    a_bogus = generate_abogus_node(url)

    if a_bogus and len(a_bogus) == 192:
        decoded = s4_decode(a_bogus)
        if len(decoded) == 144:
            bb = decoded[4:]  # 去掉随机头
            mapping[str(T)] = bb
            if (i + 1) % 10 == 0:
                print(f"  [{i+1}/100] T={T}, bb_len={len(bb)}")

    T += step
    time.sleep(0.05)

# 保存
out_file = ROOT / "lib" / "reverse" / "time_mapping_2024_100samples.json"
json.dump(mapping, open(out_file, "w"))

print(f"\n完成！采集 {len(mapping)} 个样本")
print(f"已保存: {out_file.relative_to(ROOT)}")
