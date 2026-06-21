# -*- coding: utf-8 -*-
"""抓取最新版 192 长度 a_bogus 对应的 bb 结构"""
import json
import time
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from lib.reverse.cdp2 import CDP, get_ws


def ev(cdp, expr, timeout=30):
    r = cdp.cmd("Runtime.evaluate",
                {"expression": expr, "returnByValue": True},
                timeout=timeout)
    return r.get("result", {}).get("result", {}).get("value")


SETUP = """(function(){
if(window.__bb_hook)return;
window.__bbcaps=[];
var o=String.fromCharCode;
String.fromCharCode=function(){
  try{
    if(arguments.length>=128)
      window.__bbcaps.push(Array.prototype.slice.call(arguments));
  }catch(e){}
  return o.apply(String,arguments);
};
window.__bb_hook=1;
})()"""


def grab_current():
    """抓取当前版本的 bb"""
    cdp = CDP(get_ws())
    cdp.cmd("Runtime.enable")
    ev(cdp, SETUP)

    print("抓取当前版本 bb（触发真实请求）...\n")

    # 用固定参数触发
    T = 1700000000000
    js = f"""(function(){{
Date.now=()=>{T};
Math.random=()=>0.5;
var x=new XMLHttpRequest();
x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=1',true);
x.onreadystatechange=function(){{
  if((x.responseURL||'').indexOf('a_bogus=')!==-1){{
    try{{x.abort();}}catch(e){{}}
  }}
}};
x.send(null);
}})()"""

    ev(cdp, js)
    time.sleep(0.8)

    caps = json.loads(ev(cdp, "JSON.stringify(window.__bbcaps)") or "[]")
    cdp.close()

    if not caps:
        print("未抓到 bb")
        return

    bb = caps[-1]  # 最后一个
    print(f"抓到 bb: len={len(bb)}")
    print(f"前 20 字节: {bb[:20]}")
    print(f"后 20 字节: {bb[-20:]}")

    # s4 编码后长度
    s4_len = len(bb) * 4 // 3 + 4
    print(f"\ns4 编码后预计长度: ~{s4_len}")

    # 保存
    out = {
        "timestamp": T,
        "query": "aweme_id=1",
        "bb": bb,
        "bb_len": len(bb),
        "note": "2026-06 最新版本"
    }
    json.dump(out, open(ROOT / "lib" / "reverse" / "bb_current_v192.json", "w"), indent=2)
    print(f"\n已保存: lib/reverse/bb_current_v192.json")


if __name__ == "__main__":
    grab_current()
