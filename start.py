import os,json,time,re,html as H,urllib.request,hashlib
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import unquote
VERSION="1.0.0-ic1.3.1"; START=time.time()
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
  sm=re.search(r"(?:^|\s|[0-9])([逃追両])(?=\s|$|[0-9])",t) or re.search(r"([逃追両])",t)
  # Some class rows format percentages without a literal percent sign. Use cell values only
  # when exactly three plausible rate cells can be identified; never fabricate missing riders.
  if len(rates)<3:
   cell_rates=[]
   for c in cells:
    m=re.fullmatch(r"(\d{1,3}\.\d)%?",c)
    if m:
     v=float(m.group(1))
     if 0<=v<=100: cell_rates.append(v)
   if len(cell_rates)>=3: rates=cell_rates[-3:]
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
 conflict=False; generic=(occurrences==0 and len(vals)==0)
 owner=HASH_OWNER.get(rawhash)
 # Same unbound/no-odds template across races is a generic page, not a source conflict.
 # A conflict is meaningful only when the document carries race-specific evidence.
 if not generic:
  if owner and owner!=rid: conflict=True
  else: HASH_OWNER[rawhash]=rid
 snap={"race_id":rid,"acquired_at":acquired,"raw_sha256":rawhash,"content_sha256":content_sig,
       "bytes":len(raw.encode()),"race_id_occurrences":occurrences,"odds_value_count":len(vals),
       "unique_odds_values":unique,"generic_page":generic}
 SNAPSHOTS.setdefault(rid,[]).append(snap);SNAPSHOTS[rid]=SNAPSHOTS[rid][-5:]
 ok=(occurrences>0 and len(vals)>0 and unique>0 and not conflict)
 return ok,conflict,snap
KD_EVENT_BASE={
 # Qualification resolver. Expand only after event identity is externally verified.
 "2026-09-16|岸和田":"56202609140300",
}
def kd_url(date,venue,rno):
 base=KD_EVENT_BASE.get(f"{date}|{venue}")
 if not base:return None
 return f"https://keirin.kdreams.jp/kishiwada/racedetail/{base}{int(rno):02d}/?pageType=odds"

def normname(x):return re.sub(r"[　\s]+","",x)

def kd_odds_probe(raw,date,venue,rno,entry):
 t=txt(raw); y,m,d=map(int,date.split("-"))
 # KDreams may render non-zero-padded Japanese dates. Match semantically, not by fixed text.
 date_bound=bool(re.search(fr"{y}年\s*0?{m}月\s*0?{d}日",t))
 venue_bound=(venue in t)
 race_bound=bool(re.search(fr"(?<![0-9])0?{int(rno)}R(?![0-9])",t,re.I))
 nt=normname(t); name_hits=sum(1 for e in entry if normname(e["name"]) in nt)
 identity=(date_bound and venue_bound and race_bound and name_hits==len(entry) and len(entry)>0)
 # Conservative evidence only. This is not promoted to READY until bet-type mapping is qualified.
 pairs=re.findall(r"(?<![0-9])([1-9](?:-[1-9]){1,2})\s+(\d{1,4}\.\d)(?![0-9])",t)
 seen=set(); data=[]
 for comb,val in pairs:
  key=(comb,val)
  if key in seen:continue
  seen.add(key); data.append({"combination":comb,"odds":float(val),"legs":comb.count("-")+1})
 stamps=re.findall(r"(20\d{2}/\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2})現在",t)
 return {"identity_bound":identity,"date_bound":date_bound,"venue_bound":venue_bound,"race_bound":race_bound,
         "entry_name_hits":name_hits,"entry_count":len(entry),"odds_value_count":len(data),"data":data[:500],
         "source_timestamp":stamps[-1] if stamps else None,"content_bytes":len(raw.encode())}

def stats_trace(raw,entry):
 rows=[]
 for e in entry:
  matches=[]
  for tr in re.findall(r"<tr\b[^>]*>(.*?)</tr>",raw,flags=re.S|re.I):
   t=txt(tr)
   if e["name"] in t:
    cells=[txt(x) for x in re.findall(r"<td\b[^>]*>(.*?)</td>",tr,flags=re.S|re.I)]
    matches.append({"text":t[:700],"cells":cells[:30],
                    "scores":re.findall(r"(?<!\d)(\d{2,3}\.\d{1,2})(?!\d)",t),
                    "percent_rates":re.findall(r"(\d{1,3}\.\d)%",t),
                    "styles":re.findall(r"[逃追両]",t)})
  rows.append({"car_no":e["car_no"],"name":e["name"],"matched_rows":len(matches),"evidence":matches[:3]})
 return rows

def odds_route_trace(date,venue,rno,entry):
 vc=VENUES[venue];rid=date.replace("-","")+vc+f"{int(rno):02d}"
 primary_url=f"https://keirin.netkeiba.com/odds/?race_id={rid}"
 trace={"race_id":rid,"primary":{"source":"netkeirin","url":primary_url},"secondary":None}
 try:
  raw,lat,tr=fetch(primary_url,0); ok,conflict,snap=odds_integrity(raw,rid)
  trace["primary"].update({"transport":tr,"latency_ms":lat,"integrity_pass":ok,"conflict":conflict,"snapshot":snap})
 except Exception as e:trace["primary"].update({"error":str(e)})
 ku=kd_url(date,venue,rno)
 if ku:
  sec={"source":"kdreams","url":ku};trace["secondary"]=sec
  try:
   raw,lat,tr=fetch(ku,0); probe=kd_odds_probe(raw,date,venue,rno,entry)
   sec.update({"transport":tr,"latency_ms":lat,"probe":{k:v for k,v in probe.items() if k!="data"},"sample":probe.get("data",[])[:20]})
  except Exception as e:sec["error"]=str(e)
 return trace

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
  err="JFE-05 SOURCE_CONFLICT" if conflict else (None if ok else ("ODDS_GENERIC_PAGE" if snap.get("generic_page") else "ODDS_CONTENT_NOT_BOUND"))
  ob=block(ost,"netkeirin",acquired_at=snap["acquired_at"],latency_ms=olat,transport=otr,
           identity_bound=snap["race_id_occurrences"]>0,integrity_pass=ok,snapshot=snap,parser_qualified=False)
  if err:ob["error"]=err
 except Exception as e:ob=block("PENDING",error=str(e),parser_qualified=False)
 # Secondary Odds Adapter: fail over only when Primary is not READY/qualified.
 if ob.get("status")!="READY":
  ku=kd_url(date,venue,rno)
  if ku:
   try:
    kr,k_lat,k_tr=fetch(ku,0); kp=kd_odds_probe(kr,date,venue,rno,riders if eok else [])
    # IC1.3 qualifies source binding and parser evidence, but does not promote to READY
    # until bet-type section mapping/freshness is validated across multiple races.
    if kp["identity_bound"] and kp["odds_value_count"]>0:
     ob=block("QUALIFYING","kdreams",acquired_at=now(),latency_ms=k_lat,transport=k_tr,
              identity_bound=True,integrity_pass=True,parser_qualified=False,
              source_timestamp=kp["source_timestamp"],odds_value_count=kp["odds_value_count"],
              data=kp["data"],error="ODDS_BETTYPE_MAPPING_PENDING",failover_from="netkeirin")
    else:
     ob["secondary"]={"source":"kdreams","status":"PENDING",**kp}
   except Exception as e:
    ob["secondary"]={"source":"kdreams","status":"PENDING","error":str(e)}
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
 "qualification":{"fabricated_data":False, "odds_integrity_layer":True,"odds_ready":ob.get("status")=="READY","result_parser":True,"rider_stats_parser":True,"line_order_parser":True,
 "note":"Transport/content binding may qualify; actual odds parser + pre-race freshness still required before READY."},
 "diagnostics":{"source_health":HEALTH,"snapshot_races":len(SNAPSHOTS),"hash_owner_count":len(HASH_OWNER)}}

def readiness(packet):
 b=packet["blocks"]
 return {
  "identity": b["identity"]["status"]=="READY",
  "entry": b["entry"]["status"]=="READY",
  "rider_stats": b["rider_stats"]["status"]=="READY",
  "line_order": (b["entry"]["status"]=="READY" and b["line"]["status"]=="QUALIFIED_ORDER" and b["line"].get("entry_bound") is True),
  "line_groups": bool(b["line"].get("group_boundaries_qualified")),
  "odds": b["odds"]["status"]=="READY",
  "result": b["result"]["status"]=="READY"
 }

def je_packet(packet):
 r=readiness(packet)
 # Core pre-race readiness preserves the established mandatory semantics:
 # Identity + Entry + RiderStats + Odds. Line order is an enrichment layer.
 core_ok=all(r[k] for k in ("identity","entry","rider_stats","odds"))
 enriched_ok=core_ok and r["line_order"]
 return {
  "schema":"JFE-JE-RACE-PACKET/1.0",
  "jfe_version":VERSION,
  "race":packet["race"],
  "pre_race":{
    "ready":core_ok,
    "core_ready":core_ok,
    "enriched_ready":enriched_ok,
    "entry":packet["riders"],
    "rider_stats":packet["blocks"]["rider_stats"].get("rows",[]),
    "line":{"order":packet["blocks"]["line"].get("order",[]),
            "groups":packet["blocks"]["line"].get("groups",[]),
            "groups_ready":r["line_groups"]},
    "odds":{"ready":r["odds"],
            "snapshot":packet["blocks"]["odds"].get("snapshot"),
            "data":packet["blocks"]["odds"].get("data",[])}
  },
  "post_race":{"ready":r["result"],
               "finishers":packet["blocks"]["result"].get("finishers",[]),
               "payouts":packet["blocks"]["result"].get("payouts",{})},
  "readiness":r,
  "provenance":packet["provenance"],
  "fabricated_data":False
 }

def qualify_one(date,venue,rno):
 p=race(date,venue,rno); r=readiness(p)
 return {"race_id":p["race"]["race_id"],"date":date,"venue":venue,"race_no":int(rno),
         "readiness":r,
         "integrity":{"silent_wrong_data":"UNKNOWN",
                      "detected_identity_mismatch":False,
                      "detected_fail_closed":any(x.get("validation")=="FAIL_CLOSED" for x in p["blocks"].values() if isinstance(x,dict)),
                      "note":"Silent wrong data requires external ground-truth qualification; it is never assumed false."},
         "ready_count":sum(r.values()),"total_checks":len(r)}

def qualify_suite(date,venue,spec):
 nums=[]
 for part in spec.split(","):
  if "-" in part:
   a,b=map(int,part.split("-",1)); nums.extend(range(a,b+1))
  else: nums.append(int(part))
 nums=sorted(set(n for n in nums if 1<=n<=12))[:12]
 results=[]
 for n in nums:
  try: results.append({"ok":True,**qualify_one(date,venue,n)})
  except Exception as e: results.append({"ok":False,"race_no":n,"error":str(e)})
 return {"version":VERSION,"date":date,"venue":venue,"requested":nums,"results":results,
         "summary":{"tested":len(results),"transport_ok":sum(1 for x in results if x.get("ok")),
                    "identity_ready":sum(1 for x in results if x.get("readiness",{}).get("identity")),
                    "entry_ready":sum(1 for x in results if x.get("readiness",{}).get("entry")),
                    "rider_stats_ready":sum(1 for x in results if x.get("readiness",{}).get("rider_stats")),
                    "line_order_ready":sum(1 for x in results if x.get("readiness",{}).get("line_order")),
                    "odds_ready":sum(1 for x in results if x.get("readiness",{}).get("odds")),
                    "result_ready":sum(1 for x in results if x.get("readiness",{}).get("result"))}}

def failure_reason(packet, key):
 b=packet["blocks"].get(key,{})
 if key=="entry":
  return {"status":b.get("status"),"rider_count":b.get("rider_count"),"validation":b.get("validation"),"error":b.get("error")}
 if key=="rider_stats":
  return {"status":b.get("status"),"rider_count":b.get("rider_count"),"entry_count":packet["blocks"].get("entry",{}).get("rider_count"),"entry_bound":b.get("entry_bound"),"validation":b.get("validation"),"missing_car_nos":sorted(set(x.get("car_no") for x in packet.get("riders",[]))-set(x.get("car_no") for x in b.get("rows",[]))),"error":b.get("error")}
 if key=="odds":
  sn=b.get("snapshot") or {}
  return {"status":b.get("status"),"source":b.get("source"),"error":b.get("error"),"transport":b.get("transport"),"identity_bound":b.get("identity_bound"),"generic_page":sn.get("generic_page"),"race_id_occurrences":sn.get("race_id_occurrences"),"odds_value_count":b.get("odds_value_count",sn.get("odds_value_count")),"unique_odds_values":sn.get("unique_odds_values"),"source_timestamp":b.get("source_timestamp"),"secondary":b.get("secondary")}
 if key=="line":
  return {"status":b.get("status"),"order":b.get("order"),"groups_ready":b.get("group_boundaries_qualified"),"validation":b.get("validation"),"error":b.get("error")}
 if key=="result":
  return {"status":b.get("status"),"finisher_count":len(b.get("finishers",[])),"validation":b.get("validation"),"error":b.get("error")}
 return {"status":b.get("status"),"validation":b.get("validation"),"error":b.get("error")}

def failure_suite(date,venue,spec):
 base=qualify_suite(date,venue,spec)
 failures=[]
 for x in base["results"]:
  if not x.get("ok"):
   failures.append({"race_no":x.get("race_no"),"transport_error":x.get("error")}); continue
  n=x["race_no"]
  try:
   p=race(date,venue,n); r=readiness(p)
   bad=[]
   for k in ("identity","entry","rider_stats","line_order","line_groups","odds","result"):
    if not r[k]:
     source_key="line" if k in ("line_order","line_groups") else k
     bad.append({"block":k,"diagnostic":failure_reason(p,source_key)})
   failures.append({"race_no":n,"race_id":p["race"]["race_id"],"not_ready":bad})
  except Exception as e: failures.append({"race_no":n,"transport_error":str(e)})
 return {"version":VERSION,"date":date,"venue":venue,"requested":base["requested"],"summary":base["summary"],"failures":failures,
         "integrity_note":"Not-ready blocks are reported explicitly; silent wrong data remains UNKNOWN until external ground-truth qualification."}

def trace_one(date,venue,rno):
 vc=VENUES.get(venue)
 if not vc:raise ValueError("UNKNOWN_VENUE")
 rid=date.replace("-","")+vc+f"{int(rno):02d}"
 entry_url=f"https://keirin.netkeiba.com/race/entry/?race_id={rid}"
 raw,lat,tr=fetch(entry_url,0); entry=parse_entry(raw)
 stats,stats_ok=parse_stats(raw,entry)
 missing=sorted(set(x["car_no"] for x in entry)-set(x["car_no"] for x in stats))
 return {"version":VERSION,"race_id":rid,"date":date,"venue":venue,"race_no":int(rno),
         "entry":{"count":len(entry),"riders":entry,"transport":tr,"latency_ms":lat},
         "rider_stats":{"parser_ok":stats_ok,"parsed_count":len(stats),"missing_car_nos":missing,
                        "raw_row_trace":[x for x in stats_trace(raw,entry) if x["car_no"] in missing]},
         "odds_route":odds_route_trace(date,venue,rno,entry),
         "note":"Diagnostic evidence only. Secondary odds remains QUALIFYING until bet-type mapping/freshness is externally validated."}

class S(BaseHTTPRequestHandler):
 def j(self,c,o,head=False):
  z=json.dumps(o,ensure_ascii=False).encode();self.send_response(c);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(z)));self.end_headers()
  if not head:self.wfile.write(z)
 def do_HEAD(self):self.j(200,{"service":"JFE","version":VERSION,"status":"UP"},True)
 def do_GET(self):
  p=unquote(self.path.split("?")[0])
  if p in("/","/health"):return self.j(200,{"service":"JFE","version":VERSION,"status":"UP","mode":"qualification","uptime_s":round(time.time()-START,2)})
  if p=="/v1/diagnostics":return self.j(200,{"version":VERSION,"snapshots":SNAPSHOTS,"hash_owners":HASH_OWNER,"health":HEALTH})
  tm=re.fullmatch(r"/v1/trace/(\d{4}-\d{2}-\d{2})/([^/]+)/(\d{1,2})",p)
  if tm:
   try:return self.j(200,trace_one(*tm.groups()))
   except Exception as e:return self.j(503,{"service":"JFE","version":VERSION,"status":"BLOCKED","error":str(e),"fabricated_data":False})
  jm=re.fullmatch(r"/v1/je-packet/(\d{4}-\d{2}-\d{2})/([^/]+)/(\d{1,2})",p)
  if jm:
   try:return self.j(200,je_packet(race(*jm.groups())))
   except Exception as e:return self.j(503,{"service":"JFE","version":VERSION,"status":"BLOCKED","error":str(e),"fabricated_data":False})
  fm=re.fullmatch(r"/v1/failures-suite/(\d{4}-\d{2}-\d{2})/([^/]+)/([0-9,-]+)",p)
  if fm:
   try:return self.j(200,failure_suite(*fm.groups()))
   except Exception as e:return self.j(503,{"service":"JFE","version":VERSION,"status":"BLOCKED","error":str(e),"fabricated_data":False})
  sm=re.fullmatch(r"/v1/qualify-suite/(\d{4}-\d{2}-\d{2})/([^/]+)/([0-9,-]+)",p)
  if sm:
   try:return self.j(200,qualify_suite(*sm.groups()))
   except Exception as e:return self.j(503,{"service":"JFE","version":VERSION,"status":"BLOCKED","error":str(e),"fabricated_data":False})
  qm=re.fullmatch(r"/v1/qualify/(\d{4}-\d{2}-\d{2})/([^/]+)/(\d{1,2})",p)
  if qm:
   try:return self.j(200,qualify_one(*qm.groups()))
   except Exception as e:return self.j(503,{"service":"JFE","version":VERSION,"status":"BLOCKED","error":str(e),"fabricated_data":False})
  m=re.fullmatch(r"/v1/race/(\d{4}-\d{2}-\d{2})/([^/]+)/(\d{1,2})",p)
  if m:
   try:return self.j(200,race(*m.groups()))
   except Exception as e:return self.j(503,{"service":"JFE","version":VERSION,"status":"BLOCKED","error":str(e),"fabricated_data":False})
  self.j(404,{"error":"NOT_FOUND"})
 def log_message(self,f,*a):pass
if __name__=="__main__":ThreadingHTTPServer(("0.0.0.0",int(os.getenv("PORT","10000"))),S).serve_forever()
