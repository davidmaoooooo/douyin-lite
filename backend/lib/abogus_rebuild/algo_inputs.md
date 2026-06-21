# a_bogus 算法输入情报（hook encodeURIComponent 直接捕获，突破性）

## 重大突破：SM3 输入明文直接可见
hook `window.encodeURIComponent`（SM3 的 write 函数内部调用它处理字符串），
在一次签名中捕获到**恰好 3 次**调用，对应旧版 generate_rc4_bb_str 的三次 SM3：

固定输入(q=1, Date.now=1700000000000, Math.random=0.5, perf=12345, 默认UA Chrome/149)：

### 调用1：query串 + 后缀（对应旧版 sm3.sum(sm3.sum(url_search_params + suffix))）
```
q=1&verifyFp=verify_mq4z6xni_QKrmclaL_BYTO_4oJp_Bwln_A5rR68bwoaZJ&fp=verify_mq4z6xni_QKrmclaL_BYTO_4oJp_Bwln_A5rR68bwoaZJ&msToken=BB8XmwHsFNvsk8ubDr65EwX9AKBCQFk1-KxwnF07pts7TE4aSmixaVff29MjhBSsHkToqHEZgoGcqLqPlGYl4C5LEMIGI9ZnJk1YsunvnMQlhC1GYMciA7aBjkJH3RFmTxrVhq_HSl6wjhRx0BNGFPJYUaTbJ96YkPjK1piQjzBUvIkBveKF2Q%3D%3Ddhzx
```
注意：msToken 末尾 `==` 被编码为 `%3D%3D`，后缀 `dhzx` 紧跟其后。

### 调用2：后缀单独（对应 sm3.sum(sm3.sum(suffix))）
```
dhzx
```

### 调用3：UA 处理结果（对应 sm3.sum(result_encrypt(rc4_encrypt(ua,...),"s3"))）
```
fmUmtNjj1OfTrR716RHSHkEyO55LH9cpXtzIQ2cGu4OGyLadRAIoz3CqCBP8kDqzpxV7FE0STcZAPIZ3+A7vRV1DxZB7jVkeelhZP1IOjUd3/XUomeAEsdm/4MnEo9KrgcExEO5znbahc4jEtHXD
```

## 确认的常量（变 random/time/query 验证）
- **后缀 = `dhzx`**（固定！旧版是 `cus`）—— 不随 random/time/query 变。
- UA 中间值固定（UA 不变则不变），算法 = rc4_encrypt(ua,key) 再 result_encrypt(...,"s3")，与旧版一致。
- query 串组成：`{业务query}&verifyFp={s_v_web_id}&fp={s_v_web_id}&msToken={msToken}` + 后缀 dhzx
  （注意真实签名的 query 包含了 verifyFp/fp/msToken，不只是业务参数）

## 结论：算法主干 = 旧版 douyin.js，仅改动
1. 后缀 cus → **dhzx**
2. bb 字节模板布局变化（待对齐：Arguments值、新增字段、固定常量字节 idx15=221/19=124/23=52/39=178）
3. 最终 RC4 密钥（旧版 key=[121]，新版待定）
4. random_head 的 gener_random option 常量变化（[3,82],[117,34],[184,169]...）

## 下一步（用已知SM3输入→预期SM3输出对齐bb）
- 用旧 douyin.js 的 SM3 对上述3个明文求 sum，得到 url_search_params_list/cus/ua 三个32字节数组。
- 这些数组的特定字节注入 bb（旧版 b[38,39]=url列[21,22], b[40,41]=cus[21,22], b[42,43]=ua[23,24]）。
- 新版注入位置已知（query影响明文idx 24,27,28,31,32,35）→ 反查是哪几个SM3字节。
