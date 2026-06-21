# a_bogus 进展 (CDP断点+端到端验证)

## 已验证可用方案: Edge CDP 签名
- `utils/edge_signer.py`: sign_via_edge(full_url) -> a_bogus
- 已接入 `utils/request.py` 的 get_sign_edge(), POST接口(点赞/favorite等)已切此方案
- **端到端验证**: detail接口 CDP签名 + httpx -> HTTP 200 + 真实数据 (e2e_test.py)
- tab/feed: 签名被接受(错误从"Sign Invalid"变"Validate Error", 后者是接口级校验非签名问题)
- 要求: Edge 用 `msedge --remote-debugging-port=9222 --remote-allow-origins=*` 启动并开 douyin.com

## 纯Python逆向状态 (95%)
- s4编码层: 完全掌握 (decode(a_bogus)==fin 已验证)
- SM3: 移植正确
- 后缀 cus->dhzx, 三次SM3明文输入已抓, UA/env处理已知
- 全套配对数据: lib/abogus_rebuild/fullset.json (输入->bb->fin)
- **唯一缺口**: bb(132)->fin(136) 变换, 纯在JSVMP字节码内
  - 非标准RC4(穷举全失败), 不调原生函数(断点400次全短数组)
  - s4表/移位运算都在字节码里(源码无 Dkdpgh/>>18)
  - 需逐条翻译VM opcode (数天工程)

## 工具链
- cdp.py / cdp2.py: CDP客户端(后者多线程更稳)
- 僵尸连接问题: Debugger用完必须disable+close, 否则占用page需重启Edge
