# -*- coding: utf-8 -*-
"""导出 webSignUrl 依赖的全部 localStorage 密钥 + cookie，供 Node 补环境免握手使用。"""
import json, sys
sys.path.insert(0, 'lib/abogus_rebuild')
from cdp2 import CDP, get_ws

def ev(cdp, expr, timeout=30):
    r = cdp.cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True}, timeout=timeout)
    res = r.get("result", {})
    if "exceptionDetails" in res:
        return "EXC: " + json.dumps(res["exceptionDetails"])[:300]
    return res.get("result", {}).get("value")

cdp = CDP(get_ws())
cdp.cmd("Runtime.enable")

dump = r"""(function(){
  var ls = {};
  for (var i=0;i<localStorage.length;i++){ var k=localStorage.key(i); ls[k]=localStorage.getItem(k); }
  var out = {
    localStorage: ls,
    cookie: document.cookie,
    href: location.href,
    ua: navigator.userAgent,
    ssr_user_id: (window.SSR_RENDER_DATA && window.SSR_RENDER_DATA.app && window.SSR_RENDER_DATA.app.odin) ? window.SSR_RENDER_DATA.app.odin.user_id : null,
    web_secsdk_uid: localStorage.getItem('web_runtime_security_uid')
  };
  return JSON.stringify(out);
})()"""
data = ev(cdp, dump)
if isinstance(data, str) and data.startswith("{"):
    obj = json.loads(data)
    json.dump(obj, open("lib/abogus_rebuild/websign_env.json", "w"), ensure_ascii=False, indent=2)
    print("saved websign_env.json")
    print("localStorage keys:", list(obj["localStorage"].keys()))
    print("href:", obj["href"])
    print("ua:", obj["ua"][:60])
    # 打印关键密钥的长度/前缀
    for k in obj["localStorage"]:
        if any(x in k.lower() for x in ["crypt","cert","sign","uid","secsdk","runtime"]):
            v = obj["localStorage"][k]
            print(f"  {k}: len={len(v)} | {v[:50]}")
else:
    print("DUMP FAIL:", data)
cdp.close()
