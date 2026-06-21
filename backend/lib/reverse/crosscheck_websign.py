# -*- coding: utf-8 -*-
"""交叉验证：用同一个 timestamp，对比 Node 补环境 与 实时浏览器 对同一 URL 的签名是否一致。
若一致 → Node 复现完全正确。"""
import json, subprocess, sys, os
sys.path.insert(0, 'lib/abogus_rebuild')
from cdp2 import CDP, get_ws

def ev(cdp, expr, timeout=30):
    r = cdp.cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True}, timeout=timeout)
    res = r.get("result", {})
    if "exceptionDetails" in res:
        return "EXC: " + json.dumps(res["exceptionDetails"])[:300]
    return res.get("result", {}).get("value")

URL = "https://www-hj.douyin.com/aweme/v1/web/aweme/favorite/?sec_user_id=MS4wLjABAAAAuWb40KLM29J4hu2eXKN5GSZ8k3hdsZHRQ6CUNiW4OAY&count=18&aid=6383"
FIXED_TS = 1781000000  # 固定时间戳

# 1) 浏览器：固定 Date.now，调用 webSignUrl
cdp = CDP(get_ws())
cdp.cmd("Runtime.enable")
browser_expr = r"""(function(){
  var _now = Date.now;
  Date.now = function(){ return %d000; };
  try {
    var out = window.use('webSignUrl')(%s);
    return String(out);
  } finally { Date.now = _now; }
})()""" % (FIXED_TS, json.dumps(URL))
b_out = ev(cdp, browser_expr)
cdp.close()
import re
def parse(u):
    m = {}
    for k in ['uifid', 'timestamp', 'x-secsdk-web-signature']:
        mm = re.search(k + r'=([^&]+)', u)
        m[k] = mm.group(1) if mm else None
    return m
b = parse(b_out)
print("浏览器  ts:", b['timestamp'], "sig:", b['x-secsdk-web-signature'])

# 2) Node 补环境：固定时间戳（通过 patch Date）
node_code = '''
const path=require('path'), fs=require('fs');
global.__FIX_TS = %d000;
const env=require('./lib/websign_env.js');
const window=env.window;
// patch Date.now in the global used by the loaded script
const _Date = Date;
function load(file){
  const code=fs.readFileSync(path.join('./lib',file),'utf8');
  const patched = 'var Date=globalThis.__PatchedDate||Date;\\n'+code;
  const r=new Function('window','document','navigator','location','localStorage','sessionStorage','screen','performance','self','globalThis',patched);
  r.call(window,window,env.document,window.navigator,window.location,window.localStorage,window.sessionStorage,window.screen,window.performance,window,window);
}
globalThis.__PatchedDate = class extends _Date { static now(){ return global.__FIX_TS; } };
load('secsdk_runtime.js');
env.restoreProcess();
const out = window.use('webSignUrl')(%s);
console.log('__NODE__'+String(out));
''' % (FIXED_TS, json.dumps(URL))
res = subprocess.run(['node', '-e', node_code], capture_output=True, text=True, timeout=40, cwd='.')
n_out = ''
for line in res.stdout.splitlines():
    if line.startswith('__NODE__'):
        n_out = line[len('__NODE__'):]
if not n_out:
    print("NODE STDERR:", res.stderr[-500:])
n = parse(n_out)
print("Node    ts:", n['timestamp'], "sig:", n['x-secsdk-web-signature'])

print("\nuifid 一致:", b['uifid'] == n['uifid'])
print("签名一致:", b['x-secsdk-web-signature'] == n['x-secsdk-web-signature'])
