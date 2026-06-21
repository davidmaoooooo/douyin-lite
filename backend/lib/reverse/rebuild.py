# -*- coding: utf-8 -*-
"""用真实配套数据重建 bb 数组，对比 hook 到的真实 bb，定位新版 b[] 模板差异。
旧版 generate_rc4_bb_str 的 b[] 构造移植 + 真实 SM3 输入。
"""
import sys, json
sys.path.insert(0, "lib/abogus_rebuild")
from abogus_new import sm3_sum_bytes, sm3_of_str, rc4_encrypt_bytes, result_encrypt, gener_random

o = json.load(open("lib/abogus_rebuild/fullset.json"))
real_bb = [x for x in o["longs"]["L133_171_85"] if x < 256]
real_fin = [x for x in o["longs"]["L137_171_87"] if x < 256]
env_str_bytes = [x for x in o["longs"]["L41_49_48"] if x < 256]
ua_plain = [x for x in o["longs"]["L125_77_111"] if x < 256]
ua_cipher = [x for x in o["longs"]["L125_66_226"] if x < 256]

# SM3 明文输入
euc = o["euc"]
inp1 = euc[0]   # query+msToken+dhzx
inp2 = euc[1]   # dhzx
inp3 = euc[2]   # UA处理值

# 三次 SM3 (旧版: 前两个 double-sm3, UA 是 single sm3 of inp3)
url_list = sm3_sum_bytes(sm3_of_str(inp1))   # double sm3
cus_list = sm3_sum_bytes(sm3_of_str(inp2))   # double sm3
ua_list = sm3_of_str(inp3)                    # single sm3 of UA-encoded-str

print("real_bb len:", len(real_bb))
print("real_bb:", real_bb)
print("\nurl_list(query双SM3):", list(url_list))
print("cus_list(dhzx双SM3): ", list(cus_list))
print("ua_list (UA单SM3):   ", list(ua_list))
print("\nenv_str(%d): " % len(env_str_bytes), env_str_bytes)
print("UA RC4 keystream[:8]:", [ua_plain[i]^ua_cipher[i] for i in range(8)])

# 在 real_bb 里定位 url_list/cus_list/ua_list 的字节出现位置
def find_in(haystack, needle_byte):
    return [i for i, x in enumerate(haystack) if x == needle_byte]

print("\n=== 在 real_bb 里找 SM3 字节注入位 ===")
# 旧版: b[38]=url[21],b[39]=url[22]; b[40]=cus[21],b[41]=cus[22]; b[42]=ua[23],b[43]=ua[24]
for nm, lst in [("url", url_list), ("cus", cus_list), ("ua", ua_list)]:
    # 对每个 real_bb 位置，看它等于 lst 的哪些索引
    matches = []
    for bi, bv in enumerate(real_bb):
        idxs = [j for j, lv in enumerate(lst) if lv == bv]
        if idxs:
            matches.append(f"bb[{bi}]={bv}=={nm}[{idxs}]")
    print(f"{nm}: {matches[:15]}")

json.dump({"real_bb": real_bb, "real_fin": real_fin, "url_list": list(url_list),
           "cus_list": list(cus_list), "ua_list": list(ua_list), "env": env_str_bytes},
          open("lib/abogus_rebuild/rebuild.json", "w"))
