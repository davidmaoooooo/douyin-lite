# -*- coding: utf-8 -*-
"""通过 Node 补环境批量生成 a_bogus，然后 s4 解码得到 bb"""
import json
import subprocess
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


def generate_abogus_node(url, uifid=""):
    """调用 Node 生成 a_bogus"""
    js_code = f'''
const {{ get_a_bogus }} = require("./lib/runtime/bdms/index.js");
const r = get_a_bogus({json.dumps(url)}, {json.dumps(uifid)});
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


print("=== 通过补环境批量采集 bb ===\n")

samples = []
base_T = 1700000000000

# 生成不同时间的 URL，调用补环境生成 a_bogus
for i in range(20):
    T = base_T + i * 1000
    url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=1&_t={T}"

    a_bogus = generate_abogus_node(url)
    if a_bogus and len(a_bogus) == 192:
        # s4 解码
        decoded = s4_decode(a_bogus)
        if len(decoded) == 144:
            bb = decoded[4:]  # 去掉 4 字节随机头
            samples.append({"T": T, "query": f"aweme_id=1&_t={T}", "bb": bb})
            print(f"  [{len(samples)}/20] T={T}, bb_len={len(bb)}")

# 保存
out_file = ROOT / "lib" / "reverse" / "samples_140byte.json"
json.dump(samples, open(out_file, "w"), indent=2)
print(f"\n采集: {len(samples)} 条 140 字节样本")
print(f"已保存: {out_file.relative_to(ROOT)}")
