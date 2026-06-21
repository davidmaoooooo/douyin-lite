# -*- coding: utf-8 -*-
"""用 paired.json 同次签名数据, Python 复现算法, 逐字节对比真实 bb。
目标: 确认 bb 的构造, 进而解 bb->fin。
"""
import sys, json
sys.path.insert(0, "lib/abogus_rebuild")
import abogus_new as A

o = json.load(open("lib/abogus_rebuild/paired.json"))
euc = o["euc"]
bb = [x for x in o["longs"]["L133_171"] if x < 256]
fin = [x for x in o["longs"]["L137_171"] if x < 256]
ua_plain = [x for x in o["longs"]["L125_77"] if x < 256]
ua_cipher = [x for x in o["longs"]["L125_66"] if x < 256]
env = [x for x in o["longs"]["L41_49"] if x < 256]

inp_q = euc[0]    # query (489)
inp_s = euc[1]    # dhzx
inp_u = euc[2]    # UA处理值 (168)

# 三次 SM3 (write 预处理 = encodeURIComponent.replace, 我的 sm3_of_str 已含)
q_list = A.sm3_sum_bytes(A.sm3_of_str(inp_q))   # query 双SM3
s_list = A.sm3_sum_bytes(A.sm3_of_str(inp_s))   # dhzx 双SM3
u_list = A.sm3_of_str(inp_u)                     # UA 单SM3

print("query 双SM3:", list(q_list))
print("dhzx  双SM3:", list(s_list))
print("UA    单SM3:", list(u_list))
print()
print("real bb (%d):" % len(bb))
print(bb)
print("\nreal fin (%d):" % len(fin))
print(fin)
print("\nenv (%d): %s" % (len(env), "".join(chr(c) for c in env)))
print("UA RC4 keystream[:8]:", [ua_plain[i] ^ ua_cipher[i] for i in range(8)])

# bb 长度132, env长度41. 旧版bb = 44字节模板 + window_env_list + 校验
# 新版: 看 bb 后段是否含 env 派生
# bb里找 env 字节序列
env_str = "".join(chr(c) for c in env)
print("\nbb 后段(从40起):", bb[40:])

json.dump({"q_list": list(q_list), "s_list": list(s_list), "u_list": list(u_list),
           "bb": bb, "fin": fin, "env": env}, open("lib/abogus_rebuild/recon.json", "w"))
