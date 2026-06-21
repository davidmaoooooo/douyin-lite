# -*- coding: utf-8 -*-
"""用 CDP Debugger 在 VM 原生调用点(var m=n.apply(d,e) @131927)下条件断点。
条件: e.length 在 120-200 之间(处理 bb/fin 这类长数组时)。
命中时读 n(函数源码前缀)、e(参数)、this，记录 VM 对长数据做了什么原生调用。
"""
import json
import urllib.request
import websocket
import time


def get_ws():
    d = json.load(urllib.request.urlopen("http://localhost:9222/json/list"))
    for t in d:
        if t.get("type") == "page" and "douyin" in t.get("url", ""):
            return t["webSocketDebuggerUrl"]
    return None


class CDP:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, max_size=None, timeout=30)
        self._id = 0
        self.events = []

    def cmd(self, method, params=None, wait=True):
        self._id += 1
        mid = self._id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        if not wait:
            return None
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                return msg
            else:
                self.events.append(msg)  # 缓存事件(如 Debugger.scriptParsed/paused)

    def recv_event(self, method_filter, timeout=20):
        """等一个特定事件"""
        # 先查缓存
        for i, e in enumerate(self.events):
            if e.get("method") == method_filter:
                return self.events.pop(i)
        end = time.time() + timeout
        while time.time() < end:
            try:
                msg = json.loads(self.ws.recv())
            except Exception:
                break
            if msg.get("method") == method_filter:
                return msg
            self.events.append(msg)
        return None

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


BDMS_URL_SUBSTR = "bdms_1.0.1.19_fix.js"

if __name__ == "__main__":
    cdp = CDP(get_ws())
    cdp.cmd("Debugger.enable")
    cdp.cmd("Runtime.enable")
    # 找到 bdms 脚本的 scriptId
    # 触发 scriptParsed 已在 enable 时涌出，查缓存
    time.sleep(1)
    # 主动收集 scriptParsed
    script_id = None
    # 读已缓存事件
    for e in list(cdp.events):
        if e.get("method") == "Debugger.scriptParsed":
            url = e["params"].get("url", "")
            if BDMS_URL_SUBSTR in url:
                script_id = e["params"]["scriptId"]
    # 若没有，再等一会
    if not script_id:
        for _ in range(50):
            ev = cdp.recv_event("Debugger.scriptParsed", timeout=2)
            if ev and BDMS_URL_SUBSTR in ev["params"].get("url", ""):
                script_id = ev["params"]["scriptId"]
                break
    print("bdms scriptId:", script_id)
    if not script_id:
        print("未找到 bdms 脚本，可能需要刷新页面")
        cdp.close()
        raise SystemExit

    # 在偏移 131927 下条件断点：只在 e 是长数组时暂停
    bp = cdp.cmd("Debugger.setBreakpoint", {
        "location": {"scriptId": script_id, "lineNumber": 0, "columnNumber": 131927},
        "condition": "typeof e!=='undefined' && e && e.length>=120 && e.length<=200"
    })
    print("setBreakpoint:", json.dumps(bp.get("result", bp), ensure_ascii=False)[:200])
    cdp.close()
    print("\n断点已设。下一步：触发签名并在 Debugger.paused 时读 n/e。")
