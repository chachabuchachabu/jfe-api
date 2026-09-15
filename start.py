import os,json,time,re,urllib.request,urllib.error
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import unquote
VERSION="0.9.0"; START=time.time()
VENUES={"大宮":"25","伊東温泉":"37","岐阜":"43","防府":"63","大垣":"44","青森":"12","岸和田":"56","いわき平":"13"}
def rid(d,v,r):
 c=VENUES.get(v)
 if not c: raise ValueError("UNKNOWN_VENUE")
 return d.replace("-","")+c+f"{int(r):02d}"
def fetch(u):
 q=urllib.request.Request(u,headers={"User-Agent":"JFE/0.9 qualification"})
 t=time.time()
 with urllib.request.urlopen(q,timeout=8) as x:return x.read().decode("utf-8","replace"),round((time.time()-t)*1000,1)
def race(d,v,r):
 i=rid(d,v,r); u=f"https://keirin.netkeiba.com/race/entry/?race_id={i}"; at=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
 try:
  h,lat=fetch(u); t=re.sub(r"<[^>]+>"," ",h); t=re.sub(r"\s+"," ",t); y,m,day=map(int,d.split("-"))
  if not (f"{m}/{day}" in t and v in t and f"{int(r)}R" in t): raise ValueError("JFE-04 ID_MISMATCH")
  st=re.search(r"発走\s*(\d{1,2}:\d{2})",t); cl=re.search(r"締切\s*(\d{1,2}:\d{2})",t)
  return 200,{"service":"JFE","version":VERSION,"status":"DEGRADED","race":{"race_id":i,"date":d,"venue":v,"race_no":int(r),"start_time":st.group(1) if st else None,"deadline":cl.group(1) if cl else None,"identity_validated":True},"blocks":{"identity":{"status":"READY","source":"netkeirin","acquired_at":at,"latency_ms":lat},"entry":{"status":"PENDING"},"rider_stats":{"status":"PENDING"},"line":{"status":"PENDING"},"odds":{"status":"PENDING"},"result":{"status":"PENDING"}},"provenance":{"entry_url":u},"qualification":{"live_source_request":True,"fabricated_data":False}}
 except Exception as e:return 503,{"service":"JFE","version":VERSION,"status":"BLOCKED","error":str(e),"race_id":i}
class H(BaseHTTPRequestHandler):
 def j(self,c,o,head=False):
  b=json.dumps(o,ensure_ascii=False).encode();self.send_response(c);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(b)));self.end_headers()
  if not head:self.wfile.write(b)
 def do_HEAD(self):self.j(200,{"service":"JFE","version":VERSION,"status":"UP"},True)
 def do_GET(self):
  p=unquote(self.path.split("?",1)[0])
  if p in ("/","/health"):return self.j(200,{"service":"JFE","version":VERSION,"status":"UP","mode":os.getenv("JFE_MODE","qualification"),"uptime_s":round(time.time()-START,2)})
  m=re.fullmatch(r"/v1/race/(\d{4}-\d{2}-\d{2})/([^/]+)/(\d{1,2})",p)
  if m:
   try:c,o=race(*m.groups())
   except Exception as e:c,o=400,{"status":"BLOCKED","error":str(e)}
   return self.j(c,o)
  self.j(404,{"error":"NOT_FOUND"})
 def log_message(self,f,*a):print(json.dumps({"event":"http","message":f%a},ensure_ascii=False),flush=True)
if __name__=="__main__":
 p=int(os.getenv("PORT","10000"));print(json.dumps({"event":"startup","service":"JFE","version":VERSION,"port":p}),flush=True);ThreadingHTTPServer(("0.0.0.0",p),H).serve_forever()
