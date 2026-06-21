# -*- coding: utf-8 -*-
"""解码 184 长度 a_bogus，对齐字节结构。
s4 表来自旧 douyin.js: result_encrypt(...,"s4")
新版若沿用同一编码框架，解码后应能看出 bb 结构。
"""

S4 = "Dkdpgh2ZmsQB80/MfvV36XI1R45-WUAlEixNLwoqYTOPuzKFjJnry79HbGcaStCe"  # 64字符，末位'=' 在旧表是占位

def s4_decode(enc):
    """逆 result_encrypt：每4字符->3字节。enc 末尾可能有 '=' 占位。"""
    enc = enc.rstrip("=")
    # 建索引表
    idx = {c: i for i, c in enumerate(S4)}
    out = []
    # result_encrypt 是把每3字节(24bit)按 18/12/6/0 取6bit查表 -> 4字符
    # 逆过程：每4字符 -> 24bit -> 3字节
    for i in range(0, len(enc), 4):
        chunk = enc[i:i+4]
        bits = 0
        n = len(chunk)
        vals = []
        ok = True
        for c in chunk:
            if c not in idx:
                ok = False
                break
            vals.append(idx[c])
        if not ok:
            out.append(None)
            continue
        # 拼 24bit
        if n == 4:
            num = (vals[0] << 18) | (vals[1] << 12) | (vals[2] << 6) | vals[3]
            out += [(num >> 16) & 255, (num >> 8) & 255, num & 255]
        elif n == 3:
            num = (vals[0] << 18) | (vals[1] << 12) | (vals[2] << 6)
            out += [(num >> 16) & 255, (num >> 8) & 255]
        elif n == 2:
            num = (vals[0] << 18) | (vals[1] << 12)
            out += [(num >> 16) & 255]
    return out


def diff_bytes(a, b):
    """返回不同字节的索引列表"""
    d = []
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            d.append(i)
    if len(a) != len(b):
        d.append(f"len:{len(a)}vs{len(b)}")
    return d


if __name__ == "__main__":
    import json, os
    here = os.path.dirname(__file__)
    samples = json.load(open(os.path.join(here, "samples.json"), encoding="utf-8"))

    q1 = samples["query_dim"]["q=1"]
    qa = samples["query_dim"]["q=a"]
    qc = samples["query_dim"]["q=c"]

    b1 = s4_decode(q1)
    ba = s4_decode(qa)
    bc = s4_decode(qc)

    print(f"q=1 解码字节数: {len(b1)}")
    print("q=1 bytes:", b1)
    print()
    print("q=1 vs q=a 差异字节索引:", diff_bytes(b1, ba))
    print("q=1 vs q=c 差异字节索引:", diff_bytes(b1, bc))
    print()
    # time 差分
    tb = samples["time_dim_q1_r05"]
    bt0 = s4_decode(tb["1700000000000"])
    bt1 = s4_decode(tb["1700000000001"])
    print("time +1ms 差异字节索引:", diff_bytes(bt0, bt1))
    bt1s = s4_decode(tb["1700000001000"])
    print("time +1000ms 差异 (注意长度!):", diff_bytes(bt0, bt1s), "lens", len(bt0), len(bt1s))
