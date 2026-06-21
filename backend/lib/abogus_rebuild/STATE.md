# a_bogus 逆向 - 当前完整状态（CDP+源文件突破后）

## 工具链（全部就绪）
- **CDP 实时访问**：`lib/abogus_rebuild/cdp.py`（连 Edge 9222，需 --remote-allow-origins=*）
  - Edge 启动：`cmd.exe /c 'start "" msedge.exe --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=C:\edge-debug https://www.douyin.com'`
- **真实源文件**：`lib/abogus_rebuild/bdms_1.0.1.19_fix.js`（147KB，版本1.0.1.19，单行混淆）
  - 算法是 JSVMP 字节码；解释器函数 X@偏移131083，opcode处理 d@131912
- **移植算法**：`lib/abogus_rebuild/abogus_new.py`（SM3/RC4/s4/gener_random，已验证SM3正确）
- **采集脚本**：trace.py / stacks.py / bbfin.py

## 已验证正确
1. **SM3 移植正确**：double_sm3('dhzx')=[64,253,156,240,44,96,159,150,...] 与浏览器一致。
2. s4 编码表沿用旧版。
3. 后缀 cus→**dhzx**。
4. method/body/perf 不影响。

## 算法链路（charCodeAt时序 + 调用栈，全部来自 bdms VM 函数 d）
- UA明文 → RC4 → UA密文(同长)
- window_env串(如 '1028|909|...')
- **bb明文(132字节)**: 171,85,42,85,41,81,170,85,144,64,118,9,246,64,36,1,144,64,37,0...
- **fin明文(136字节, =s4解码值)**: 171,87,80,22,215,117,10,50,16,248,35,248,178,224,8,217...
- SM3 hex输出(32)

## 唯一卡点：bb(132) → fin(136) 的变换
- 差4字节，**非简单RC4**（穷举 key[0,1,8]/[0,1,14]/[121]等 × offset 0-5 × 正反向 全部未命中）。
- bb 和 fin 内容完全不同，但都以171开头。
- 推测：fin = 某变换(random_head + bb) 或 bb是中间态、fin是另一阶段。
- **需 JSVMP 字节码级分析**：在 charCodeAt(bb) 后单步 VM，看 bb 如何变 fin。

## bb/fin 完整数据
见 lib/abogus_rebuild/bb_fin.json（bb_len=132, fin_len=136 的完整字节）

## 下一步建议
1. 用 CDP `Debugger.pause` + 在 bdms js 的 d/X 函数下断点，dump bb→fin 之间的 VM opcode 序列。
2. 或：穷举更复杂的 bb→fin 变换（result_encrypt变体、双重RC4、字节重排）。
3. 关键洞察待验证：fin 是否可由 random_head + 已知SM3字节 + env 直接拼出，**不经过bb**？
