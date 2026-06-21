import sys, json
sys.path.insert(0, "lib/abogus_rebuild")
from cdp import CDP, get_douyin_page_ws

def grab(t):
    JS = """
    (async function(){
      const _OD=Date;
      Date.now=()=>%d;Math.random=()=>0.5;performance.now=()=>12345;
      window.Date=class extends _OD{constructor(...a){if(a.length===0)super(%d);else super(...a);}static now(){return %d;}};
      const longs={};
      const oC=String.prototype.charCodeAt;
      String.prototype.charCodeAt=function(i){try{const s=this.toString();if(i===0&&s.length>=120&&s.length<=140){const k='L'+s.length+'_'+s.charCodeAt(0);if(!longs[k])longs[k]=Array.from(s).map(c=>c.charCodeAt(0));}}catch(e){}return oC.call(this,i);};
      const base='https://www.douyin.com/aweme/v1/web/aweme/detail/?q=1';
      await new Promise((r)=>{const x=new XMLHttpRequest();x.open('GET',base,true);let d=false;x.onreadystatechange=function(){const fu=x.responseURL||'';if(!d&&fu.indexOf('a_bogus=')!==-1){d=true;r();try{x.abort();}catch(e){}}else if(x.readyState===4&&!d){d=true;r();}};x.send(null);setTimeout(()=>{if(!d){d=true;r();}},6000);});
      String.prototype.charCodeAt=oC;Date.now=_OD.now;window.Date=_OD;
      return JSON.stringify(longs);
    })()
    """ % (t,t,t)
    ws,_=get_douyin_page_ws(); cdp=CDP(ws)
    raw=cdp.eval(JS,await_promise=True,timeout_ms=15000); cdp.close()
    o=json.loads(raw)
    for k,v in o.items():
        if k.startswith('L13') and v and v[0]==171 and v[1]==85:
            return [x for x in v if x<256]
    return None

T0=1700000000000
results={}
for dt in [0,1,256,65536,16777216]:
    bb=grab(T0+dt)
    results[dt]=bb
    print(f'time+{dt}: bb={bb[:44] if bb else None}')
json.dump(results,open('lib/abogus_rebuild/time_bb.json','w'))
