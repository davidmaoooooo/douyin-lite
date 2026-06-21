# -*- coding: utf-8 -*-
"""精确解码 + 寻找旧 bb 模板锚点。
旧 bb 已知固定值: b[18]=44, aid=6383(0x18EF), pageId=6241(0x1861) 等。
新版若沿用，解码字节里应能找到这些锚点。
"""
S4 = "Dkdpgh2ZmsQB80/MfvV36XI1R45-WUAlEixNLwoqYTOPuzKFjJnry79HbGcaStCe"
IDX = {c: i for i, c in enumerate(S4)}


def s4_decode(enc):
    enc = enc.rstrip("=")
    out = []
    for i in range(0, len(enc), 4):
        chunk = enc[i:i+4]
        vals = [IDX[c] for c in chunk]
        n = len(vals)
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


def find_anchors(b):
    """在字节序列里找已知锚点"""
    res = {}
    # 44 (b[18])
    res["44_positions"] = [i for i, x in enumerate(b) if x == 44]
    # aid=6383: 大端 0x18EF=[24,239] 或小端 [239,24]
    for i in range(len(b)-1):
        if b[i] == 24 and b[i+1] == 239:
            res.setdefault("aid_BE_24_239", []).append(i)
        if b[i] == 239 and b[i+1] == 24:
            res.setdefault("aid_LE_239_24", []).append(i)
    # pageId=6241: 0x1861=[24,97]
    for i in range(len(b)-1):
        if b[i] == 24 and b[i+1] == 97:
            res.setdefault("pageId_24_97", []).append(i)
        if b[i] == 97 and b[i+1] == 24:
            res.setdefault("pageId_97_24", []).append(i)
    return res


if __name__ == "__main__":
    import json, os
    here = os.path.dirname(__file__)
    s = json.load(open(os.path.join(here, "samples.json"), encoding="utf-8"))
    q1 = s["query_dim"]["q=1"]
    b = s4_decode(q1)
    print(f"q=1 字节数: {len(b)}")
    print("bytes:", b)
    print()
    print("锚点:", json.dumps(find_anchors(b), ensure_ascii=False))
    print()
    # 时间戳锚点: 1700000000000 = 0x18BCFE56800
    #  低4字节(b&0xFFFFFFFF) = 1700000000000 % 2^32 = ?
    t = 1700000000000
    lo = t & 0xFFFFFFFF
    print(f"time={t} lo32={lo} 大端字节={[(lo>>24)&255,(lo>>16)&255,(lo>>8)&255,lo&255]}")
    print(f"  /256^4 floor = {(t>>32)}")
