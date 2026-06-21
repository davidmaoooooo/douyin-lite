# -*- coding: utf-8 -*-
"""
a_bogus 新版(184长度) Python 复现 / 逆向工作脚本。

主干复用旧版 douyin.js generate_rc4_bb_str 流程, 已知改动:
  - 后缀 cus -> dhzx (algo_inputs.md 直接捕获 SM3 明文确认)
  - random_head gener_random option 常量疑似 [3,82],[117,34],[184,169]
  - 最终 RC4 密钥未知 (旧版 [121])
  - bb 模板布局可能变化

本脚本: 移植 SM3/rc4_encrypt/result_encrypt/gener_random,
        用 samples_clean.json 基线逐字节对齐, 推导 RC4 key 与 bb 模板。

所有结论写文件 (Windows console 中文乱码), print 用英文。
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- s4 编码表 (与旧版一致) ----------------
S4 = "Dkdpgh2ZmsQB80/MfvV36XI1R45-WUAlEixNLwoqYTOPuzKFjJnry79HbGcaStCe"
S4_IDX = {c: i for i, c in enumerate(S4)}

# result_encrypt 编码表
S_OBJ = {
    "s0": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",
    "s1": "Dkdpgh4ZKsQB80/Mfvw36XI1R25+WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe=",
    "s2": "Dkdpgh4ZKsQB80/Mfvw36XI1R25-WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe=",
    "s3": "ckdp1h4ZKsUB80/Mfvw36XIgR25+WQAlEi7NLboqYTOPuzmFjJnryx9HVGDaStCe",
    "s4": "Dkdpgh2ZmsQB80/MfvV36XI1R45-WUAlEixNLwoqYTOPuzKFjJnry79HbGcaStCe",
}


def s4_encode(byte_list):
    """result_encrypt 等价 (用 s4 表), 输入字节列表 -> base64变体字符串。"""
    return result_encrypt(bytes(byte_list).decode("latin-1"), "s4")


def s4_decode(enc):
    enc = enc.rstrip("=")
    out = []
    for i in range(0, len(enc), 4):
        chunk = enc[i:i + 4]
        vals = [S4_IDX[c] for c in chunk]
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


# ---------------- result_encrypt (douyin.js 移植) ----------------
def get_long_int(round_, long_str):
    round_ = round_ * 3
    def cc(idx):
        return ord(long_str[idx]) if idx < len(long_str) else 0
    return (cc(round_) << 16) | (cc(round_ + 1) << 8) | (cc(round_ + 2))


def result_encrypt(long_str, num=None):
    table = S_OBJ[num]
    const0, const1, const2 = 16515072, 258048, 4032
    result = ""
    lound = 0
    long_int = get_long_int(lound, long_str)
    total = int(len(long_str) / 3 * 4)
    for i in range(total):
        if i // 4 != lound:
            lound += 1
            long_int = get_long_int(lound, long_str)
        key = i % 4
        if key == 0:
            temp_int = (long_int & const0) >> 18
        elif key == 1:
            temp_int = (long_int & const1) >> 12
        elif key == 2:
            temp_int = (long_int & const2) >> 6
        else:
            temp_int = long_int & 63
        result += table[temp_int]
    return result


# ---------------- RC4 (douyin.js 移植) ----------------
def rc4_encrypt_bytes(plain_bytes, key_bytes):
    s = list(range(256))
    j = 0
    klen = len(key_bytes)
    for i in range(256):
        j = (j + s[i] + key_bytes[i % klen]) % 256
        s[i], s[j] = s[j], s[i]
    i = j = 0
    out = []
    for k in range(len(plain_bytes)):
        i = (i + 1) % 256
        j = (j + s[i]) % 256
        s[i], s[j] = s[j], s[i]
        t = (s[i] + s[j]) % 256
        out.append(s[t] ^ plain_bytes[k])
    return out


def rc4_keystream(key_bytes, length):
    s = list(range(256))
    j = 0
    klen = len(key_bytes)
    for i in range(256):
        j = (j + s[i] + key_bytes[i % klen]) % 256
        s[i], s[j] = s[j], s[i]
    i = j = 0
    ks = []
    for _ in range(length):
        i = (i + 1) % 256
        j = (j + s[i]) % 256
        s[i], s[j] = s[j], s[i]
        t = (s[i] + s[j]) % 256
        ks.append(s[t])
    return ks


# ---------------- SM3 (douyin.js 移植) ----------------
def _rotl(x, n):
    n %= 32
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF


def _tj(j):
    return 2043430169 if 0 <= j < 16 else 2055708042


def _ff(j, x, y, z):
    if 0 <= j < 16:
        return (x ^ y ^ z) & 0xFFFFFFFF
    return (x & y | x & z | y & z) & 0xFFFFFFFF


def _gg(j, x, y, z):
    if 0 <= j < 16:
        return (x ^ y ^ z) & 0xFFFFFFFF
    return (x & y | (~x & 0xFFFFFFFF) & z) & 0xFFFFFFFF


_IV = [1937774191, 1226093241, 388252375, 3666478592,
       2842636476, 372324522, 3817729613, 2969243214]


def _str_to_bytes(e):
    """复现 write 的字符串处理: encodeURIComponent + %XX 解码为单字节。"""
    from urllib.parse import quote
    n = quote(e, safe="!()*-._~'")  # 与 JS encodeURIComponent 对齐
    # JS encodeURIComponent 不编码: A-Za-z0-9 - _ . ! ~ * ' ( )
    out = []
    i = 0
    while i < len(n):
        if n[i] == '%':
            out.append(int(n[i + 1:i + 3], 16))
            i += 3
        else:
            out.append(ord(n[i]))
            i += 1
    return out


def _sm3_compress(reg, block):
    w = [0] * 132
    for t in range(16):
        w[t] = ((block[4 * t] << 24) | (block[4 * t + 1] << 16) |
                (block[4 * t + 2] << 8) | block[4 * t + 3]) & 0xFFFFFFFF
    for n in range(16, 68):
        a = w[n - 16] ^ w[n - 9] ^ _rotl(w[n - 3], 15)
        a = a ^ _rotl(a, 15) ^ _rotl(a, 23)
        w[n] = (a ^ _rotl(w[n - 13], 7) ^ w[n - 6]) & 0xFFFFFFFF
    for n in range(64):
        w[n + 68] = (w[n] ^ w[n + 4]) & 0xFFFFFFFF
    reg2 = reg[:]
    i = reg2
    for c in range(64):
        o = (_rotl(i[0], 12) + i[4] + _rotl(_tj(c), c)) & 0xFFFFFFFF
        o = _rotl(o, 7)
        s = (o ^ _rotl(i[0], 12)) & 0xFFFFFFFF
        u = _ff(c, i[0], i[1], i[2])
        u = (u + i[3] + s + w[c + 68]) & 0xFFFFFFFF
        b = _gg(c, i[4], i[5], i[6])
        b = (b + i[7] + o + w[c]) & 0xFFFFFFFF
        i[3] = i[2]
        i[2] = _rotl(i[1], 9)
        i[1] = i[0]
        i[0] = u
        i[7] = i[6]
        i[6] = _rotl(i[5], 19)
        i[5] = i[4]
        i[4] = (b ^ _rotl(b, 9) ^ _rotl(b, 17)) & 0xFFFFFFFF
    return [(reg[k] ^ reg2[k]) & 0xFFFFFFFF for k in range(8)]


def sm3_sum_bytes(data):
    """对字节列表做一次 SM3, 返回 32 字节列表。"""
    reg = _IV[:]
    chunk = list(data)
    size = len(chunk)
    # _fill
    a = 8 * size
    chunk.append(128)
    f = len(chunk) % 64
    if 64 - f < 8:
        f -= 64
    while f < 56:
        chunk.append(0)
        f += 1
    for i in range(4):
        c = a // 4294967296
        chunk.append((c >> (8 * (3 - i))) & 255)
    for i in range(4):
        chunk.append((a >> (8 * (3 - i))) & 255)
    for off in range(0, len(chunk), 64):
        reg = _sm3_compress(reg, chunk[off:off + 64])
    out = [0] * 32
    for f in range(8):
        c = reg[f]
        out[4 * f + 3] = c & 255
        c >>= 8
        out[4 * f + 2] = c & 255
        c >>= 8
        out[4 * f + 1] = c & 255
        c >>= 8
        out[4 * f] = c & 255
    return out


def sm3_of_str(s):
    return sm3_sum_bytes(_str_to_bytes(s))


def double_sm3_str(s):
    return sm3_sum_bytes(sm3_of_str(s))


# ---------------- gener_random ----------------
def gener_random(random, option):
    r = int(random)
    return [
        (r & 255 & 170) | (option[0] & 85),
        (r & 255 & 85) | (option[0] & 170),
        ((r >> 8) & 255 & 170) | (option[1] & 85),
        ((r >> 8) & 255 & 85) | (option[1] & 170),
    ]


# ---------------- 验证: SM3 明文 -> 输出 ----------------
def verify_sm3_inputs():
    lines = []
    P = lines.append

    # algo_inputs.md 捕获的明文 (q=1 基线)
    fp = "verify_mq4z6xni_QKrmclaL_BYTO_4oJp_Bwln_A5rR68bwoaZJ"
    mstoken = ("BB8XmwHsFNvsk8ubDr65EwX9AKBCQFk1-KxwnF07pts7TE4aSmixaVff29MjhBSsHkToqHEZ"
               "goGcqLqPlGYl4C5LEMIGI9ZnJk1YsunvnMQlhC1GYMciA7aBjkJH3RFmTxrVhq_HSl6wjhRx0BNGFPJYUaTbJ96YkPjK1piQjzBUvIkBveKF2Q==")
    # 调用1明文: query + verifyFp + fp + msToken + 后缀dhzx
    inp1 = "q=1&verifyFp=" + fp + "&fp=" + fp + "&msToken=" + mstoken + "dhzx"
    # 调用2: 后缀
    inp2 = "dhzx"
    # 调用3: UA处理结果 (algo_inputs 调用3明文)
    inp3 = ("fmUmtNjj1OfTrR716RHSHkEyO55LH9cpXtzIQ2cGu4OGyLadRAIoz3CqCBP8kDqzpxV7FE0STcZAPIZ3+A7vRV1DxZB7jVkeelhZP1IOjUd3/XUomeAEsdm/4MnEo9KrgcExEO5znbahc4jEtHXD")

    # 调用1: 旧版是 sm3.sum(sm3.sum(url_search_params + suffix)) -> double_sm3
    url_list = sm3_sum_bytes(sm3_of_str(inp1))
    # 调用2: sm3.sum(sm3.sum(suffix)) ; 但 algo_inputs 调用2 明文只有 "dhzx" 一次
    #   旧版 cus = sm3.sum(sm3.sum(suffix)); 内层 sm3.sum(suffix) 先 encodeURIComponent(suffix)
    #   外层 sm3.sum(<32字节数组>) 不走 encodeURIComponent (输入是数组)
    cus_list = sm3_sum_bytes(sm3_of_str(inp2))
    # 调用3: ua = sm3.sum(result_encrypt(rc4_encrypt(ua),"s3"))  -> 单次 sm3 of inp3
    ua_list = sm3_of_str(inp3)

    P("SM3 input1 (query+dhzx) double-sm3 ->")
    P("  " + " ".join(str(x) for x in url_list))
    P("SM3 input2 (dhzx) double-sm3 ->")
    P("  " + " ".join(str(x) for x in cus_list))
    P("SM3 input3 (UA result) single-sm3 ->")
    P("  " + " ".join(str(x) for x in ua_list))
    return lines, url_list, cus_list, ua_list


if __name__ == "__main__":
    lines, url_list, cus_list, ua_list = verify_sm3_inputs()
    out = os.path.join(HERE, "abogus_new_out.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("WROTE", out)
