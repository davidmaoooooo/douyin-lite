# -*- coding: utf-8 -*-
"""
大规模生成时间映射表 - 后台运行版本

覆盖：2024-2026 年（2年）
步长：600 秒（10分钟）
预计样本：175,200 个
预计时间：24-48 小时
"""
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

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
    js_code = f'''
const {{ get_a_bogus }} = require("./lib/runtime/bdms/index.js");
const r = get_a_bogus({json.dumps(url)}, "");
if (global._process) global.process = global._process;
console.log(JSON.stringify({{a_bogus:r}}));
process.exit(0);
'''
    try:
        result = subprocess.run(['node', '-e', js_code],
                              capture_output=True, text=True, timeout=30,
                              cwd=str(ROOT))
        for line in result.stdout.strip().split('\n'):
            if line.startswith('{'):
                return json.loads(line).get('a_bogus', '')
    except:
        pass
    return ''

# 配置
START = 1704067200000   # 2024-01-01 00:00:00
END = 1767225600000     # 2026-01-01 00:00:00
STEP = 600000           # 10 分钟

total = (END - START) // STEP
out_file = ROOT / "lib" / "reverse" / "time_mapping_2024_2026.json"

print(f"=== 大规模映射表生成 ===")
print(f"时间范围: 2024-01-01 ~ 2026-01-01")
print(f"步长: 10 分钟")
print(f"预计样本: {total:,}")
print(f"预计时间: {total * 0.5 / 3600:.1f} 小时")
print(f"输出: {out_file.name}\n")

# 检查是否已有进度
if out_file.exists():
    mapping = json.load(open(out_file))
    mapping = {int(k): v for k, v in mapping.items()}
    print(f"发现已有进度: {len(mapping):,} 样本")
else:
    mapping = {}

T = START
count = 0
failed = 0
start_time = time.time()

try:
    while T < END:
        if T not in mapping:
            url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=1&_t={T}"
            a_bogus = generate_abogus_node(url)

            if a_bogus and len(a_bogus) == 192:
                decoded = s4_decode(a_bogus)
                if len(decoded) == 144:
                    bb = decoded[4:]
                    mapping[T] = bb
                    count += 1
                else:
                    failed += 1
            else:
                failed += 1

            # 每 100 个保存一次
            if count % 100 == 0 and count > 0:
                json.dump({str(k): v for k, v in mapping.items()},
                         open(out_file, "w"))
                elapsed = time.time() - start_time
                progress = (T - START) / (END - START) * 100
                rate = count / elapsed if elapsed > 0 else 0
                eta = (total - count) / rate / 3600 if rate > 0 else 0
                print(f"[{progress:5.2f}%] 成功:{count:,} 失败:{failed} "
                      f"速率:{rate:.1f}/s ETA:{eta:.1f}h")

        T += STEP
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n中断，保存进度...")

# 最终保存
json.dump({str(k): v for k, v in mapping.items()}, open(out_file, "w"))

print(f"\n完成！")
print(f"成功: {count:,} 样本")
print(f"失败: {failed}")
print(f"已保存: {out_file}")
