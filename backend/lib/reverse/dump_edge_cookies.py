# -*- coding: utf-8 -*-
"""导出当前 Edge 调试会话的全部 cookie，与 websign_env.json 的密钥同源，用于端到端验证。"""
import json, sys
sys.path.insert(0, 'lib/abogus_rebuild')
from cdp2 import CDP, get_ws

cdp = CDP(get_ws())
cdp.cmd("Network.enable")
r = cdp.cmd("Network.getAllCookies", {})
cookies = r.get("result", {}).get("cookies", [])
jar = {}
for c in cookies:
    if 'douyin' in c.get('domain', '') or c.get('domain', '').endswith('.douyin.com'):
        jar[c['name']] = c['value']
json.dump(jar, open("lib/abogus_rebuild/edge_session_cookies.json", "w"), ensure_ascii=False, indent=2)
print("saved", len(jar), "cookies")
print("has sessionid:", 'sessionid' in jar, "| ttwid:", 'ttwid' in jar, "| UIFID:", 'UIFID' in jar)
cdp.close()
