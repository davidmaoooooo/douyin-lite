# -*- coding: utf-8 -*-
"""采集完整的 140 字节 bb 样本（新版本）"""
import json
import time
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
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
    if(arguments.length>=135)
      window.__bbcaps.push(Array.prototype.slice.call(arguments));
  }catch(e){}
  return o.apply(String,arguments);
};
window.__bb_hook=1;
})()"""


def grab_bb(cdp, T, query):
    ev(cdp, "window.__bbcaps=[];")
    js = f"""(function(){{
Date.now=()=>{T};
Math.random=()=>0.5;
var x=new XMLHttpRequest();
x.open('GET','https://www.douyin.com/aweme/v1/web/aweme/detail/?{query}',true);
x.onreadystatechange=function(){{
  if((x.responseURL||'').indexOf('a_bogus=')!==-1){{
    try{{x.abort();}}catch(e){{}}
  }}
}};
x.send(null);
}})()"""
    ev(cdp, js)
    time.sleep(1.2)
    caps = json.loads(ev(cdp, "JSON.stringify(window.__bbcaps)") or "[]")
    for c in caps:
        if len(c) == 140:  # 只要 140 字节的
            return c
    return None


def sample_140():
    """采集 140 字节样本"""
    print("=== 采集 140 字节 bb 样本 ===\n")

    cdp = CDP(get_ws())
    cdp.cmd("Runtime.enable")
    ev(cdp, SETUP)

    samples = []
    base_T = 1700000000000

    # 时间变化样本（20个）
    print("采集时间变化样本...")
    for i in range(20):
        T = base_T + i * 1000
        bb = grab_bb(cdp, T, "aweme_id=1")
        if bb:
            samples.append({"T": T, "query": "aweme_id=1", "bb": bb})
            print(f"  [{len(samples)}/20] T={T}")

    cdp.close()

    # 保存
    out_file = ROOT / "lib" / "reverse" / "samples_140byte.json"
    json.dump(samples, open(out_file, "w"), indent=2)
    print(f"\n采集: {len(samples)} 条 140 字节样本")
    print(f"已保存: {out_file.relative_to(ROOT)}")


if __name__ == "__main__":
    sample_140()
