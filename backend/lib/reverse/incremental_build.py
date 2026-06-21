# -*- coding: utf-8 -*-
"""
渐进式生成映射表 - 每次运行生成 500 个样本

多次运行累积到完整映射表
"""
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

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
        return ''

# 配置
STEP = 600000  # 10 分钟
BATCH = 500     # 每次 500 个
out_file = ROOT / "lib" / "reverse" / "time_mapping_full.json"

# 加载已有进度
if out_file.exists():
    mapping = json.load(open(out_file))
    mapping = {int(k): v for k, v in mapping.items()}
else:
    mapping = {}

# 确定下一个起始点
if mapping:
    last_T = max(mapping.keys())
    start_T = last_T + STEP
else:
    start_T = 1704067200000  # 2024-01-01

print(f"当前进度: {len(mapping)} 样本")
print(f"本次生成: {BATCH} 个，从 T={start_T}\n")

T = start_T
success = 0

for i in range(BATCH):
    url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=1&_t={T}"
    a_bogus = generate_abogus_node(url)

    if a_bogus and len(a_bogus) == 192:
        decoded = s4_decode(a_bogus)
        if len(decoded) == 144:
            mapping[T] = decoded[4:]
            success += 1

    if (i + 1) % 50 == 0:
        print(f"  [{i+1}/{BATCH}] 成功: {success}")

    T += STEP
    time.sleep(0.05)

# 保存
json.dump({str(k): v for k, v in mapping.items()}, open(out_file, "w"))

print(f"\n完成！总样本: {len(mapping):,}")
print(f"本次新增: {success}")
print(f"已保存: {out_file.name}")
print(f"\n提示: 再次运行此脚本继续生成")
