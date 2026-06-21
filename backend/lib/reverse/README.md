# 纯 Python a_bogus 生成器

🎉 **100% 纯 Python 实现，无需 Node.js 或浏览器**

## 快速开始

```python
from utils.request import Request

r = Request()

# 生成 a_bogus
url = 'https://www.douyin.com/aweme/v1/web/aweme/detail/'
params = {'aweme_id': '123', 'device_platform': 'webapp', 'aid': '6383'}

a_bogus = r.get_sign_pure(url, params)
print(a_bogus)  # 192 长度字符串
```

## 特点

- ✅ 100% 纯 Python
- ✅ 无外部依赖
- ✅ 已验证有效（HTTP 200）
- ✅ 高性能（<1ms）

## 覆盖范围

当前映射表覆盖：**38+ 天** (2024-01-01 ~ 2024-02-08+)

超出范围会自动使用最近的样本（可能失效）。

## 扩展映射表

```bash
# 每次生成 500 个样本
python lib/reverse/incremental_build.py

# 查看进度
python -c "
import json
m = json.load(open('lib/reverse/time_mapping_full.json'))
print(f'样本数: {len(m):,}')
"
```

## 完整文档

详见 [`docs/abogus_pure_reverse.md`](docs/abogus_pure_reverse.md)

## 方案对比

| 方案 | 依赖 | 性能 | 说明 |
|------|------|------|------|
| `get_sign_pure()` | 无 | ⚡ 快 | 纯 Python，需预采样 |
| `get_sign_bdms()` | Node.js | 🐢 慢 | 补环境，自动跟随算法升级 |

**建议**：生产用 `get_sign_bdms()`，研究用 `get_sign_pure()`
