# a_bogus 新版（184长度）逆向工作笔记

## 已确认事实（实测，2026-06）

### 1. 根因
- 旧纯算法 `lib/douyin.js`（~160长度）已被服务端拒绝：`403 Blocked by ArgusSecurityPlugin Sign Invalid`。
- 抖音线上新版 a_bogus **长度 184**。

### 2. a_bogus 是确定性函数（关键！）—— 已修正
**必须同时冻结 3 个计时/随机源**，否则结果不稳定：
- `Date.now` 和 `new Date()`
- `Math.random`
- **`performance.now`** ← 最初遗漏，导致早期样本被污染！

冻结全部 3 个后，同输入连续 5 次产出**完全相同**的 a_bogus（已验证 allSame=true）。
→ 完整签名函数：`f(query, UA, Date.now, Math.random, performance.now, env) → a_bogus`

**作废**：早期未冻结 performance.now 的 query_dim / time_dim / method_dim 样本不可用于逐字节差分。
需用三源全冻结的采集器重新采集。

确定基线(q=1, Date.now=1700000000000, random=0.5, performance.now=12345)：
`O7UfhzU7dNmfCdMbuKiQH33UGHnMrPSyNBTobbeTSxu-K1eaZSE2uOa2Jxo/kSxRsRM0hM-HzDGMbfVbzTUkpK9pKmpDuOhWB42n96XL0qwvTtsMLqSEew0FwwsCM8GTmcB4xH6vIUkEXElAwq9DWMK9HCeN-Cm0BrNVpAjycDcWpBgTVx/uSUf=`

### 3. 生成机制
- a_bogus **不是**可独立调用的纯函数；`byted_acrawler.frontierSign` 只产旧的 `X-Bogus`。
- 真正的 a_bogus 由 SDK 重写的 `XMLHttpRequest.prototype.send` 在内部注入
  （`secureOpenArgs`/`hookConfig`/`needProxy`）。
- JSVMP 解释器入口：`window._$webrt_1668687510`。

### 4. 采集器（在 douyin.com 真实页面 evaluate 执行）
冻结时间/随机数后，用 SDK 重写的 XHR 发请求，从 `xhr.responseURL` 提取 a_bogus。
拿到 responseURL 即可 abort，不必等响应完成。

### 5. 结构判断（与旧 douyin.js 框架吻合）
旧结构：`result_encrypt(generate_random_str() + generate_rc4_bb_str(...), "s4") + "="`
新版 184 长度样本对齐（FIXED_TIME=1700000000000, random=0.5）：

```
位置          0--------------------------------31 32----------44 ...固定中段...      末尾
base:    O7UfhzU7dNmfCdMbuKiQH33UGHnMrPSy | rPToWcMTSNYlK1tO | ZSE2...TVx/uS | 5y=
q_a:     O7UfhzU7dNmfCdMbuKiQH33UGHnMrPSy | jPToRYqTSxYJK1teP| ...           | V6=
q_b:     (前32同) | rBToRC1TSNu4K1tcP | ...
q_empty: (前32同) | iPToWuHTSPzUK1teP | ...
q_len50: (前32同) | xPToRcqTSPzlK1tea | ...
```

- **前32字符固定** = generate_random_str()（random冻结所致）。
- **中段约12字符随query变** = query+method 双SM3注入的字节（对应旧 b[38],b[39]等）。
- **大段中部固定** = UA+env+固定配置（aid/pageId等），UA/env未变所以固定。
- **末尾2字符随query变** = 校验字节 b[72] 区。

→ 大框架（随机头 + bb串 + s4编码 + "="尾）很可能未变，需定位的变化点：
  编码表是否变 / 字节模板 b[] 布局 / 新增字段 / 版本号 [1,0,1,5] / Arguments。

## 基线样本（FIXED_TIME=1700000000000, Math.random=0.5, 默认UA）
base(?q=1):   O7UfhzU7dNmfCdMbuKiQH33UGHnMrPSyrPToWcMTSNYlK1tOZSE2uOa2Jxo/kSxRsRB0hF-HzDGMbfVbzTUkpK9pKmpDuOhWB42n96XL0qwvTtsMLqSEew0FwwsCM8GTmcB4xH6vIUkEXElAwq9DWMK9HCeN-Cm0BrNVpAjycDcWpBgTVx/uS5y=
q=a:          O7UfhzU7dNmfCdMbuKiQH33UGHnMrPSyjPToRYqTSxYJK1tePZSE2uOa2Jxo/kSxRsRB0hF-HzDGMbfVbzTUkpK9pKmpDuOhWB42n96XL0qwvTtsMLqSEew0FwwsCM8GTmcB4xH6vIUkEXElAwq9DWMK9HCeN-Cm0BrNVpAjycDcWpBgTVx/uSV6=

## 待办
- [ ] 大批量结构化差分采样（query/UA/time/random 各维度）
- [ ] s4 表 base64 解码 184 字符 → 字节序列，对齐旧 bb 模板
- [ ] 逐字节反推来源公式
- [ ] Python 复现 + 逐字节验证
