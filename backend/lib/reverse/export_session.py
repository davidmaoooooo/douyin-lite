# -*- coding: utf-8 -*-
"""
一键导出抖音会话签名材料（保证同源）。

从同一个浏览器调试会话同时导出：
  1. secsdk 会话密钥 + localStorage  -> lib/abogus_rebuild/websign_env.json   (webSign 补环境用)
  2. 全部 cookie（含 HttpOnly 的 sessionid 等，用 Network.getAllCookies） -> config/cookie.json  (请求用)

两者来自同一会话 => x-secsdk-web-signature 与 cookie 同源，服务器才会放行。

前置条件：用调试端口启动 Edge/Chrome 并登录抖音：
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" ^
     --remote-debugging-port=9222 --remote-allow-origins=* ^
     --user-data-dir="%USERPROFILE%/edge-debug-douyin" ^
     "https://www.douyin.com/?recommend=1"

用法：
  python lib/abogus_rebuild/export_session.py
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'lib', 'abogus_rebuild'))
from cdp2 import CDP, get_ws  # noqa: E402

WEBSIGN_ENV = os.path.join(ROOT, 'lib', 'abogus_rebuild', 'websign_env.json')
CONFIG_COOKIE = os.path.join(ROOT, 'config', 'cookie.json')


def ev(cdp, expr, timeout=30):
    r = cdp.cmd("Runtime.evaluate",
                {"expression": expr, "returnByValue": True, "awaitPromise": True},
                timeout=timeout)
    res = r.get("result", {})
    if "exceptionDetails" in res:
        return "EXC: " + json.dumps(res["exceptionDetails"])[:400]
    return res.get("result", {}).get("value")


def main():
    ws = get_ws()
    if not ws:
        print("❌ 未找到 douyin 页面。请先用 --remote-debugging-port=9222 启动浏览器并打开抖音。")
        sys.exit(1)
    cdp = CDP(ws)
    cdp.cmd("Runtime.enable")
    cdp.cmd("Network.enable")

    # ---- 1. localStorage + secsdk 密钥（webSign 补环境用）----
    dump = r"""(function(){
      var ls = {};
      for (var i=0;i<localStorage.length;i++){ var k=localStorage.key(i); ls[k]=localStorage.getItem(k); }
      return JSON.stringify({
        localStorage: ls,
        cookie: document.cookie,
        href: location.href,
        ua: navigator.userAgent,
        ssr_user_id: (window.SSR_RENDER_DATA && window.SSR_RENDER_DATA.app && window.SSR_RENDER_DATA.app.odin) ? window.SSR_RENDER_DATA.app.odin.user_id : null
      });
    })()"""
    data = ev(cdp, dump)
    if not (isinstance(data, str) and data.startswith("{")):
        print("❌ 导出 localStorage 失败:", data)
        cdp.close()
        sys.exit(1)
    env = json.loads(data)

    crypt = env["localStorage"].get("security-sdk/s_sdk_crypt_sdk")
    uid = env["localStorage"].get("web_runtime_security_uid")
    if not crypt or not uid:
        print("❌ 缺少 secsdk 密钥（security-sdk/s_sdk_crypt_sdk / web_runtime_security_uid）。")
        print("   说明页面 secsdk 尚未初始化完成，请等页面完全加载后重试。")
        cdp.close()
        sys.exit(1)

    # ---- 2. 全部 cookie（含 HttpOnly，用 CDP）----
    r = cdp.cmd("Network.getAllCookies", {})
    all_cookies = r.get("result", {}).get("cookies", [])
    jar = {}
    for c in all_cookies:
        dom = c.get("domain", "")
        if "douyin" in dom or dom.endswith(".douyin.com"):
            jar[c["name"]] = c["value"]

    # 用 CDP 拿到的 HttpOnly cookie 覆盖/补全 env.cookie（document.cookie 拿不到 HttpOnly）
    cdp.close()

    # ---- 3. 同源校验 ----
    secsdk_uid_cookie = jar.get("x-web-secsdk-uid", "")
    same = (secsdk_uid_cookie == uid)

    # ---- 4. 写文件 ----
    # websign_env.json：用 CDP 全量 cookie 字符串（含 HttpOnly），保证补环境 document.cookie 完整
    env["cookie"] = "; ".join(f"{k}={v}" for k, v in jar.items())
    json.dump(env, open(WEBSIGN_ENV, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(jar, open(CONFIG_COOKIE, "w", encoding="utf-8"), ensure_ascii=False)

    print("✅ 导出完成（同一会话，已同源）：")
    print(f"   - {os.path.relpath(WEBSIGN_ENV, ROOT)}  (secsdk 密钥 + localStorage)")
    print(f"   - {os.path.relpath(CONFIG_COOKIE, ROOT)}  ({len(jar)} 个 cookie，含 HttpOnly)")
    print(f"   web_runtime_security_uid: {uid}")
    print(f"   登录态: sessionid={'有' if 'sessionid' in jar else '无（匿名）'}  "
          f"UIFID={'有' if 'UIFID' in jar else '无'}")
    print(f"   secsdk 同源: {'✅ 一致' if same else '⚠️ x-web-secsdk-uid 与 localStorage uid 不一致'}")
    if not same and secsdk_uid_cookie:
        print(f"     cookie x-web-secsdk-uid={secsdk_uid_cookie} vs localStorage uid={uid}")


if __name__ == "__main__":
    main()
