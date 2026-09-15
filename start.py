import os,json,time,re,html as H,urllib.request,urllib.error
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import unquote
VERSION="1.0.0-rc1"; START=time.time()
VENUES={"大宮":"25","伊東温泉":"37","岐阜":"43","防府":"63","大垣":"44","青森":"12","岸和田":"56","いわき平":"13"}
CACHE={}; HEALTH={}
def now(): return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
def text(s):
 s=re.sub(r"<script.*?</script>|<style.*?</style>"," ",s,flags=re.S|re.I)
 return re.sub(r"\s+"," ",H.unescape(re.sub(r"<[^>]+>"," ",s))).strip()
def fetch(url,ttl=15):
 t=time.time()
 if url in CACHE and t-CACHE[url][0]<ttl:return CACHE[url][1],0.0,"CACHE"
 err=None
 for attempt in range(3):
  try:
   q=urllib.request.Request(url,headers={"User-Agent":"JFE/1.0 qualification"})
   with urllib.request.urlopen(q,timeout=8) as x: raw=x.read().decode("utf-8","replace")
   CACHE[url]=(time.time(),raw); HEALTH[url]={"ok":HEALTH.get(url,{}).get("ok",0)+1,"fail":HEALTH.get(url,{}).get("fail",0)}
   return raw,round((time.time()-t)*1000,1),"LIVE"
  except Exception as e:
   err=e; time.sleep(.25*(2**attempt))
 HEALTH[url]={"ok":HEALTH.get(url,{}).get("ok",0),"fail":HEALTH.get(url,{}).get("fail",0)+1}
 raise RuntimeError("JFE-01 FETCH_FAIL:"+type(err).__name__)
def parse_entry(raw):
 out=[]
 for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>",raw,flags=re.S|re.I):
  tt=text(row); reads=re.findall(r"(?<![ァ-ヶー])([ァ-ヶー]{4,})(?![ァ-ヶー])",tt)
  if not reads:continue
  cells=[text(x) for x in re.findall(r"<td\b[^>]*>(.*?)</td>",row,flags=re.S|re.I)]
  nums=[int(c) for c in cells[:6] if re.fullmatch(r"[1-9]",c)]
  if not nums:continue
  attrs=[H.unescape(x).strip() for x in re.findall(r'(?:alt|title)=["\']([^"\']+)["\']',row,flags=re.I)]
  names=[re.sub(r"[　 ]+","",x) for x in attrs if re.fullmatch(r"[一-龯々　 ]{2,10}",x)]
  if not names:continue
  # Capture rider profile URL when present for future authoritative stats join.
  links=re.findall(r'href=["\']([^"\']+)["\']',row,flags=re.I)
  prof=next((x for x in links if "profile" in x.lower() or "racer" in x.lower()),None)
  car=nums[1] if len(nums)>1 else nums[0]
  out.append({"car_no":car,"name":names[0],"reading":reads[0],"profile_url":prof})
 d={x["car_no"]:x for x in out if 1<=x["car_no"]<=9}; return [d[k] for k in sorted(d)]
def block(status,source=None,**kw):
 d={"status":status}
 if source:d["source"]=source
 d.update(kw); return d
def race(date,venue,rno):
 code=VENUES.get(venue)
 if not code:raise ValueError("UNKNOWN_VENUE")
 rid=date.replace("-","")+code+f"{int(rno):02d}"
 urls={
 "entry":f"https://keirin.netkeiba.com/race/entry/?race_id={rid}",
 "odds":f"https://keirin.netkeiba.com/odds/?race_id={rid}",
 "result":f"https://keirin.netkeiba.com/race/result/?race_id={rid}"}
 raw,lat,mode=fetch(urls["entry"],30); tt=text(raw); _,m,d=map(int,date.split("-"))
 if not(f"{m}/{d}" in tt and venue in tt and f"{int(rno)}R" in tt):raise ValueError("JFE-04 ID_MISMATCH")
 riders=parse_entry(raw); nums=[x["car_no"] for x in riders]
 entry_ok=5<=len(riders)<=9 and nums==list(range(1,len(riders)+1))
 st=re.search(r"発走\s*(\d{1,2}:\d{2})",tt); cl=re.search(r"締切\s*(\d{1,2}:\d{2})",tt)
 blocks={
 "identity":block("READY","netkeirin",acquired_at=now(),latency_ms=lat,transport=mode),
 "entry":block("READY" if entry_ok else "PENDING","netkeirin",rider_count=len(riders),validation="PASS" if entry_ok else "FAIL_CLOSED"),
 "rider_stats":block("PENDING",reason="PROFILE_JOIN_QUALIFICATION_REQUIRED"),
 "line":block("PENDING",reason="STRUCTURAL_LINE_QUALIFICATION_REQUIRED"),
 "odds":block("PENDING",reason="DYNAMIC_PRE_RACE_QUALIFICATION_REQUIRED",acquired_at=None),
 "result":block("PENDING",reason="POST_RACE_STATE_QUALIFICATION_REQUIRED")}
 mandatory=["identity","entry","rider_stats","odds"]
 status="READY" if all(blocks[x]["status"]=="READY" for x in mandatory) else "DEGRADED"
 return {"service":"JFE","version":VERSION,"status":status,
 "race":{"race_id":rid,"date":date,"venue":venue,"race_no":int(rno),"start_time":st.group(1) if st else None,"deadline":cl.group(1) if cl else None,"identity_validated":True},
 "riders":riders if entry_ok else [],"blocks":blocks,
 "provenance":{"entry_url":urls["entry"],"odds_url":urls["odds"],"result_url":urls["result"]},
 "diagnostics":{"mandatory":mandatory,"source_health":HEALTH,"cache_entries":len(CACHE),"fabricated_data":False}}
class S(BaseHTTPRequestHandler):
 def sendj(self,c,o,head=False):
  b=json.dumps(o,ensure_ascii=False).encode();self.send_response(c);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(b)));self.end_headers()
  if not head:self.wfile.write(b)
 def do_HEAD(self):self.sendj(200,{"service":"JFE","version":VERSION,"status":"UP"},True)
 def do_GET(self):
  p=unquote(self.path.split("?")[0])
  if p in("/","/health"):return self.sendj(200,{"service":"JFE","version":VERSION,"status":"UP","mode":"qualification","uptime_s":round(time.time()-START,2)})
  m=re.fullmatch(r"/v1/race/(\d{4}-\d{2}-\d{2})/([^/]+)/(\d{1,2})",p)
  if m:
   try:return self.sendj(200,race(*m.groups()))
   except Exception as e:return self.sendj(503,{"service":"JFE","version":VERSION,"status":"BLOCKED","error":str(e),"fabricated_data":False})
  if p=="/v1/diagnostics":return self.sendj(200,{"version":VERSION,"cache_entries":len(CACHE),"source_health":HEALTH})
  self.sendj(404,{"error":"NOT_FOUND"})
 def log_message(self,f,*a):pass
if __name__=="__main__":ThreadingHTTPServer(("0.0.0.0",int(os.getenv("PORT","10000"))),S).serve_forever()
