# -*- coding: utf-8 -*-
"""
a_bogus 新版（184长度）密码学分析工具。

核心结构假设（与旧 douyin.js 框架对齐）：
    a_bogus = s4_encode( random_str(前N明文字节) + rc4(bb串, key=?) ) + "="

关键点：
- s4 编码表与旧版一致（已确认）。
- 编码前是一段字节流。前段对应 generate_random_str()（random冻结则固定）。
- 其余字节是 rc4(明文模板, 未知key) 的密文。
- RC4 是流密码：cipher[i] = keystream[i] ^ plain[i]。
  两个样本若 key 相同（同一次签名内 RC4 状态确定），且明文只在某些位置不同，
  则在【相同位置】 cipher_A[i] ^ cipher_B[i] = plain_A[i] ^ plain_B[i]。
  注意：不同样本是不同的 RC4 调用，keystream 相同当且仅当 key 相同。
  抖音 RC4 key 是常量（不随输入变），所以所有样本 keystream 一致 => 可做差分。

所有输出写文件，避免 Windows 控制台中文乱码。
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
S4 = "Dkdpgh2ZmsQB80/MfvV36XI1R45-WUAlEixNLwoqYTOPuzKFjJnry79HbGcaStCe"
IDX = {c: i for i, c in enumerate(S4)}


def s4_decode(enc):
    """s4 base64 变体解码为字节列表。"""
    enc = enc.rstrip("=")
    out = []
    for i in range(0, len(enc), 4):
        chunk = enc[i:i + 4]
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


def rc4_keystream(key_bytes, length):
    """生成 RC4 keystream（与 douyin.js rc4_encrypt 的取流方式一致）。"""
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


def rc4(data_bytes, key_bytes):
    ks = rc4_keystream(key_bytes, len(data_bytes))
    return [data_bytes[i] ^ ks[i] for i in range(len(data_bytes))]


def diff_positions(a, b):
    """返回两个字节序列不同的位置索引（含越界差异）。"""
    out = []
    n = max(len(a), len(b))
    for i in range(n):
        va = a[i] if i < len(a) else None
        vb = b[i] if i < len(b) else None
        if va != vb:
            out.append(i)
    return out


def hexrow(b):
    return " ".join(f"{x:3d}" for x in b)


def load_samples():
    return json.load(open(os.path.join(HERE, "samples_clean.json"), encoding="utf-8"))


# ---- 旧版 generate_random_str 复现（用于已知明文攻击 random 头） ----
def gener_random(random, option):
    r = int(random)
    return [
        (r & 255 & 170) | (option[0] & 85),
        (r & 255 & 85) | (option[0] & 170),
        ((r >> 8) & 255 & 170) | (option[1] & 85),
        ((r >> 8) & 255 & 85) | (option[1] & 170),
    ]


def generate_random_str_old(math_random):
    """旧版：Math.random()*10000 三次，option=[3,45],[1,0],[1,5]。"""
    rlist = []
    rv = int(math_random * 10000)
    rlist += gener_random(rv, [3, 45])
    rlist += gener_random(rv, [1, 0])
    rlist += gener_random(rv, [1, 5])
    return rlist


if __name__ == "__main__":
    samples = load_samples()
    lines = []
    P = lines.append

    # 解码全部样本
    decoded = {}
    for dim in ("query_dim", "time_dim", "random_dim"):
        decoded[dim] = {}
        for k, v in samples[dim].items():
            decoded[dim][k] = s4_decode(v)

    P("=" * 70)
    P("1. 解码长度统计")
    P("=" * 70)
    for dim in decoded:
        for k, b in decoded[dim].items():
            P(f"  {dim:12s} {k:10s} enc_len={len(samples[dim][k]):3d} bytes={len(b)}")

    # ---- query_dim 差分：q=1 作基线 ----
    P("")
    P("=" * 70)
    P("2. query_dim 差分 (基线 q=1, RC4 keystream 对所有样本相同 => cipher 差=明文差)")
    P("=" * 70)
    qbase = decoded["query_dim"]["q=1"]
    P(f"  q=1 bytes ({len(qbase)}):")
    P("    " + hexrow(qbase))
    for k, b in decoded["query_dim"].items():
        if k == "q=1":
            continue
        dp = diff_positions(qbase, b)
        P(f"  q=1 vs {k:10s} diff_positions={dp}")
        for i in dp:
            va = qbase[i] if i < len(qbase) else None
            vb = b[i] if i < len(b) else None
            xv = (va ^ vb) if (va is not None and vb is not None) else None
            P(f"      idx {i:3d}: {va} ^ {vb} = {xv}")

    # ---- time_dim 差分 ----
    P("")
    P("=" * 70)
    P("3. time_dim 差分 (基线 +0)")
    P("=" * 70)
    tbase = decoded["time_dim"]["+0"]
    for k, b in decoded["time_dim"].items():
        if k == "+0":
            continue
        dp = diff_positions(tbase, b)
        P(f"  +0 vs {k:10s} diff_positions={dp}")
        for i in dp:
            va = tbase[i] if i < len(tbase) else None
            vb = b[i] if i < len(b) else None
            xv = (va ^ vb) if (va is not None and vb is not None) else None
            P(f"      idx {i:3d}: {va} ^ {vb} = {xv}")

    # ---- random_dim 差分 ----
    P("")
    P("=" * 70)
    P("4. random_dim 差分 (基线 0.5) - 预期整段雪崩")
    P("=" * 70)
    rbase = decoded["random_dim"]["0.5"]
    for k, b in decoded["random_dim"].items():
        if k == "0.5":
            continue
        dp = diff_positions(rbase, b)
        P(f"  0.5 vs {k:10s} diff count={len(dp)} / {max(len(rbase),len(b))}  first10={dp[:10]}")

    # ---- 已知明文攻击尝试：random 头是否为旧 generate_random_str ----
    P("")
    P("=" * 70)
    P("5. 已知明文攻击：前段 random 字节 vs 旧 generate_random_str(0.5)")
    P("=" * 70)
    rnd_plain_old = generate_random_str_old(0.5)
    P(f"  旧 generate_random_str(0.5) 明文 = {rnd_plain_old}")
    P(f"  解码后前16字节(0.5样本)        = {rbase[:16]}")
    P("  注意：若前段是明文(未RC4)，应直接等于上面旧明文；")
    P("        若前段也进了RC4，则 cipher[i]^plain[i]=keystream[i]。")
    # 若前12字节是明文random，则它们应在不同random样本间变化、但在query/time维固定
    P("")
    P("  各维度前16字节是否固定（判断 random 头边界）：")
    for dim in ("query_dim", "time_dim", "random_dim"):
        P(f"    --- {dim} ---")
        keys = list(decoded[dim].keys())
        ref = decoded[dim][keys[0]][:16]
        allsame = all(decoded[dim][k][:16] == ref for k in keys)
        P(f"      前16字节全维度相同? {allsame}")
        if dim == "random_dim":
            for k in keys:
                P(f"        {k:6s}: {decoded[dim][k][:16]}")

    out_path = os.path.join(HERE, "crypto_out.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("WROTE", out_path, len(lines), "lines")
