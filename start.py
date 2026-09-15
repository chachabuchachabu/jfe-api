import os,json,time,re,html as H,urllib.request,hashlib
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import unquote
VERSION="1.0.0-rc5.1"; START=time.time()
VENUES={"大宮":"25","伊東温泉":"37","岐阜":"43","防府":"63","大垣":"44","青森":"12","岸和田":"56","いわき平":"13"}
CACHE={}; HEALTH={}; SNAPSHOTS={}; HASH_OWNER={}
def now():return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
def txt(s):
 s=re.sub(r"<script.*?</script>|<style.*?</style>"," ",s,flags=re.S|re.I)
 return re.sub(r"\s+"," ",H.unescape(re.sub(r"<[^>]+>"," ",s))).strip()
def fetch(url,ttl=0):
 t=time.time()
 if ttl and url in CACHE and t-CACHE[url][0]<ttl:return CACHE[url][1],0.0,"CACHE"
 e=None
 for a in range(3):
  try:
   q=urllib.request.Request(url,headers={"User-Agent":"JFE/1.0-RC3 qualification","Cache-Control":"no-cache"})
   with urllib.request.urlopen(q,timeout=8) as x:r=x.read().decode("utf-8","replace")
   if ttl:CACHE[url]=(time.time(),r)
   h=HEALTH.setdefault(url,{"ok":0,"fail":0});h["ok"]+=1
   return r,round((time.time()-t)*1000,1),"LIVE"
  except Exception as z:e=z;time.sleep(.25*2**a)
 h=HEALTH.setdefault(url,{"ok":0,"fail":0});h["fail"]+=1
 raise RuntimeError("JFE-01 FETCH_FAIL:"+type(e).__name__)
def parse_entry(raw):
 o=[]
 for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>",raw,flags=re.S|re.I):
  t=txt(row);rd=re.findall(r"(?<![ァ-ヶー])([ァ-ヶー]{4,})(?![ァ-ヶー])",t)
  if not rd:continue
  cs=[txt(x) for x in re.findall(r"<td\b[^>]*>(.*?)</td>",row,flags=re.S|re.I)]
  ns=[int(x) for x in cs[:6] if re.fullmatch(r"[1-9]",x)]
  at=[H.unescape(x).strip() for x in re.findall(r'(?:alt|title)=["\']([^"\']+)["\']',row,flags=re.I)]
  nm=[re.sub(r"[　 ]+","",x) for x in at if re.fullmatch(r"[一-龯々　 ]{2,10}",x)]
  if ns and nm:o.append({"car_no":ns[1] if len(ns)>1 else ns[0],"name":nm[0],"reading":rd[0]})
 d={x["car_no"]:x for x in o if 1<=x["car_no"]<=9};return[d[k] for k in sorted(d)]
def block(s,source=None,**kw):
 d={"status":s}
 if source:d["source"]=source
 d.update(kw);return d


def parse_stats(raw, entry):
 # Structural row parser: exact Entry identity anchors each rider's statistics.
 out=[]
 for tr in re.findall(r"<tr\b[^>]*>(.*?)</tr>",raw,flags=re.S|re.I):
  t=txt(tr); hits=[e for e in entry if e["name"] in t]
  if len(hits)!=1: continue
  e=hits[0]
  cells=[txt(x) for x in re.findall(r"<td\b[^>]*>(.*?)</td>",tr,flags=re.S|re.I)]
  # Score is distinctive 2-3 digit decimal; rates are percentages.
  scores=[float(x) for x in re.findall(r"(?<!\d)(\d{2,3}\.\d{2})(?!\d)",t)]
  rates=[float(x) for x in re.findall(r"(\d{1,3}\.\d)%",t)]
  # style: netkeirin emits a prefixed numeric class marker such as 1逃 / 3追.
  sm=re.search(r"(?:^|\s)[123]?([逃追両])(?:\s|$)",t)
  if not scores or len(rates)<3 or not sm: continue
  # Use the last three percentages in the row as win/2-place/3-place rates.
  out.append({"car_no":e["car_no"],"name":e["name"],"score":scores[0],"style":sm.group(1),
              "win_rate":rates[-3],"two_rate":rates[-2],"three_rate":rates[-1]})
 d={x["car_no"]:x for x in out}
 rows=[d[k] for k in sorted(d)]
 ok=(len(rows)==len(entry) and {x["car_no"] for x in rows}=={x["car_no"] for x in entry}
     and all(0<=x["win_rate"]<=x["two_rate"]<=x["three_rate"]<=100 for x in rows)
     and all(50<=x["score"]<=150 for x in rows))
 return rows,ok

def parse_line(raw, entry):
 # Prefer the explicit "並び予想" section and bind its rider names back to Entry.
 t=txt(raw); pos=t.find("並び予想")
 if pos<0:return [],False
 s=t[pos:pos+1800]
 seq=[]
 for m in re.finditer(r"([1-9])\s*([一-龯々　 ]{1,12})",s):
  car=int(m.group(1)); name=re.sub(r"[　 ]+","",m.group(2))
  match=[e for e in entry if e["car_no"]==car and (e["name"].startswith(name) or name.startswith(e["name"][:2]))]
  if match and car not in seq:seq.append(car)
 # A safe line order must cover every entrant exactly once. Group boundaries are intentionally not inferred yet.
 ok=(len(seq)==len(entry) and set(seq)=={e["car_no"] for e in entry})
 return seq,ok

def parse_result(raw, entry):
 rows=[]
 for tr in re.findall(r"<tr\b[^>]*>(.*?)</tr>",raw,flags=re.S|re.I):
  t=txt(tr)
  m=re.search(r"([1-9])着",t)
  if not m: continue
  rank=int(m.group(1))
  # Result rows contain linked rider name; bind only to a known Entry rider.
  hits=[]
  for e in entry:
   if e["name"] in t: hits.append(e)
  if len(hits)!=1: continue
  e=hits[0]
  # Require the car number to occur as a standalone table-cell value.
  cells=[txt(x) for x in re.findall(r"<td\b[^>]*>(.*?)</td>",tr,flags=re.S|re.I)]
  nums=[int(x) for x in cells if re.fullmatch(r"[1-9]",x)]
  if e["car_no"] not in nums: continue
  ag=re.search(r"(?<!\d)(\d{2}\.\d)(?!\d)",t)
  decision=next((x for x in ("逃","捲","差","マーク") if x in t),None)
  rows.append({"rank":rank,"car_no":e["car_no"],"name":e["name"],
               "agari":float(ag.group(1)) if ag else None,"decision":decision})
 rows=sorted({x["rank"]:(x) for x in rows}.values(),key=lambda x:x["rank"])
 cars=[x["car_no"] for x in rows]
 ok=(len(rows)==len(entry) and [x["rank"] for x in rows]==list(range(1,len(entry)+1))
     and len(cars)==len(set(cars)) and set(cars)=={x["car_no"] for x in entry})
 return rows,ok

def parse_payouts(raw):
 t=txt(raw); out={}
 pats={
  "quinella":r"２車複\s*([1-9]-[1-9])\s*([\d,]+)円",
  "exacta":r"２車単\s*([1-9]>[1-9])\s*([\d,]+)円",
  "trio":r"３連複\s*([1-9]-[1-9]-[1-9])\s*([\d,]+)円",
  "trifecta":r"３連単\s*([1-9]>[1-9]>[1-9])\s*([\d,]+)円"}
 for k,p in pats.items():
  m=re.search(p,t)
  if m: out[k]={"combination":m.group(1),"payout_yen":int(m.group(2).replace(",",""))}
 return out

def odds_integrity(raw,rid):
 acquired=now(); rawhash=hashlib.sha256(raw.encode()).hexdigest()
 # Strong evidence: requested race_id must occur in the returned document itself.
 occurrences=len(re.findall(re.escape(rid),raw))
 # Extract conservative numeric odds-like values only as evidence, not yet as betting data.
 t=txt(raw); vals=re.findall(r"(?<!\d)(\d{1,4}\.\d)(?!\d)",t)
 unique=len(set(vals)); content_sig=hashlib.sha256((rid+"|"+ "|".join(vals[:500])).encode()).hexdigest()
 conflict=False; owner=HASH_OWNER.get(rawhash)
 if owner and owner!=rid: conflict=True
 else: HASH_OWNER[rawhash]=rid
 snap={"race_id":rid,"acquired_at":acquired,"raw_sha256":rawhash,"content_sha256":content_sig,
       "bytes":len(raw.encode()),"race_id_occurrences":occurrences,"odds_value_count":len(vals),
       "unique_odds_values":unique}
 SNAPSHOTS.setdefault(rid,[]).append(snap);SNAPSHOTS[rid]=SNAPSHOTS[rid][-5:]
 ok=(occurrences>0 and len(vals)>0 and unique>0 and not conflict)
 return ok,conflict,snap
def race(date,venue,rno):
 vc=VENUES.get(venue)
 if not vc:raise ValueError("UNKNOWN_VENUE")
 rid=date.replace("-","")+vc+f"{int(rno):02d}"
 urls={"entry":f"https://keirin.netkeiba.com/race/entry/?race_id={rid}",
       "odds":f"https://keirin.netkeiba.com/odds/?race_id={rid}",
       "result":f"https://keirin.netkeiba.com/race/result/?race_id={rid}"}
 raw,lat,tr=fetch(urls["entry"],30);t=txt(raw);_,m,d=map(int,date.split("-"))
 if not(f"{m}/{d}" in t and venue in t and f"{int(rno)}R" in t):raise ValueError("JFE-04 ID_MISMATCH")
 riders=parse_entry(raw);nums=[x["car_no"] for x in riders];eok=5<=len(riders)<=9 and nums==list(range(1,len(riders)+1))
 try:
  oraw,olat,otr=fetch(urls["odds"],0);ok,conflict,snap=odds_integrity(oraw,rid)
  ost="QUALIFIED_TRANSPORT" if ok else "PENDING"
  err="JFE-05 SOURCE_CONFLICT" if conflict else (None if ok else "ODDS_CONTENT_NOT_BOUND")
  ob=block(ost,"netkeirin",acquired_at=snap["acquired_at"],latency_ms=olat,transport=otr,
           identity_bound=snap["race_id_occurrences"]>0,integrity_pass=ok,snapshot=snap,parser_qualified=False)
  if err:ob["error"]=err
 except Exception as e:ob=block("PENDING",error=str(e),parser_qualified=False)
 try:
  rr,rl,rt=fetch(urls["result"],15)
  result_rows,result_ok=parse_result(rr,riders if eok else [])
  payouts=parse_payouts(rr)
  rb=block("READY" if result_ok else "PENDING","netkeirin",acquired_at=now(),latency_ms=rl,transport=rt,
           content_bytes=len(rr.encode()),parser_qualified=result_ok,entry_bound=result_ok,
           finishers=result_rows,payouts=payouts,
           validation="PASS" if result_ok else "FAIL_CLOSED")
 except Exception as e:rb=block("PENDING",error=str(e),parser_qualified=False)
 st=re.search(r"発走\s*(\d{1,2}:\d{2})",t);cl=re.search(r"締切\s*(\d{1,2}:\d{2})",t)
 stats,stats_ok=parse_stats(raw,riders if eok else [])
 line_order,line_ok=parse_line(raw,riders if eok else [])
 blocks={"identity":block("READY","netkeirin",acquired_at=now(),latency_ms=lat,transport=tr),
 "entry":block("READY" if eok else "PENDING","netkeirin",rider_count=len(riders),validation="PASS" if eok else "FAIL_CLOSED"),
 "rider_stats":block("READY" if stats_ok else "PENDING","netkeirin",entry_bound=stats_ok,
                     rider_count=len(stats),rows=stats,validation="PASS" if stats_ok else "FAIL_CLOSED"),
 "line":block("QUALIFIED_ORDER" if line_ok else "PENDING","netkeirin",entry_bound=line_ok,
              order=line_order,group_boundaries_qualified=False,
              validation="ORDER_PASS_GROUPS_PENDING" if line_ok else "FAIL_CLOSED"),
 "odds":ob,"result":rb}
 return {"service":"JFE","version":VERSION,"status":"DEGRADED",
 "race":{"race_id":rid,"date":date,"venue":venue,"race_no":int(rno),"start_time":st.group(1) if st else None,"deadline":cl.group(1) if cl else None,"identity_validated":True},
 "riders":riders if eok else [],"blocks":blocks,"provenance":urls,
 "qualification":{"fabricated_data":False, "odds_integrity_layer":True,"odds_ready":False,"result_parser":True,"rider_stats_parser":True,"line_order_parser":True,
 "note":"Transport/content binding may qualify; actual odds parser + pre-race freshness still required before READY."},
 "diagnostics":{"source_health":HEALTH,"snapshot_races":len(SNAPSHOTS),"hash_owner_count":len(HASH_OWNER)}}
class S(BaseHTTPRequestHandler):
 def j(self,c,o,head=False):
  z=json.dumps(o,ensure_ascii=False).encode();self.send_response(c);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(z)));self.end_headers()
  if not head:self.wfile.write(z)
 def do_HEAD(self):self.j(200,{"service":"JFE","version":VERSION,"status":"UP"},True)
 def do_GET(self):
  p=unquote(self.path.split("?")[0])
  if p in("/","/health"):return self.j(200,{"service":"JFE","version":VERSION,"status":"UP","mode":"qualification","uptime_s":round(time.time()-START,2)})
  if p=="/v1/diagnostics":return self.j(200,{"version":VERSION,"snapshots":SNAPSHOTS,"hash_owners":HASH_OWNER,"health":HEALTH})
  m=re.fullmatch(r"/v1/race/(\d{4}-\d{2}-\d{2})/([^/]+)/(\d{1,2})",p)
  if m:
   try:return self.j(200,race(*m.groups()))
   except Exception as e:return self.j(503,{"service":"JFE","version":VERSION,"status":"BLOCKED","error":str(e),"fabricated_data":False})
  self.j(404,{"error":"NOT_FOUND"})
 def log_message(self,f,*a):pass
if __name__=="__main__":ThreadingHTTPServer(("0.0.0.0",int(os.getenv("PORT","10000"))),S).serve_forever()
