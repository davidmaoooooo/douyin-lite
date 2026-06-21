# bb(132) -> fin(136) 攻坚记录

> 本次会话状态：**环境拒绝任何 Python/代码执行**（`.venv/Scripts/python.exe`、`python`、`python3`、`py`
> 全部 Bash 权限被拒；只读 Bash 如 `ls`/`grep` 可用）。因此 **无法运行 cdp.py 连 Edge**，
> 无法 dump VM、无法下断点、无法采标准答案、无法对任何 bb->fin 变换做数值验证。
> 以下仅为 **静态/手算** 推断，凡未经执行验证者一律标注【未验证】，不得当作定论。

## 一、确定的结构（读 douyin.js 旧版 + bb_fin2.json 字节，手算可核）

旧版 `sign()` 结构（lib/douyin.js:413-426）：
```
result_str = generate_random_str()           // 12 字节 = 3×gener_random
           + generate_rc4_bb_str(...)         // = rc4_encrypt(bb_string, key=[121])
a_bogus = result_encrypt(result_str, "s4") + "="
```
即旧版 fin(s4解码值) = random_head(12) ++ RC4(bb, [121])，且 RC4 保长 → fin_len = 12 + len(bb)。

## 二、新版关键差异（与"fin = head + RC4(bb)"假设矛盾）【部分手算可核】

新版 bb_fin2.json：bb_len=132, fin_len=136，**仅差 4 字节**（旧版差 12）。

1. **fin[0] == bb[0] == 171**，fin[1]=87 vs bb[1]=85（差 2）。
   - 若 fin = 独立 4 字节 random_head ++ RC4(bb)，则 fin[0] 应是与 bb 无关的随机头字节，
     不应恒等于 bb[0]=171。→ **该假设基本被否**。
2. 对 fin[0:4]=[171,87,80,22] 反解单次 `gener_random(5000,opt)`（Math.random=0.5→r=5000）：
   - gener_random(5000,opt) = [136|(opt0&85), 0|(opt0&170), 18|(opt1&85), 17|(opt1&170)]
   - 解 byte1=87 要求 opt0&170 含 bit{6,4,2,0}，但 &170 只能落在 bit{7,5,3,1} → **无解**。
   - → fin 头 4 字节 **不是** 干净的 gener_random 输出。
3. 结论倾向（与历史 VERDICT.md 一致）：**random_head 也进入了被加密的明文**，
   整个 fin 是对 (head ++ bb 或其重排) 的整体变换，呈雪崩特征，而非"明文头 + 密文体"。

## 三、与历史 intermediates.json 的一致性【手算可核】

- bb_plain_133 与 bb_fin2.bb：共享前缀 `171,85,42,85,41,81,170,85,144` 后在 idx9 分叉
  （时间/随机区，符合不同采集条件）。
- final_plain_137 与 bb_fin2.fin：共享前缀 `171,87,80,22,215,117,10,50,16,248,35,248,178`
  后在 idx13 分叉。两对都差 4，结构自洽。

## 四、bdms 源文件静态线索

- `lib/abogus_rebuild/bdms_1.0.1.19_fix.js` 第 2 行含 SM3 IV 字面量 `1937774191` `1226093241`
  （明文常量，非 JSVMP 编码）。
- s4 表字符串 `Dkdpgh2ZmsQB80...`、`charCodeAt/fromCharCode`、`0.00390625` 均 **不以字面量出现**
  → 在 VM 运行时构造，必须动态 dump（需 CDP）。

## 五、阻塞与所需

**核心卡点未解**：bb(132)->fin(136) 的精确变换仍未确定，且本会话无法推进——
因为它需要 (a) CDP 连 Edge dump VM 原生调用序列 / 下断点读局部变量，或
(b) 运行 Python 对真实 bb/fin 暴力验证各种 RC4/重排/双重加密假设。
**两者都依赖代码执行，本会话全被拒。**

**解除阻塞所需**：放行 `.venv/Scripts/python.exe` 的 Bash 执行权限（至少允许运行
`lib/abogus_rebuild/cdp.py`、`ops.py` 及临时验证脚本）。届时按原任务"攻坚手段 1-4"推进。
