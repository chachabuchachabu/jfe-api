import html
import os,json,time,re,html as H,urllib.request,hashlib,threading,queue
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import unquote,parse_qs,urlparse
VERSION="1.0.0-ic1.4-dev-b48.2"; START=time.time()
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


def _parse_stats_row(tr, e):
 # Parse one rider row only after Entry identity has selected the rider.
 t=txt(tr)
 cells=[txt(x) for x in re.findall(r"<td\b[^>]*>(.*?)</td>",tr,flags=re.S|re.I)]
 scores=[float(x) for x in re.findall(r"(?<!\d)(\d{2,3}\.\d{2})(?!\d)",t)]
 rates=[float(x) for x in re.findall(r"(\d{1,3}\.\d)%",t)]
 sm=re.search(r"(?:^|\s|[0-9])([逃追両])(?=\s|$|[0-9])",t) or re.search(r"([逃追両])",t)
 if len(rates)<3:
  cell_rates=[]
  for c in cells:
   m=re.fullmatch(r"(\d{1,3}\.\d)%?",c)
   if m:
    v=float(m.group(1))
    if 0<=v<=100:cell_rates.append(v)
  if len(cell_rates)>=3:rates=cell_rates[-3:]
 if not scores or len(rates)<3 or not sm:return None
 row={"car_no":e["car_no"],"name":e["name"],"score":scores[0],"style":sm.group(1),
      "win_rate":rates[-3],"two_rate":rates[-2],"three_rate":rates[-1]}
 if not (0<=row["win_rate"]<=row["two_rate"]<=row["three_rate"]<=100):return None
 if not 50<=row["score"]<=150:return None
 return row

def parse_stats(raw, entry):
 # IC1.4-B Entry-first binding. Expected cars come only from the verified Entry manifest.
 expected={e["car_no"]:e for e in entry}
 trs=re.findall(r"<tr\b[^>]*>(.*?)</tr>",raw,flags=re.S|re.I)
 out={}; recovery=[]
 # Pass 1: structural rows with exactly one Entry identity.
 for tr in trs:
  t=txt(tr);hits=[e for e in entry if e["name"] in t]
  if len(hits)!=1:continue
  row=_parse_stats_row(tr,hits[0])
  if row:out[row["car_no"]]=row
 # Pass 2: targeted recovery only for missing active cars. Never re-fetch/re-parse successful riders.
 missing=sorted(set(expected)-set(out))
 for car in missing:
  e=expected[car]; candidates=[]
  for tr in trs:
   t=txt(tr)
   if e["name"] in t:candidates.append(tr)
  recovered=None
  for tr in candidates:
   recovered=_parse_stats_row(tr,e)
   if recovered:break
  recovery.append({"car_no":car,"name":e["name"],"initial_state":"PARTIAL_PARSE",
                   "candidate_rows":len(candidates),"final_state":"AVAILABLE" if recovered else "ERROR",
                   "method":"TARGETED_ENTRY_IDENTITY"})
  if recovered:out[car]=recovered
 rows=[out[k] for k in sorted(out) if k in expected]
 final_missing=sorted(set(expected)-set(out))
 unexpected=sorted(set(out)-set(expected))
 ok=bool(entry) and not final_missing and not unexpected and len(rows)==len(entry)
 meta={"state":"AVAILABLE" if ok else ("PARTIAL" if rows else "ERROR"),
       "expected_car_nos":sorted(expected),"retrieved_car_nos":sorted(out),
       "missing_car_nos":final_missing,"unexpected_car_nos":unexpected,"recovery_history":recovery}
 return rows,ok,meta

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


BET_TYPES={"ワイド":("wide",2),"２車複":("quinella",2),"2車複":("quinella",2),"２車単":("exacta",2),"2車単":("exacta",2),"３連複":("trio",3),"3連複":("trio",3),"３連単":("trifecta",3),"3連単":("trifecta",3)}

def _norm_combination(x):
 nums=[int(n) for n in re.findall(r"[1-9]",x)]
 return tuple(nums)

def parse_kd_odds_sections(raw, active_car_nos):
 """IC1.4-C fail-closed odds parser. Values are promoted only inside an explicitly bound bet-type section."""
 active=set(active_car_nos); text=txt(raw)
 # Find explicit bet-type headings in document order. No heading => no inference.
 marks=[]
 for label,(key,legs) in BET_TYPES.items():
  for m in re.finditer(re.escape(label),text): marks.append((m.start(),m.end(),label,key,legs))
 # De-duplicate aliases/hits at nearly the same position and sort.
 marks=sorted(marks,key=lambda x:x[0]); ded=[]
 for x in marks:
  if ded and x[0]-ded[-1][0]<4 and x[3]==ded[-1][3]: continue
  ded.append(x)
 marks=ded
 states={k:{"state":"UNKNOWN","bet_type_bound":False,"data":[],"rejected":[]} for k in ("wide","quinella","exacta","trio","trifecta")}
 for i,(a,b,label,key,legs) in enumerate(marks):
  end=marks[i+1][0] if i+1<len(marks) else min(len(text),b+12000)
  section=text[b:end]
  rec=states[key];rec["bet_type_bound"]=True;rec["label_evidence"]=label
  # Require exact leg arity; separators may be -, >, =, whitespace around values.
  pat=r"(?<![0-9])("+r"\s*[-=>]\s*".join([r"[1-9]"]*legs)+r")\s+(\d{1,5}(?:\.\d+)?)"
  for comb,val in re.findall(pat,section):
   nums=_norm_combination(comb); reason=None
   if len(nums)!=legs: reason="SELECTION_ARITY_ERROR"
   elif len(set(nums))!=legs: reason="DUPLICATE_SELECTION"
   elif not set(nums).issubset(active): reason="INVALID_COMBINATION"
   else:
    odds=float(val)
    if odds<=1.0: reason="INVALID_ODDS"
   item={"combination":"-".join(map(str,nums)),"selection":list(nums),"odds":float(val)}
   if reason:item["reason"]=reason;rec["rejected"].append(item)
   else:rec["data"].append(item)
  # Explicit section but no valid values is UNKNOWN unless source explicitly says unpublished.
  unpublished=bool(re.search(r"(?:未発売|発売前|オッズ未発表|まだ発売されていません)",section[:1200]))
  if rec["data"]: rec["state"]="AVAILABLE"
  elif unpublished: rec["state"]="NOT_PUBLISHED"
  elif rec["rejected"]: rec["state"]="ERROR"
  else: rec["state"]="UNKNOWN"
 return states

def kd_odds_probe(raw,date,venue,rno,entry):
 t=txt(raw); y,m,d=map(int,date.split("-"))
 # KDreams may render non-zero-padded Japanese dates. Match semantically, not by fixed text.
 date_bound=bool(re.search(fr"{y}年\s*0?{m}月\s*0?{d}日",t))
 venue_bound=(venue in t)
 race_bound=bool(re.search(fr"(?<![0-9])0?{int(rno)}R(?![0-9])",t,re.I))
 nt=normname(t); name_hits=sum(1 for e in entry if normname(e["name"]) in nt)
 identity=(date_bound and venue_bound and race_bound and name_hits==len(entry) and len(entry)>0)
 # Conservative evidence only. This is not promoted to READY until bet-type mapping is qualified.
 sections=parse_kd_odds_sections(raw,[e["car_no"] for e in entry]) if identity else {k:{"state":"UNKNOWN","bet_type_bound":False,"data":[],"rejected":[]} for k in ("wide","quinella","exacta","trio","trifecta")}
 data=[]
 for bt,rec in sections.items():
  for q in rec.get("data",[]): data.append({**q,"bet_type":bt})
 stamps=re.findall(r"(20\d{2}/\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2})現在",t)
 return {"identity_bound":identity,"date_bound":date_bound,"venue_bound":venue_bound,"race_bound":race_bound,
         "entry_name_hits":name_hits,"entry_count":len(entry),"odds_value_count":len(data),"data":data[:500],
         "bet_types":sections,"source_timestamp":stamps[-1] if stamps else None,"content_bytes":len(raw.encode())}

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
    available_types=[k for k,v in kp.get("bet_types",{}).items() if v.get("state")=="AVAILABLE" and v.get("bet_type_bound")]
    if kp["identity_bound"] and kp["odds_value_count"]>0 and available_types:
     # Source timestamp is retained separately; absence does not masquerade as NOT_PUBLISHED.
     fresh_state="UNKNOWN" if not kp.get("source_timestamp") else "SOURCE_TIMESTAMP_PRESENT"
     ob=block("READY","kdreams",acquired_at=now(),latency_ms=k_lat,transport=k_tr,
              identity_bound=True,integrity_pass=True,parser_qualified=True,
              source_timestamp=kp["source_timestamp"],freshness_state=fresh_state,available_bet_types=available_types,
              bet_types=kp["bet_types"],odds_value_count=kp["odds_value_count"],
              data=kp["data"],failover_from="netkeirin")
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
 stats,stats_ok,stats_meta=parse_stats(raw,riders if eok else [])
 line_order,line_ok=parse_line(raw,riders if eok else [])
 blocks={"identity":block("READY","netkeirin",acquired_at=now(),latency_ms=lat,transport=tr),
 "entry":block("READY" if eok else "PENDING","netkeirin",rider_count=len(riders),validation="PASS" if eok else "FAIL_CLOSED"),
 "rider_stats":block("READY" if stats_ok else "PENDING","netkeirin",entry_bound=stats_ok,
                     rider_count=len(stats),rows=stats,validation="PASS" if stats_ok else "FAIL_CLOSED",
                     state=stats_meta["state"],expected_car_nos=stats_meta["expected_car_nos"],
                     missing_car_nos=stats_meta["missing_car_nos"],unexpected_car_nos=stats_meta["unexpected_car_nos"],
                     recovery_history=stats_meta["recovery_history"]),
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
  "integrity":{
    "race_binding":"PASS" if r["identity"] else "ERROR",
    "entry_state":"AVAILABLE" if r["entry"] else "ERROR",
    "rider_state":packet["blocks"]["rider_stats"].get("state","UNKNOWN"),
    "missing_car_nos":packet["blocks"]["rider_stats"].get("missing_car_nos",[]),
    "unexpected_car_nos":packet["blocks"]["rider_stats"].get("unexpected_car_nos",[]),
    "recovery_history":packet["blocks"]["rider_stats"].get("recovery_history",[]),
    "odds_state":"AVAILABLE" if r["odds"] else "UNKNOWN",
    "available_bet_types":packet["blocks"]["odds"].get("available_bet_types",[]),
    "source_timestamp":packet["blocks"]["odds"].get("source_timestamp"),
    "freshness_state":packet["blocks"]["odds"].get("freshness_state","UNKNOWN")
  },
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
 stats,stats_ok,stats_meta=parse_stats(raw,entry)
 missing=sorted(set(x["car_no"] for x in entry)-set(x["car_no"] for x in stats))
 return {"version":VERSION,"race_id":rid,"date":date,"venue":venue,"race_no":int(rno),
         "entry":{"count":len(entry),"riders":entry,"transport":tr,"latency_ms":lat},
         "rider_stats":{"parser_ok":stats_ok,"parsed_count":len(stats),"missing_car_nos":missing,"state":stats_meta["state"],"recovery_history":stats_meta["recovery_history"],
                        "raw_row_trace":[x for x in stats_trace(raw,entry) if x["car_no"] in missing]},
         "odds_route":odds_route_trace(date,venue,rno,entry),
         "note":"Diagnostic evidence only. Secondary odds remains QUALIFYING until bet-type mapping/freshness is externally validated."}











# ===== DEV-B44 Entry-First Binding =====
def _strip_tags(x):
    x=re.sub(r"<br\s*/?>"," ",x,flags=re.I); x=re.sub(r"<[^>]+>"," ",x)
    return re.sub(r"\s+"," ",html.unescape(x)).strip()

def parse_primary_racecard_entries(raw):
    m=re.search(r'<table\b[^>]*class=["\'][^"\']*\bracecard_table\b(?![^"\']*\bnone\b)[^"\']*["\'][^>]*>(.*?)</table>',raw,re.I|re.S)
    if not m: return {"state":"UNKNOWN","entries":[],"errors":["PRIMARY_RACECARD_TABLE_NOT_FOUND"]}
    entries=[]; errors=[]
    for rm in re.finditer(r'<tr\b[^>]*class=["\'][^"\']*\bn(\d+)\b[^"\']*["\'][^>]*>(.*?)</tr>',m.group(1),re.I|re.S):
        rc=int(rm.group(1)); row=rm.group(2)
        nm=re.search(r'<td\b[^>]*class=["\'][^"\']*\bnum\b[^"\']*["\'][^>]*>\s*<span[^>]*>\s*(\d+)\s*</span>',row,re.I|re.S)
        rider=re.search(r'<td\b[^>]*class=["\'][^"\']*\brider\b[^"\']*["\'][^>]*>(.*?)(?:<br\s*/?>)(.*?)</td>',row,re.I|re.S)
        if not nm or not rider: errors.append("ROW_BINDING_INCOMPLETE:n%s"%rc); continue
        car=int(nm.group(1)); name=_strip_tags(rider.group(1)); home=_strip_tags(rider.group(2))
        hm=re.search(r'(.+?)/\s*(\d+)\s*/\s*(\d+)',home)
        td_matches=list(re.finditer(r'<td\b([^>]*)>(.*?)</td>',row,re.I|re.S))
        rider_idx=None; cells=[]
        for i,tm in enumerate(td_matches):
            attrs=tm.group(1); cells.append(_strip_tags(tm.group(2)))
            cm=re.search(r'class=["\']([^"\']*)["\']',attrs,re.I)
            if cm and "rider" in cm.group(1).split(): rider_idx=i
        grade=None; score=None
        if rider_idx is not None:
            if rider_idx+1 < len(cells): grade=cells[rider_idx+1] or None
            if rider_idx+4 < len(cells):
                try: score=float(cells[rider_idx+4])
                except: score=None
        if car!=rc: errors.append("CAR_CLASS_MISMATCH:%s:%s"%(rc,car)); continue
        if not name: errors.append("RIDER_NAME_EMPTY:%s"%car); continue
        entries.append({"car_no":car,"rider_name":name,
          "prefecture":hm.group(1).replace(" ","") if hm else None,
          "age":int(hm.group(2)) if hm else None,"term":int(hm.group(3)) if hm else None,
          "grade":grade,"race_score":score,
          "binding_evidence":{"row_class":"n%s"%rc,"num_cell":str(car),"rider_cell":home}})
    cars=[e["car_no"] for e in entries]
    if len(cars)!=len(set(cars)): errors.append("DUPLICATE_CAR_NUMBER")
    return {"state":"AVAILABLE" if entries and not errors else ("PARTIAL" if entries else "UNKNOWN"),
      "entries":entries,"expected_car_numbers":sorted(set(cars)),"retrieved_car_numbers":sorted(set(cars)),
      "missing_car_numbers":[],"unexpected_car_numbers":[],"errors":errors}

def live_entry_binding(target_date):
    base=live_race_verification(target_date); races=[]; recovery=[]
    for venue in base.get("venues",[]):
        if venue.get("state")!="VERIFIED_VENUE": continue
        identity={}
        for ev in venue.get("evidence",[]): identity.update(ev.get("race_identity_evidence") or {})
        for race_no in venue.get("races",[]):
            urls=identity.get(race_no) or identity.get(str(race_no)) or []
            url=canonical_racedetail_url(urls)
            rec={"kaisai_date_id":venue.get("kaisai_date_id"),"venue_code":venue.get("venue_code"),"race_no":race_no,"race_url":url}
            if not url:
                rec.update({"state":"ERROR","error_type":"RACE_BINDING_ERROR"}); races.append(rec); continue
            try:
                q=urllib.request.Request(url,headers={"User-Agent":"JFE-Entry-Binding/0.1","Accept-Encoding":"identity","Cache-Control":"no-cache"})
                with urllib.request.urlopen(q,timeout=20) as x: body=x.read(); status=getattr(x,"status",None)
                parsed=parse_primary_racecard_entries(body.decode("utf-8","replace")) if status==200 else {"state":"ERROR","entries":[],"errors":["HTTP_ERROR"]}
                rec.update({"http_status":status,"byte_length":len(body),"content_sha256":hashlib.sha256(body).hexdigest(),"state":parsed["state"],"entry_binding":parsed})
                if parsed["state"]!="AVAILABLE": recovery.append({"kaisai_date_id":venue.get("kaisai_date_id"),"race_no":race_no,"reason":"ENTRY_BINDING_INCOMPLETE","errors":parsed.get("errors",[])})
            except Exception as e:
                rec.update({"state":"ERROR","error_type":type(e).__name__,"error":str(e)})
                recovery.append({"kaisai_date_id":venue.get("kaisai_date_id"),"race_no":race_no,"reason":"ENTRY_FETCH_ERROR"})
            races.append(rec)
    avail=sum(r.get("state")=="AVAILABLE" for r in races)
    return {"schema":"JFE-LIVE-ENTRY-BINDING/0.1","service":"JFE","version":VERSION,"target_date":target_date,
      "state":"AVAILABLE" if races and avail==len(races) else "PARTIAL","acquired_at":now(),"race_count":len(races),
      "available_race_count":avail,"races":races,"recovery_queue":recovery,
      "binding_contract":"PRIMARY_RACECARD_ROW_CLASS_NUM_RIDER","fabricated_data":False}

def compact_entry_binding(target_date):
    x=live_entry_binding(target_date); rows=[]
    for r in x.get("races",[]):
        b=r.get("entry_binding") or {}
        rows.append({"venue_code":r.get("venue_code"),"race_no":r.get("race_no"),"state":r.get("state"),
          "http_status":r.get("http_status"),"entry_count":len(b.get("entries",[])),"cars":b.get("retrieved_car_numbers",[]),
          "riders":[{"car_no":e.get("car_no"),"name":e.get("rider_name"),"prefecture":e.get("prefecture"),
                     "age":e.get("age"),"term":e.get("term"),"grade":e.get("grade"),"race_score":e.get("race_score")}
                    for e in b.get("entries",[])],"errors":b.get("errors",[])})
    return {"schema":"JFE-COMPACT-ENTRY-BINDING/0.1","service":"JFE","version":VERSION,"target_date":target_date,
      "state":x.get("state"),"race_count":x.get("race_count"),"available_race_count":x.get("available_race_count"),
      "races":rows,"recovery_count":len(x.get("recovery_queue",[])),"fabricated_data":False}

# ===== DEV-B45 Entry Integrity Gate =====
def validate_entry_integrity(binding):
    entries=(binding or {}).get("entries") or []
    errors=[]; warnings=[]
    cars=[]; names=[]
    field_states=[]
    for e in entries:
        car=e.get("car_no"); name=e.get("rider_name")
        f={"car_no":car,"name":name,"state":"AVAILABLE","errors":[]}
        if not isinstance(car,int) or car <= 0: f["errors"].append("INVALID_CAR_NUMBER")
        if not isinstance(name,str) or not name.strip(): f["errors"].append("EMPTY_RIDER_NAME")
        if not isinstance(e.get("age"),int) or e.get("age") <= 0: f["errors"].append("INVALID_AGE")
        if not isinstance(e.get("term"),int) or e.get("term") <= 0: f["errors"].append("INVALID_TERM")
        grade=e.get("grade")
        if not isinstance(grade,str) or not re.fullmatch(r"(?:S|A|L)\d+",grade): f["errors"].append("INVALID_GRADE")
        score=e.get("race_score")
        if not isinstance(score,(int,float)) or isinstance(score,bool): f["errors"].append("INVALID_RACE_SCORE")
        if f["errors"]: f["state"]="ERROR"; errors.extend("CAR_%s:%s"%(car,x) for x in f["errors"])
        cars.append(car); names.append(name); field_states.append(f)
    if not entries: errors.append("NO_BOUND_ENTRIES")
    valid_cars=[x for x in cars if isinstance(x,int) and x>0]
    if len(valid_cars)!=len(set(valid_cars)): errors.append("DUPLICATE_CAR_NUMBER")
    valid_names=[x.strip() for x in names if isinstance(x,str) and x.strip()]
    if len(valid_names)!=len(set(valid_names)): errors.append("DUPLICATE_RIDER_NAME")
    # Do not assume a fixed rider count or contiguous 1..N field.
    source_expected=(binding or {}).get("expected_car_numbers") or []
    retrieved=(binding or {}).get("retrieved_car_numbers") or []
    if sorted(source_expected)!=sorted(retrieved): errors.append("SOURCE_RETRIEVED_CAR_SET_MISMATCH")
    if sorted(valid_cars)!=sorted(retrieved): errors.append("BOUND_CAR_SET_MISMATCH")
    return {"schema":"JFE-ENTRY-INTEGRITY/0.1","state":"AVAILABLE" if not errors else "ERROR",
      "entry_count":len(entries),"active_car_numbers":sorted(valid_cars),
      "source_expected_car_numbers":sorted(source_expected),"retrieved_car_numbers":sorted(retrieved),
      "unique_car_numbers":len(valid_cars)==len(set(valid_cars)),
      "unique_rider_names":len(valid_names)==len(set(valid_names)),
      "field_states":field_states,"errors":errors,"warnings":warnings,
      "withdrawal_state":"UNKNOWN","withdrawals":[],
      "note":"Withdrawal is not inferred without explicit source evidence; fixed rider count/contiguous car assumptions are prohibited."}

def live_entry_integrity(target_date):
    base=live_entry_binding(target_date); races=[]; recovery=[]
    for r in base.get("races",[]):
        b=r.get("entry_binding") or {}
        gate=validate_entry_integrity(b) if r.get("state")=="AVAILABLE" else {"schema":"JFE-ENTRY-INTEGRITY/0.1","state":"ERROR","errors":["ENTRY_BINDING_NOT_AVAILABLE"],"withdrawal_state":"UNKNOWN","withdrawals":[]}
        rec={"kaisai_date_id":r.get("kaisai_date_id"),"venue_code":r.get("venue_code"),"race_no":r.get("race_no"),
          "state":gate["state"],"entry_count":gate.get("entry_count",0),"active_car_numbers":gate.get("active_car_numbers",[]),
          "withdrawal_state":gate.get("withdrawal_state"),"errors":gate.get("errors",[]),"integrity":gate}
        if gate["state"]!="AVAILABLE": recovery.append({"kaisai_date_id":r.get("kaisai_date_id"),"race_no":r.get("race_no"),"reason":"ENTRY_INTEGRITY_FAILED","errors":gate.get("errors",[])})
        races.append(rec)
    ok=sum(r.get("state")=="AVAILABLE" for r in races)
    return {"schema":"JFE-LIVE-ENTRY-INTEGRITY-GATE/0.1","service":"JFE","version":VERSION,"target_date":target_date,
      "state":"AVAILABLE" if races and ok==len(races) else ("PARTIAL" if ok else "ERROR"),"acquired_at":now(),
      "race_count":len(races),"available_race_count":ok,"races":races,"recovery_queue":recovery,
      "fixed_rider_count_assumption":False,"fabricated_data":False}


# ===== DEV-B46 Entry Snapshot / Change Detection =====
ENTRY_SNAPSHOT_HISTORY={}

def _entry_snapshot_payload(race):
    gate=race.get("integrity") or {}
    fields=[]
    for f in gate.get("field_states",[]):
        fields.append({"car_no":f.get("car_no"),"rider_name":f.get("name"),"state":f.get("state")})
    return {"kaisai_date_id":race.get("kaisai_date_id"),"venue_code":race.get("venue_code"),
      "race_no":race.get("race_no"),"state":race.get("state"),"active_car_numbers":gate.get("active_car_numbers",[]),
      "withdrawal_state":gate.get("withdrawal_state","UNKNOWN"),"withdrawals":gate.get("withdrawals",[]),"entries":fields}

def _entry_snapshot_hash(payload):
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def compare_entry_snapshots(previous,current):
    if previous is None: return {"state":"BASELINE","changed":False,"changes":[]}
    changes=[]
    p={e.get("car_no"):e for e in previous.get("payload",{}).get("entries",[]) if isinstance(e.get("car_no"),int)}
    c={e.get("car_no"):e for e in current.get("payload",{}).get("entries",[]) if isinstance(e.get("car_no"),int)}
    for car in sorted(set(c)-set(p)): changes.append({"type":"ADDED","car_no":car,"current":c[car]})
    for car in sorted(set(p)-set(c)): changes.append({"type":"REMOVED","car_no":car,"previous":p[car],"withdrawal_inferred":False})
    for car in sorted(set(p)&set(c)):
        if p[car].get("rider_name")!=c[car].get("rider_name"):
            changes.append({"type":"RIDER_CHANGED","car_no":car,"previous":p[car].get("rider_name"),"current":c[car].get("rider_name")})
        for fld in ("state",):
            if p[car].get(fld)!=c[car].get(fld): changes.append({"type":"FIELD_CHANGED","car_no":car,"field":fld,"previous":p[car].get(fld),"current":c[car].get(fld)})
    # Withdrawal is only reported from explicit source evidence already present in the integrity gate.
    pw=previous.get("payload",{}).get("withdrawals",[]) or []; cw=current.get("payload",{}).get("withdrawals",[]) or []
    if pw!=cw: changes.append({"type":"FIELD_CHANGED","field":"withdrawals","previous":pw,"current":cw,"explicit_source_evidence":True})
    return {"state":"CHANGED" if changes else "UNCHANGED","changed":bool(changes),"changes":changes}

def live_entry_snapshot(target_date):
    base=live_entry_integrity(target_date); acquired=now(); races=[]; recovery=[]
    for race in base.get("races",[]):
        key="%s:%s"%(race.get("kaisai_date_id"),race.get("race_no"))
        payload=_entry_snapshot_payload(race); h=_entry_snapshot_hash(payload)
        sid="%s-%s-%s"%(race.get("kaisai_date_id"),race.get("race_no"),h[:16])
        snap={"snapshot_id":sid,"acquired_at":acquired,"source_hash":h,"payload":payload}
        hist=ENTRY_SNAPSHOT_HISTORY.setdefault(key,[]); prev=hist[-1] if hist else None
        diff=compare_entry_snapshots(prev,snap)
        # Append immutable content versions only; repeat acquisition remains an UNCHANGED observation.
        if prev is None or prev.get("source_hash")!=h: hist.append(snap)
        state="ERROR" if race.get("state")!="AVAILABLE" else ("CHANGED" if diff["changed"] else "AVAILABLE")
        rec={"kaisai_date_id":race.get("kaisai_date_id"),"venue_code":race.get("venue_code"),"race_no":race.get("race_no"),
          "state":state,"snapshot_id":sid,"acquired_at":acquired,"source_hash":h,"previous_snapshot_id":prev.get("snapshot_id") if prev else None,
          "change_state":diff["state"],"changes":diff["changes"],"active_car_numbers":payload["active_car_numbers"],
          "withdrawal_state":payload["withdrawal_state"],"withdrawals":payload["withdrawals"],"history_depth":len(hist)}
        if state=="ERROR": recovery.append({"kaisai_date_id":race.get("kaisai_date_id"),"race_no":race.get("race_no"),"reason":"ENTRY_SNAPSHOT_SOURCE_NOT_AVAILABLE"})
        races.append(rec)
    bad=sum(r.get("state")=="ERROR" for r in races); changed=sum(r.get("state")=="CHANGED" for r in races)
    state="ERROR" if races and bad==len(races) else ("PARTIAL" if bad else ("CHANGED" if changed else "AVAILABLE"))
    return {"schema":"JFE-LIVE-ENTRY-SNAPSHOT/0.1","service":"JFE","version":VERSION,"target_date":target_date,"state":state,
      "acquired_at":acquired,"race_count":len(races),"changed_race_count":changed,"error_race_count":bad,"races":races,
      "recovery_queue":recovery,"snapshot_policy":"IMMUTABLE_CONTENT_VERSION","withdrawal_inference":False,
      "fixed_rider_count_assumption":False,"fabricated_data":False}

# ===== DEV-B47 Pre-Race Entry Snapshot LOCK =====
PRE_RACE_LOCKS={}

def _lock_key(r):
    return "%s:%s"%(r.get("kaisai_date_id"),r.get("race_no"))

def _new_entry_lock(r, locked_at, relock_of=None):
    material={"kaisai_date_id":r.get("kaisai_date_id"),"venue_code":r.get("venue_code"),"race_no":r.get("race_no"),
      "entry_snapshot_id":r.get("snapshot_id"),"entry_source_hash":r.get("source_hash"),
      "active_car_numbers":list(r.get("active_car_numbers") or []),"withdrawal_state":r.get("withdrawal_state","UNKNOWN")}
    lock_hash=hashlib.sha256(json.dumps(material,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return {"lock_id":"%s-%s-lock-%s"%(r.get("kaisai_date_id"),r.get("race_no"),lock_hash[:16]),
      "locked_at":locked_at,"lock_state":"LOCKED","lock_scope":"ENTRY_ONLY","entry_snapshot_id":r.get("snapshot_id"),
      "entry_source_hash":r.get("source_hash"),"active_car_numbers":material["active_car_numbers"],
      "withdrawal_state":material["withdrawal_state"],"odds_locked":False,"scheduled_start_cutoff_enforced":False,
      "relock_of":relock_of,"invalidated_at":None,"invalidation_reason":None}

def live_pre_race_lock(target_date, force_relock=False):
    current=live_entry_snapshot(target_date); at=now(); out=[]; recovery=[]
    for r in current.get("races",[]):
        key=_lock_key(r); existing=PRE_RACE_LOCKS.get(key)
        if r.get("state")=="ERROR":
            out.append({"kaisai_date_id":r.get("kaisai_date_id"),"venue_code":r.get("venue_code"),"race_no":r.get("race_no"),
              "state":"ERROR","lock_state":"NOT_LOCKED","entry_snapshot_id":r.get("snapshot_id"),"errors":["ENTRY_SNAPSHOT_NOT_AVAILABLE"]})
            recovery.append({"kaisai_date_id":r.get("kaisai_date_id"),"race_no":r.get("race_no"),"reason":"ENTRY_SNAPSHOT_NOT_AVAILABLE"}); continue
        if existing is None:
            existing=_new_entry_lock(r,at); PRE_RACE_LOCKS[key]=existing
        elif existing.get("entry_snapshot_id")!=r.get("snapshot_id"):
            if force_relock:
                old_id=existing.get("lock_id"); existing=_new_entry_lock(r,at,relock_of=old_id); PRE_RACE_LOCKS[key]=existing
            else:
                existing=dict(existing); existing["lock_state"]="RELOCK_REQUIRED"; existing["invalidated_at"]=at
                existing["invalidation_reason"]="ENTRY_SNAPSHOT_CHANGED"; PRE_RACE_LOCKS[key]=existing
        elif existing.get("lock_state")=="RELOCK_REQUIRED" and force_relock:
            old_id=existing.get("lock_id"); existing=_new_entry_lock(r,at,relock_of=old_id); PRE_RACE_LOCKS[key]=existing
        rec={"kaisai_date_id":r.get("kaisai_date_id"),"venue_code":r.get("venue_code"),"race_no":r.get("race_no"),
          "state":"AVAILABLE" if existing.get("lock_state")=="LOCKED" else "CHANGED",**existing,
          "current_entry_snapshot_id":r.get("snapshot_id"),"current_entry_source_hash":r.get("source_hash")}
        out.append(rec)
    invalid=sum(x.get("lock_state")=="RELOCK_REQUIRED" for x in out); err=sum(x.get("state")=="ERROR" for x in out)
    state="ERROR" if out and err==len(out) else ("PARTIAL" if err else ("CHANGED" if invalid else "AVAILABLE"))
    return {"schema":"JFE-PRE-RACE-ENTRY-LOCK/0.1","service":"JFE","version":VERSION,"target_date":target_date,"state":state,
      "acquired_at":at,"race_count":len(out),"locked_race_count":sum(x.get("lock_state")=="LOCKED" for x in out),
      "relock_required_count":invalid,"error_race_count":err,"races":out,"recovery_queue":recovery,
      "lock_scope":"ENTRY_ONLY","silent_overwrite":False,"odds_locked":False,"scheduled_start_cutoff_enforced":False,
      "storage_mode":"PROCESS_MEMORY_VOLATILE","durable_across_restart":False,"fixed_rider_count_assumption":False,"fabricated_data":False}

# ===== DEV-B48 Market/Odds DOM Probe =====
def _odds_url_from_racedetail(url):
    """Use the already source-bound racedetail URL; only switch the official pageType view."""
    if not isinstance(url,str) or "/racedetail/" not in url: return None
    base=url.split("?",1)[0]
    return base+"?pageType=odds"

def odds_dom_probe(raw, active_car_numbers):
    """Diagnostic-only market probe. It never promotes numeric values without explicit bet-type context."""
    text=txt(raw); active=set(int(x) for x in (active_car_numbers or []) if isinstance(x,int) or str(x).isdigit())
    labels=[]
    for label,(key,legs) in BET_TYPES.items():
        if re.search(re.escape(label),text):
            item={"label":label,"bet_type":key,"legs":legs}
            if item not in labels: labels.append(item)
    classes=[]
    for m in re.finditer(r'class\s*=\s*["\']([^"\']+)["\']',raw,re.I):
        for c in m.group(1).split():
            if c not in classes and any(k in c.lower() for k in ("odd","rate","bet","waku","wheel","race")): classes.append(c)
    tables=[]
    for m in re.finditer(r"<table\b[^>]*>",raw,re.I):
        a=m.start(); end=raw.find("</table>",a); frag=raw[a:(end+8 if end!=-1 else min(len(raw),a+2500))]
        ft=txt(frag)
        if any(x["label"] in ft for x in labels) or re.search(r"\b\d{1,5}\.\d\b",ft):
            tables.append(_compact_html(frag,900))
        if len(tables)>=8: break
    stamps=re.findall(r"(20\d{2}[/-]\d{1,2}[/-]\d{1,2}\s+\d{1,2}:\d{2})現在",text)
    sections=parse_kd_odds_sections(raw,sorted(active)) if active else {k:{"state":"UNKNOWN","bet_type_bound":False,"data":[],"rejected":[]} for k in ("wide","quinella","exacta","trio","trifecta")}
    summary={}
    for k,v in sections.items():
        summary[k]={"state":v.get("state"),"bet_type_bound":bool(v.get("bet_type_bound")),"verified_odds_count":len(v.get("data",[])),"rejected_count":len(v.get("rejected",[])),"label_evidence":v.get("label_evidence")}
    return {"explicit_bet_type_labels":labels,"market_classes":classes[:80],"table_count":len(re.findall(r"<table\b",raw,re.I)),
      "candidate_table_samples":tables,"source_timestamp":stamps[-1] if stamps else None,"bet_type_summary":summary,
      "verified_odds_count":sum(x["verified_odds_count"] for x in summary.values()),"active_car_numbers":sorted(active)}

def _bounded_stage(name, seconds, fn):
    """Wall-clock guard that works inside ThreadingHTTPServer request threads."""
    started=time.time(); q=queue.Queue(maxsize=1)
    def worker():
        try: q.put(("COMPLETED",fn(),None),block=False)
        except Exception as e:
            try: q.put(("ERROR",None,e),block=False)
            except Exception: pass
    threading.Thread(target=worker,daemon=True,name="JFE-"+name).start()
    try:
        state,value,err=q.get(timeout=float(seconds))
        if state=="COMPLETED": return {"state":"COMPLETED","elapsed_ms":round((time.time()-started)*1000,1),"value":value}
        return {"state":"ERROR","elapsed_ms":round((time.time()-started)*1000,1),"error_type":type(err).__name__,"error":str(err)}
    except queue.Empty:
        return {"state":"TIMEOUT","elapsed_ms":round((time.time()-started)*1000,1),"error_type":"TimeoutError","error":"STAGE_TIMEOUT:"+name}

def live_odds_dom_probe(target_date):
    """B48.2: bounded stage diagnostics. Always return JSON within the endpoint time budget."""
    request_started=time.time(); recovery=[]; out=[]
    stages={"pre_race_lock":{"state":"NOT_STARTED"},"entry_binding":{"state":"NOT_STARTED"},"odds_fetch":{"state":"NOT_STARTED"}}
    diag={"lock_race_count":0,"locked_candidates":0,"source_bound_candidates":0,"identity_matches":0,"source_url_matches":0,"fetch_attempts":0,"fetch_successes":0}

    lock_stage=_bounded_stage("PRE_RACE_LOCK",12,lambda:live_pre_race_lock(target_date,False)); stages["pre_race_lock"]={k:v for k,v in lock_stage.items() if k!="value"}
    if lock_stage["state"]!="COMPLETED":
        recovery.append({"reason":"UPSTREAM_LOCK_"+lock_stage["state"],"error_type":lock_stage.get("error_type"),"error":lock_stage.get("error")})
        return {"schema":"JFE-LIVE-ODDS-DOM-PROBE/0.3","service":"JFE","version":VERSION,"target_date":target_date,"state":"ERROR","acquired_at":now(),"sample_count":0,"samples":[],"recovery_queue":recovery,"binding_diagnostics":diag,"stage_diagnostics":stages,"request_elapsed_ms":round((time.time()-request_started)*1000,1),"time_budget_seconds":30,"sample_policy":"FIRST_SUCCESSFULLY_SOURCE_BOUND_LOCKED_RACE_PER_VENUE","parser_promotion":"NONE_DIAGNOSTIC_ONLY","bet_type_inference":False,"invalid_combination_guard":True,"silent_drop":False,"always_respond_policy":True,"fabricated_data":False}
    locks=lock_stage["value"]; locked=[r for r in locks.get("races",[]) if r.get("lock_state")=="LOCKED"]
    diag["lock_race_count"]=len(locks.get("races",[])); diag["locked_candidates"]=len(locked)
    if not locked:
        recovery.append({"reason":"UPSTREAM_LOCK_ZERO_RACE","upstream_state":locks.get("state"),"upstream_race_count":len(locks.get("races",[])),"upstream_locked_count":locks.get("locked_race_count"),"upstream_error_count":locks.get("error_race_count")})
        return {"schema":"JFE-LIVE-ODDS-DOM-PROBE/0.3","service":"JFE","version":VERSION,"target_date":target_date,"state":"ERROR","acquired_at":now(),"sample_count":0,"samples":[],"recovery_queue":recovery,"binding_diagnostics":diag,"stage_diagnostics":stages,"request_elapsed_ms":round((time.time()-request_started)*1000,1),"time_budget_seconds":30,"sample_policy":"FIRST_SUCCESSFULLY_SOURCE_BOUND_LOCKED_RACE_PER_VENUE","parser_promotion":"NONE_DIAGNOSTIC_ONLY","bet_type_inference":False,"invalid_combination_guard":True,"silent_drop":False,"always_respond_policy":True,"fabricated_data":False}

    bind_stage=_bounded_stage("ENTRY_BINDING",10,lambda:live_entry_binding(target_date)); stages["entry_binding"]={k:v for k,v in bind_stage.items() if k!="value"}
    if bind_stage["state"]!="COMPLETED":
        recovery.append({"reason":"ENTRY_BINDING_"+bind_stage["state"],"error_type":bind_stage.get("error_type"),"error":bind_stage.get("error")})
        return {"schema":"JFE-LIVE-ODDS-DOM-PROBE/0.3","service":"JFE","version":VERSION,"target_date":target_date,"state":"ERROR","acquired_at":now(),"sample_count":0,"samples":[],"recovery_queue":recovery,"binding_diagnostics":diag,"stage_diagnostics":stages,"request_elapsed_ms":round((time.time()-request_started)*1000,1),"time_budget_seconds":30,"sample_policy":"FIRST_SUCCESSFULLY_SOURCE_BOUND_LOCKED_RACE_PER_VENUE","parser_promotion":"NONE_DIAGNOSTIC_ONLY","bet_type_inference":False,"invalid_combination_guard":True,"silent_drop":False,"always_respond_policy":True,"fabricated_data":False}
    binding=bind_stage["value"]; bound=[r for r in binding.get("races",[]) if r.get("race_url")]; diag["source_bound_candidates"]=len(bound)
    by_exact={(str(r.get("kaisai_date_id")),str(r.get("venue_code")),int(r.get("race_no"))):r for r in bound if r.get("race_no") is not None}
    by_vr={}
    for r in bound:
        if r.get("race_no") is not None: by_vr.setdefault((str(r.get("venue_code")),int(r.get("race_no"))),[]).append(r)
    seen=set(); candidate=None
    for r in locked:
        vc=str(r.get("venue_code")); kid=str(r.get("kaisai_date_id")); rn=int(r.get("race_no"))
        if vc in seen: continue
        match=by_exact.get((kid,vc,rn)); mode="EXACT_KAISAIDATE_VENUE_RACE"
        if match is None:
            cs=by_vr.get((vc,rn),[])
            if len(cs)==1: match=cs[0]; mode="VENUE_RACE_UNIQUE_FALLBACK"
        if match:
            diag["identity_matches"]+=1; source_url=match.get("race_url"); odds_url=_odds_url_from_racedetail(source_url)
            if odds_url:
                diag["source_url_matches"]+=1; candidate=(r,match,mode,odds_url); break
    if candidate is None:
        recovery.append({"reason":"NO_SOURCE_BOUND_ODDS_CANDIDATE"})
    else:
        r,match,mode,odds_url=candidate; kid=str(r.get("kaisai_date_id")); vc=str(r.get("venue_code")); rn=int(r.get("race_no")); diag["fetch_attempts"]=1
        def _one_fetch():
            q=urllib.request.Request(odds_url,headers={"User-Agent":"JFE-Odds-DOM-Probe/0.2","Accept-Encoding":"identity","Cache-Control":"no-cache"})
            with urllib.request.urlopen(q,timeout=5) as x: body=x.read(); status=getattr(x,"status",None); ctype=x.headers.get("Content-Type")
            return body,status,ctype
        fs=_bounded_stage("ODDS_FETCH",6,_one_fetch); stages["odds_fetch"]={k:v for k,v in fs.items() if k!="value"}
        rec={"kaisai_date_id":kid,"venue_code":vc,"race_no":rn,"state":"ERROR","entry_lock_id":r.get("lock_id"),"source_racedetail_url":match.get("race_url"),"source_binding_mode":mode,"odds_url":odds_url}
        if fs["state"]=="COMPLETED":
            body,status,ctype=fs["value"]; raw=body.decode("utf-8","replace"); d=odds_dom_probe(raw,r.get("active_car_numbers") or [])
            rec.update({"state":"AVAILABLE" if status==200 else "ERROR","http_status":status,"content_type":ctype,"byte_length":len(body),"content_sha256":hashlib.sha256(body).hexdigest(),"diagnostic":d})
            if status==200: diag["fetch_successes"]=1
        else:
            rec.update({"error_type":fs.get("error_type"),"error":fs.get("error")}); recovery.append({"reason":"ODDS_FETCH_"+fs["state"],"error_type":fs.get("error_type"),"error":fs.get("error")})
        out.append(rec)
    ok=sum(x.get("state")=="AVAILABLE" for x in out)
    state="AVAILABLE" if out and ok==len(out) else ("PARTIAL" if ok else "ERROR")
    return {"schema":"JFE-LIVE-ODDS-DOM-PROBE/0.3","service":"JFE","version":VERSION,"target_date":target_date,"state":state,"acquired_at":now(),"sample_count":len(out),"samples":out,"recovery_queue":recovery,"binding_diagnostics":diag,"stage_diagnostics":stages,"request_elapsed_ms":round((time.time()-request_started)*1000,1),"time_budget_seconds":30,"sample_policy":"FIRST_SOURCE_BOUND_LOCKED_RACE_GLOBAL_DIAGNOSTIC","parser_promotion":"NONE_DIAGNOSTIC_ONLY","bet_type_inference":False,"invalid_combination_guard":True,"silent_drop":False,"always_respond_policy":True,"fabricated_data":False}

# ===== DEV-B43.2 DOM Structure Probe =====
def _compact_html(x, limit=420):
    return re.sub(r"\s+"," ",x).strip()[:limit]

def dom_structure_probe(raw):
    """Bounded diagnostics only: expose structural evidence, never infer entries."""
    classes=[]
    for m in re.finditer(r'class\s*=\s*["\']([^"\']+)["\']',raw,re.I):
        for c in m.group(1).split():
            if c not in classes: classes.append(c)
    ids=[]
    for x in re.findall(r'id\s*=\s*["\']([^"\']+)["\']',raw,re.I):
        if x not in ids: ids.append(x)
    tables=[]
    for m in re.finditer(r"<table\b[^>]*>",raw,re.I):
        a=m.start(); end=raw.find("</table>",a)
        frag=raw[a:(end+8 if end!=-1 else min(len(raw),a+1800))]
        tables.append(_compact_html(frag,700))
        if len(tables)>=8: break
    # Search source text around likely entry/rider labels and profile-ish tokens.
    contexts=[]
    pats=[r"車番",r"選手名",r"選手",r"級班",r"競走得点",r"府県",r"期別",r"racer",r"senshu",r"profile"]
    for pat in pats:
        for m in re.finditer(pat,raw,re.I):
            a=max(0,m.start()-260); b=min(len(raw),m.end()+520)
            x=_compact_html(raw[a:b],650)
            if x and x not in contexts: contexts.append(x)
            if len(contexts)>=16: break
        if len(contexts)>=16: break
    # Attribute names can reveal JS/data binding without dumping the body.
    data_attrs=[]
    for x in re.findall(r"\b(data-[a-zA-Z0-9_-]+)\s*=",raw):
        if x not in data_attrs: data_attrs.append(x)
    return {"table_count":len(re.findall(r"<table\b",raw,re.I)),
            "tr_count":len(re.findall(r"<tr\b",raw,re.I)),
            "td_count":len(re.findall(r"<td\b",raw,re.I)),
            "sample_classes":classes[:80],"sample_ids":ids[:40],
            "data_attributes":data_attrs[:40],"table_samples":tables,
            "keyword_contexts":contexts}

def live_dom_probe(target_date):
    """Fetch only one source-bound race per verified venue to keep output compact."""
    base=live_race_verification(target_date)
    out=[]; recovery=[]
    for venue in base.get("venues",[]):
        if venue.get("state")!="VERIFIED_VENUE" or not venue.get("races"): continue
        race_no=venue["races"][0]
        identity={}
        for ev in venue.get("evidence",[]): identity.update(ev.get("race_identity_evidence") or {})
        urls=identity.get(race_no) or identity.get(str(race_no)) or []
        url=canonical_racedetail_url(urls)
        rec={"kaisai_date_id":venue.get("kaisai_date_id"),"venue_code":venue.get("venue_code"),
             "race_no":race_no,"race_url":url,"state":"UNKNOWN"}
        if not url:
            rec.update({"state":"ERROR","error_type":"RACE_BINDING_ERROR"}); out.append(rec); continue
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"JFE-DOM-Probe/0.1",
                "Accept-Encoding":"identity","Cache-Control":"no-cache"})
            with urllib.request.urlopen(q,timeout=20) as x:
                body=x.read(); status=getattr(x,"status",None)
            raw=body.decode("utf-8","replace")
            rec.update({"state":"AVAILABLE" if status==200 else "ERROR","http_status":status,
                        "byte_length":len(body),"content_sha256":hashlib.sha256(body).hexdigest(),
                        "dom":dom_structure_probe(raw)})
        except Exception as e:
            rec.update({"state":"ERROR","error_type":type(e).__name__,"error":str(e)})
            recovery.append({"kaisai_date_id":venue.get("kaisai_date_id"),"race_no":race_no,
                             "reason":"DOM_PROBE_FETCH_ERROR"})
        out.append(rec)
    return {"schema":"JFE-DOM-STRUCTURE-PROBE/0.1","service":"JFE","version":VERSION,
            "target_date":target_date,"state":"AVAILABLE" if out and all(x.get("state")=="AVAILABLE" for x in out) else "PARTIAL",
            "acquired_at":now(),"sample_policy":"FIRST_SOURCE_BOUND_RACE_PER_VERIFIED_VENUE",
            "sample_count":len(out),"samples":out,"recovery_queue":recovery,
            "parser_promotion":"NONE_DIAGNOSTIC_ONLY","fabricated_data":False}

# ===== DEV-B43.1 Compact Entry Diagnostic =====
def compact_entry_diagnostic(target_date):
    """Run B43, but return only the evidence needed to design the binding parser."""
    full=live_entry_acquisition(target_date)
    rows=[]
    totals={"races":0,"http_200":0,"racer_links":0,"car_token_races":0,"errors":0}
    for r in full.get("races",[]):
        pr=r.get("entry_probe") or {}
        row={"kaisai_date_id":r.get("kaisai_date_id"),"venue_code":r.get("venue_code"),
             "race_no":r.get("race_no"),"state":r.get("state"),
             "entry_binding_state":r.get("entry_binding_state"),
             "http_status":r.get("http_status"),
             "racer_link_count":pr.get("racer_link_count",0),
             "car_tokens":pr.get("car_tokens",[])}
        links=pr.get("racer_links") or []
        if links: row["sample_racer_links"]=links[:3]
        ctx=pr.get("contexts") or []
        if ctx: row["sample_context"]=ctx[0][:350]
        if r.get("error_type"): row["error_type"]=r.get("error_type")
        rows.append(row)
        totals["races"]+=1
        totals["http_200"]+=1 if r.get("http_status")==200 else 0
        totals["racer_links"]+=pr.get("racer_link_count",0) or 0
        totals["car_token_races"]+=1 if pr.get("car_tokens") else 0
        totals["errors"]+=1 if r.get("state")=="ERROR" else 0
    return {"schema":"JFE-COMPACT-ENTRY-DIAGNOSTIC/0.1","service":"JFE","version":VERSION,
            "target_date":target_date,"state":full.get("state"),"acquired_at":full.get("acquired_at"),
            "verified_venue_count":full.get("verified_venue_count",0),"totals":totals,
            "races":rows,"recovery_count":len(full.get("recovery_queue",[])),
            "fabricated_data":False}

# ===== DEV-B43 Entry Acquisition Probe =====
def canonical_racedetail_url(identity_urls):
    for u in identity_urls or []:
        if re.search(r"/racedetail/\d{16}/?$",u):
            return u
    for u in identity_urls or []:
        if "/racedetail/" in u and "pageType=" not in u:
            return u.split("?")[0]
    return None

def entry_structure_probe(raw):
    hrefs=re.findall(r"href\s*=\s*[\"']([^\"']+)[\"']",raw,re.I)
    racer_links=[]
    for h in hrefs:
        hl=h.lower()
        if any(k in hl for k in ("racer_detail","racer-detail","racer/detail","senshu","player")):
            u=_abs_kd_url(h)
            if u not in racer_links: racer_links.append(u)
    contexts=[]
    for m in re.finditer(r"(?:Racer_Detail|racer|senshu|選手)",raw,re.I):
        a=max(0,m.start()-180); b=min(len(raw),m.end()+260)
        x=re.sub(r"\s+"," ",raw[a:b]).strip()
        if x and x not in contexts: contexts.append(x[:500])
        if len(contexts)>=20: break
    car_tokens=sorted({int(x) for x in re.findall(r"(?:車番|carNo|car_no)[^0-9]{0,20}([1-9]\d?)",raw,re.I)})
    return {"href_count":len(hrefs),"racer_link_count":len(racer_links),
            "racer_links":racer_links[:40],"car_tokens":car_tokens,"contexts":contexts}

def live_entry_acquisition(target_date):
    base=live_race_verification(target_date)
    if base.get("state")=="ERROR":
        return {"schema":"JFE-LIVE-ENTRY-ACQUISITION/0.1","service":"JFE","version":VERSION,
                "target_date":target_date,"state":"ERROR","upstream":base,"races":[],
                "recovery_queue":[],"fabricated_data":False}
    races=[]; recovery=[]
    for venue in base.get("venues",[]):
        if venue.get("state")!="VERIFIED_VENUE": continue
        identity={}
        for ev in venue.get("evidence",[]):
            identity.update(ev.get("race_identity_evidence") or {})
        for race_no in venue.get("races",[]):
            urls=identity.get(race_no) or identity.get(str(race_no)) or []
            url=canonical_racedetail_url(urls)
            rec={"kaisai_date_id":venue["kaisai_date_id"],"venue_code":venue["venue_code"],
                 "race_no":race_no,"race_url":url,"state":"UNKNOWN"}
            if not url:
                rec["state"]="ERROR"; rec["error_type"]="RACE_BINDING_ERROR"
                recovery.append({"kaisai_date_id":venue["kaisai_date_id"],"race_no":race_no,
                                 "reason":"CANONICAL_RACE_URL_MISSING"})
                races.append(rec); continue
            try:
                q=urllib.request.Request(url,headers={"User-Agent":"JFE-Entry-Acquisition/0.1",
                    "Accept-Encoding":"identity","Cache-Control":"no-cache"})
                with urllib.request.urlopen(q,timeout=20) as x:
                    body=x.read(); status=getattr(x,"status",None); ctype=x.headers.get("Content-Type")
                raw=body.decode("utf-8","replace")
                probe=entry_structure_probe(raw)
                rec.update({"http_status":status,"content_type":ctype,"byte_length":len(body),
                            "content_sha256":hashlib.sha256(body).hexdigest(),"entry_probe":probe,
                            "state":"PARTIAL" if status==200 else "ERROR",
                            "entry_binding_state":"PROBE_ONLY"})
                if status!=200:
                    recovery.append({"kaisai_date_id":venue["kaisai_date_id"],"race_no":race_no,
                                     "reason":"HTTP_ERROR"})
            except Exception as e:
                rec.update({"state":"ERROR","entry_binding_state":"ERROR",
                            "error_type":type(e).__name__,"error":str(e)})
                recovery.append({"kaisai_date_id":venue["kaisai_date_id"],"race_no":race_no,
                                 "reason":"ENTRY_FETCH_ERROR"})
            races.append(rec)
    ok=sum(1 for r in races if r.get("http_status")==200)
    return {"schema":"JFE-LIVE-ENTRY-ACQUISITION/0.1","service":"JFE","version":VERSION,
            "target_date":target_date,"state":"PARTIAL" if races else "UNKNOWN","acquired_at":now(),
            "transport":"RENDER_HTTP","verified_venue_count":base.get("verified_venue_count",0),
            "race_count":len(races),"http_200_race_count":ok,"races":races,
            "recovery_queue":recovery,"entry_gate":"ENTRY_FIRST_PROBE_ONLY","fabricated_data":False}

# ===== DEV-B42 Race Identity Gate =====
def race_identity_evidence(raw, meeting_id):
    """Accept race numbers only when bound to a race-specific source link/reference."""
    hrefs=re.findall(r"href\s*=\s*[\"']([^\"']+)[\"']",raw,re.I)
    evidence={}
    for h in hrefs:
        if "race" not in h.lower(): continue
        # Strong form: meeting id followed by a two-digit race suffix.
        for m in re.finditer(re.escape(meeting_id)+r"(\d{2})(?:[/?&#\"']|$)",h,re.I):
            n=int(m.group(1))
            if 1 <= n <= 99:
                evidence.setdefault(n,[]).append(_abs_kd_url(h))
        # Query/path race number is accepted only when the same href is meeting-bound.
        if meeting_id in h:
            for m in re.finditer(r"(?:race(?:no|num|number)?|r)[=/_-]?0?(\d{1,2})(?:\D|$)",h,re.I):
                n=int(m.group(1))
                if 1 <= n <= 99:
                    evidence.setdefault(n,[]).append(_abs_kd_url(h))
    # Deduplicate evidence URLs per race.
    for n in list(evidence):
        evidence[n]=list(dict.fromkeys(evidence[n]))
    return evidence

def enumerate_bound_races(raw,meeting_id):
    ev=race_identity_evidence(raw,meeting_id)
    return sorted(ev),ev

# ===== DEV-B41 Race Verification / Dynamic Race Enumeration =====
def _abs_kd_url(href):
    if href.startswith("https://") or href.startswith("http://"): return href
    if href.startswith("//"): return "https:"+href
    if href.startswith("/"): return "https://keirin.kdreams.jp"+href
    return "https://keirin.kdreams.jp/"+href

def discover_meeting_racecard_urls(raw,target_date):
    """Bind target-date meeting IDs to source-published KDreams racecard URLs."""
    compact=target_date.replace("-","")
    hrefs=re.findall(r"href\s*=\s*[\"']([^\"']+)[\"']",raw,re.I)
    found={}
    for h in hrefs:
        if "racecard" not in h.lower(): continue
        mids=re.findall(r"(\d{14})",h)
        for mid in mids:
            if mid[2:10] != compact: continue
            found.setdefault(mid,[])
            u=_abs_kd_url(h)
            if u not in found[mid]: found[mid].append(u)
    return found

def enumerate_races_from_racecard(raw,meeting_id):
    """Enumerate race numbers from page evidence; never assumes 12 races."""
    nums=set()
    # Race-specific 14/16-digit identifiers and explicit race labels/links.
    for tok in re.findall(r"\d{14,16}",raw):
        if tok.startswith(meeting_id):
            tail=tok[len(meeting_id):]
            if tail.isdigit() and tail:
                n=int(tail[-2:])
                if 1 <= n <= 99: nums.add(n)
    for m in re.findall(r"(?:race|r)[/_=-]?0?(\d{1,2})(?:\D|$)",raw,re.I):
        n=int(m)
        if 1 <= n <= 99: nums.add(n)
    for m in re.findall(r"(\d{1,2})\s*R\b",raw,re.I):
        n=int(m)
        if 1 <= n <= 99: nums.add(n)
    return sorted(nums)

def live_race_verification(target_date):
    root="https://keirin.kdreams.jp/"; acquired_at=now()
    try:
        rq=urllib.request.Request(root,headers={"User-Agent":"JFE-Race-Verification/0.1",
            "Accept-Encoding":"identity","Cache-Control":"no-cache"})
        with urllib.request.urlopen(rq,timeout=20) as x:
            root_body=x.read()
        root_raw=root_body.decode("utf-8","replace")
        candidates=discover_meeting_racecard_urls(root_raw,target_date)
        venues=[]; recovery=[]
        for mid,urls in candidates.items():
            rec={"kaisai_date_id":mid,"venue_code":mid[:2],"bound_date":mid[2:10],
                 "source_racecard_urls":urls,"state":"DISCOVERED_CANDIDATE","races":[]}
            verified=False
            for url in urls:
                try:
                    q=urllib.request.Request(url,headers={"User-Agent":"JFE-Race-Verification/0.1",
                        "Accept-Encoding":"identity","Cache-Control":"no-cache"})
                    with urllib.request.urlopen(q,timeout=20) as x:
                        body=x.read(); status=getattr(x,"status",None)
                    raw=body.decode("utf-8","replace")
                    races,race_ev=enumerate_bound_races(raw,mid)
                    ev={"url":url,"http_status":status,"byte_length":len(body),
                        "content_sha256":hashlib.sha256(body).hexdigest(),"race_numbers":races,"race_identity_evidence":race_ev}
                    rec.setdefault("evidence",[]).append(ev)
                    if status==200 and races:
                        rec["state"]="VERIFIED_VENUE"; rec["races"]=races
                        rec["race_count"]=len(races); verified=True; break
                except Exception as e:
                    rec.setdefault("errors",[]).append({"url":url,"error_type":type(e).__name__,"error":str(e)})
            if not verified:
                rec["race_count"]=0
                recovery.append({"kaisai_date_id":mid,"reason":"RACE_VERIFICATION_INCOMPLETE"})
            venues.append(rec)
        verified_count=sum(1 for v in venues if v["state"]=="VERIFIED_VENUE")
        return {"schema":"JFE-LIVE-RACE-VERIFICATION/0.1","service":"JFE","version":VERSION,
                "target_date":target_date,"state":"AVAILABLE" if verified_count else "UNKNOWN",
                "source_url":root,"acquired_at":acquired_at,"transport":"RENDER_HTTP",
                "root_byte_length":len(root_body),"root_content_sha256":hashlib.sha256(root_body).hexdigest(),
                "candidate_count":len(venues),"verified_venue_count":verified_count,
                "venues":venues,"recovery_queue":recovery,"fabricated_data":False}
    except Exception as e:
        return {"schema":"JFE-LIVE-RACE-VERIFICATION/0.1","service":"JFE","version":VERSION,
                "target_date":target_date,"state":"ERROR","source_url":root,"acquired_at":acquired_at,
                "transport":"RENDER_HTTP","error_type":type(e).__name__,"error":str(e),
                "venues":[],"recovery_queue":[],"fabricated_data":False}

# ===== DEV-B40 Target-Date Meeting ID Discovery =====
def discover_target_meeting_ids(raw,target_date):
    compact=target_date.replace("-","")
    hrefs=re.findall(r"href\s*=\s*[\"']([^\"']+)[\"']",raw,re.I)
    ids=[]
    for h in hrefs:
        for mid in re.findall(r"(?:kaisaiDateId=|/)(\d{14})(?:[/?&#\"']|$)",h,re.I):
            if mid[2:10]==compact:
                ids.append(mid)
    for mid in re.findall(r"kaisaiDateId[^0-9]{0,20}(\d{14})",raw,re.I):
        if mid[2:10]==compact:
            ids.append(mid)
    uniq=[]; seen=set()
    for mid in ids:
        if mid not in seen:
            seen.add(mid); uniq.append(mid)
    return {"target_date":target_date,"meeting_ids":uniq,"meeting_count":len(uniq),"href_count":len(hrefs)}

def live_meeting_discovery(target_date):
    source_url="https://keirin.kdreams.jp/"; acquired_at=now(); t=time.time()
    try:
        q=urllib.request.Request(source_url,headers={"User-Agent":"JFE-Meeting-Discovery/0.1",
            "Accept-Encoding":"identity","Cache-Control":"no-cache"})
        with urllib.request.urlopen(q,timeout=20) as x:
            body=x.read(); status=getattr(x,"status",None); ctype=x.headers.get("Content-Type")
        raw=body.decode("utf-8","replace")
        parsed=discover_target_meeting_ids(raw,target_date)
        meetings=[{"kaisai_date_id":mid,"venue_code":mid[:2],"bound_date":mid[2:10],
                   "meeting_suffix":mid[10:],"state":"DISCOVERED_CANDIDATE"} for mid in parsed["meeting_ids"]]
        return {"schema":"JFE-LIVE-MEETING-DISCOVERY/0.1","service":"JFE","version":VERSION,
                "target_date":target_date,"state":"AVAILABLE" if meetings else "UNKNOWN",
                "source_url":source_url,"acquired_at":acquired_at,"transport":"RENDER_HTTP",
                "http_status":status,"content_type":ctype,"byte_length":len(body),
                "content_sha256":hashlib.sha256(body).hexdigest(),"elapsed_ms":round((time.time()-t)*1000,1),
                "href_count":parsed["href_count"],"meeting_count":len(meetings),"meetings":meetings,
                "verification_state":"CANDIDATE_ONLY","fabricated_data":False}
    except Exception as e:
        return {"schema":"JFE-LIVE-MEETING-DISCOVERY/0.1","service":"JFE","version":VERSION,
                "target_date":target_date,"state":"ERROR","source_url":source_url,
                "acquired_at":acquired_at,"transport":"RENDER_HTTP","error_type":type(e).__name__,
                "error":str(e),"meetings":[],"meeting_count":0,"fabricated_data":False}

# ===== DEV-B39 Live Response Body Diagnostics =====
def live_body_diagnostics(target_date):
    source_url="https://keirin.kdreams.jp/"; acquired_at=now(); t=time.time()
    try:
        q=urllib.request.Request(source_url,headers={
            "User-Agent":"JFE-Body-Diagnostics/0.1",
            "Accept":"text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Encoding":"identity","Cache-Control":"no-cache"})
        with urllib.request.urlopen(q,timeout=20) as x:
            body=x.read(); status=getattr(x,"status",None)
            headers={k.lower():v for k,v in x.headers.items()}
        raw=body.decode("utf-8","replace"); low=raw.lower()
        title_m=re.search(r"<title[^>]*>(.*?)</title>",raw,re.I|re.S)
        title=re.sub(r"\s+"," ",title_m.group(1)).strip()[:300] if title_m else None
        counts={"html_open":len(re.findall(r"<html\b",raw,re.I)),
                "script_open":len(re.findall(r"<script\b",raw,re.I)),
                "anchor_open":len(re.findall(r"<a\b",raw,re.I)),
                "href_attr":len(re.findall(r"\bhref\s*=",raw,re.I)),
                "form_open":len(re.findall(r"<form\b",raw,re.I)),
                "iframe_open":len(re.findall(r"<iframe\b",raw,re.I))}
        keywords={k:low.count(k.lower()) for k in
                  ["racecard","odds","競輪","keirin","kdreams","cloudflare","javascript","__next_data__"]}
        excerpt=re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]+"," ",raw[:1800])
        url_refs=re.findall(r"https?://[^\s\\\"'<>]+",raw,re.I)
        api_like=[]; seen=set()
        for u in url_refs:
            if u not in seen and any(k in u.lower() for k in ("api","race","odds","keirin","kdreams")):
                seen.add(u); api_like.append(u)
        return {"schema":"JFE-LIVE-BODY-DIAGNOSTICS/0.1","service":"JFE","version":VERSION,
                "target_date":target_date,"state":"AVAILABLE","source_url":source_url,
                "acquired_at":acquired_at,"transport":"RENDER_HTTP","http_status":status,
                "content_type":headers.get("content-type"),"content_encoding":headers.get("content-encoding"),
                "content_length_header":headers.get("content-length"),"byte_length":len(body),
                "content_sha256":hashlib.sha256(body).hexdigest(),"elapsed_ms":round((time.time()-t)*1000,1),
                "title":title,"tag_counts":counts,"keyword_counts":keywords,"body_prefix":excerpt,
                "api_like_url_count":len(api_like),"api_like_urls":api_like[:40],
                "replacement_char_count":raw.count("\ufffd"),"fabricated_data":False,"diagnostic_only":True}
    except Exception as e:
        return {"schema":"JFE-LIVE-BODY-DIAGNOSTICS/0.1","service":"JFE","version":VERSION,
                "target_date":target_date,"state":"ERROR","source_url":source_url,
                "acquired_at":acquired_at,"transport":"RENDER_HTTP","error_type":type(e).__name__,
                "error":str(e),"fabricated_data":False,"diagnostic_only":True}

# ===== DEV-B38 Live Discovery Structure Probe =====
def live_discovery_probe(target_date):
    source_url="https://keirin.kdreams.jp/"; acquired_at=now(); t=time.time()
    try:
        q=urllib.request.Request(source_url,headers={"User-Agent":"JFE-Discovery-Probe/0.1","Cache-Control":"no-cache"})
        with urllib.request.urlopen(q,timeout=20) as x:
            body=x.read(); status=getattr(x,"status",None); ctype=x.headers.get("Content-Type")
        raw=body.decode("utf-8","replace")
        hrefs=re.findall(r"href\\s*=\\s*[\"']([^\"']+)[\"']",raw,re.I)
        uniq=[]; seen=set()
        for h in hrefs:
            if h not in seen: seen.add(h); uniq.append(h)
        date_compact=target_date.replace("-","")
        relevant=[h for h in uniq if ("racecard" in h.lower() or "keirin" in h.lower() or date_compact in h)]
        tokens=sorted(set(re.findall(r"\\d{14}",raw)))
        date_tokens=[x for x in tokens if date_compact in x]
        return {"schema":"JFE-LIVE-DISCOVERY-PROBE/0.1","service":"JFE","version":VERSION,
                "target_date":target_date,"state":"AVAILABLE","source_url":source_url,"acquired_at":acquired_at,
                "transport":"RENDER_HTTP","http_status":status,"content_type":ctype,"byte_length":len(body),
                "content_sha256":hashlib.sha256(body).hexdigest(),"elapsed_ms":round((time.time()-t)*1000,1),
                "href_count":len(hrefs),"unique_href_count":len(uniq),"relevant_href_count":len(relevant),
                "relevant_hrefs":relevant[:80],"date_token_count":len(date_tokens),"date_tokens":date_tokens[:80],
                "truncated":len(relevant)>80 or len(date_tokens)>80,"fabricated_data":False}
    except Exception as e:
        return {"schema":"JFE-LIVE-DISCOVERY-PROBE/0.1","service":"JFE","version":VERSION,
                "target_date":target_date,"state":"ERROR","source_url":source_url,"acquired_at":acquired_at,
                "transport":"RENDER_HTTP","error_type":type(e).__name__,"error":str(e),
                "relevant_hrefs":[],"date_tokens":[],"fabricated_data":False}

# ===== DEV-B37 Render Live Daily Discovery =====
def live_daily_discovery(target_date):
    """Use the proven Render HTTP path, then discover venue candidates without hardcoded venue counts."""
    source_url="https://keirin.kdreams.jp/"
    acquired_at=now(); t=time.time()
    try:
        q=urllib.request.Request(source_url,headers={"User-Agent":"JFE-Live-Discovery/0.1","Cache-Control":"no-cache"})
        with urllib.request.urlopen(q,timeout=20) as x:
            body=x.read(); status=getattr(x,"status",None); ctype=x.headers.get("Content-Type")
        raw=body.decode("utf-8","replace")
        # Reuse B4 discovery first; preserve UNKNOWN rather than guessing if page does not expose bound venue metadata.
        parsed=discover_venues_from_html(raw,target_date)
        venues=parsed.get("venues",[])
        state="AVAILABLE" if venues else "UNKNOWN"
        return {"schema":"JFE-LIVE-DAILY-DISCOVERY/0.1","service":"JFE","version":VERSION,
                "target_date":target_date,"state":state,"source_url":source_url,
                "acquired_at":acquired_at,"transport":"RENDER_HTTP","http_status":status,
                "content_type":ctype,"byte_length":len(body),"content_sha256":hashlib.sha256(body).hexdigest(),
                "elapsed_ms":round((time.time()-t)*1000,1),"venues":venues,
                "venue_count":len(venues),"parser_state":parsed.get("state"),
                "parser_errors":parsed.get("errors",[]),"fabricated_data":False}
    except Exception as e:
        return {"schema":"JFE-LIVE-DAILY-DISCOVERY/0.1","service":"JFE","version":VERSION,
                "target_date":target_date,"state":"ERROR","source_url":source_url,
                "acquired_at":acquired_at,"transport":"RENDER_HTTP","error_type":type(e).__name__,
                "error":str(e),"venues":[],"venue_count":0,"fabricated_data":False}

class S(BaseHTTPRequestHandler):
 def j(self,c,o,head=False):
  z=json.dumps(o,ensure_ascii=False).encode();self.send_response(c);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(z)));self.end_headers()
  if not head:self.wfile.write(z)
 def do_HEAD(self):self.j(200,{"service":"JFE","version":VERSION,"status":"UP"},True)
 def do_GET(self):
  p=unquote(self.path.split("?")[0])
  if p in("/","/health"):return self.j(200,{"service":"JFE","version":VERSION,"status":"UP","mode":"qualification","uptime_s":round(time.time()-START,2)})
  if p=="/v1/diagnostics":return self.j(200,{"version":VERSION,"snapshots":SNAPSHOTS,"hash_owners":HASH_OWNER,"health":HEALTH})
  odp=re.fullmatch(r"/v1/odds-dom-probe/(\d{4}-\d{2}-\d{2})",p)
  if odp:
   result=live_odds_dom_probe(odp.group(1))
   return self.j(200 if result["state"]!="ERROR" else 503,result)
  prl=re.fullmatch(r"/v1/pre-race-lock/(\d{4}-\d{2}-\d{2})",p)
  if prl:
   result=live_pre_race_lock(prl.group(1),False)
   return self.j(200 if result["state"]!="ERROR" else 503,result)
  prr=re.fullmatch(r"/v1/pre-race-relock/(\d{4}-\d{2}-\d{2})",p)
  if prr:
   result=live_pre_race_lock(prr.group(1),True)
   return self.j(200 if result["state"]!="ERROR" else 503,result)
  esnap=re.fullmatch(r"/v1/entry-snapshot/(\d{4}-\d{2}-\d{2})",p)
  if esnap:
   result=live_entry_snapshot(esnap.group(1))
   return self.j(200 if result["state"]!="ERROR" else 503,result)
  ei=re.fullmatch(r"/v1/entry-integrity/(\d{4}-\d{2}-\d{2})",p)
  if ei:
   result=live_entry_integrity(ei.group(1))
   return self.j(200 if result["state"]!="ERROR" else 503,result)
  eb=re.fullmatch(r"/v1/entry-binding/(\d{4}-\d{2}-\d{2})",p)
  if eb:
   result=compact_entry_binding(eb.group(1))
   return self.j(200 if result["state"]!="ERROR" else 503,result)
  dp=re.fullmatch(r"/v1/dom-probe/(\d{4}-\d{2}-\d{2})",p)
  if dp:
   result=live_dom_probe(dp.group(1))
   return self.j(200 if result["state"]!="ERROR" else 503,result)
  es=re.fullmatch(r"/v1/entry-summary/(\d{4}-\d{2}-\d{2})",p)
  if es:
   result=compact_entry_diagnostic(es.group(1))
   return self.j(200 if result["state"]!="ERROR" else 503,result)
  ea=re.fullmatch(r"/v1/entry-acquisition/(\d{4}-\d{2}-\d{2})",p)
  if ea:
   result=live_entry_acquisition(ea.group(1))
   return self.j(200 if result["state"]!="ERROR" else 503,result)
  rg=re.fullmatch(r"/v1/race-identity-gate/(\d{4}-\d{2}-\d{2})",p)
  if rg:
   result=live_race_verification(rg.group(1))
   result["schema"]="JFE-LIVE-RACE-IDENTITY-GATE/0.1"
   result["identity_gate"]="B42_SOURCE_LINK_BOUND"
   return self.j(200 if result["state"]!="ERROR" else 503,result)
  rv=re.fullmatch(r"/v1/race-verification/(\d{4}-\d{2}-\d{2})",p)
  if rv:
   result=live_race_verification(rv.group(1))
   return self.j(200 if result["state"]!="ERROR" else 503,result)
  mm=re.fullmatch(r"/v1/meeting-discovery/(\d{4}-\d{2}-\d{2})",p)
  if mm:
   result=live_meeting_discovery(mm.group(1))
   return self.j(200 if result["state"]!="ERROR" else 503,result)
  bm=re.fullmatch(r"/v1/body-diagnostics/(\d{4}-\d{2}-\d{2})",p)
  if bm:
   result=live_body_diagnostics(bm.group(1))
   return self.j(200 if result["state"]=="AVAILABLE" else 503,result)
  pm=re.fullmatch(r"/v1/discovery-probe/(\d{4}-\d{2}-\d{2})",p)
  if pm:
   result=live_discovery_probe(pm.group(1))
   return self.j(200 if result["state"]=="AVAILABLE" else 503,result)
  dm=re.fullmatch(r"/v1/discovery/(\d{4}-\d{2}-\d{2})",p)
  if dm:
   result=live_daily_discovery(dm.group(1))
   return self.j(200 if result["state"]!="ERROR" else 503,result)
  if p=="/v1/acquisition/test":
   url=os.getenv("JFE_ACQUISITION_TEST_URL","https://keirin.kdreams.jp/")
   acquired_at=now(); t=time.time()
   try:
    q=urllib.request.Request(url,headers={"User-Agent":"JFE-Acquisition-Test/0.3","Cache-Control":"no-cache"})
    with urllib.request.urlopen(q,timeout=20) as x:
     body=x.read(); status=getattr(x,"status",None); ctype=x.headers.get("Content-Type")
    result={"schema":"JFE-ACQUISITION-EVIDENCE/1.2","service":"JFE","version":VERSION,
            "state":"AVAILABLE","source_url":url,"acquired_at":acquired_at,"transport":"RENDER_HTTP",
            "http_status":status,"content_type":ctype,"byte_length":len(body),
            "content_sha256":hashlib.sha256(body).hexdigest(),"elapsed_ms":round((time.time()-t)*1000,1),
            "fabricated_data":False}
    print("JFE_ACQUISITION_RESULT "+json.dumps(result,ensure_ascii=False),flush=True)
    return self.j(200,result)
   except Exception as e:
    result={"schema":"JFE-ACQUISITION-EVIDENCE/1.2","service":"JFE","version":VERSION,
            "state":"ERROR","source_url":url,"acquired_at":acquired_at,"transport":"RENDER_HTTP",
            "error_type":type(e).__name__,"error":str(e),"fabricated_data":False}
    print("JFE_ACQUISITION_RESULT "+json.dumps(result,ensure_ascii=False),flush=True)
    return self.j(503,result)
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
# DEV-B36: server start moved to EOF so all integrated modules load before serving.

# ===== IC1.4-A Daily Discovery (DEV-B4) =====
class DiscoveredRace:
    def __init__(self,race_no,url="",start_time="",state="AVAILABLE",evidence=None):
        self.race_no=race_no; self.url=url; self.start_time=start_time; self.state=state; self.evidence=evidence or {}
    @property
    def __dict__(self):
        return {"race_no":self.race_no,"url":self.url,"start_time":self.start_time,"state":self.state,"evidence":self.evidence}

class DiscoveredVenue:
    def __init__(self,venue_name,venue_code="",meeting_url="",state="AVAILABLE",races=None,evidence=None):
        self.venue_name=venue_name; self.venue_code=venue_code; self.meeting_url=meeting_url; self.state=state; self.races=races or []; self.evidence=evidence or {}
    @property
    def __dict__(self):
        return {"venue_name":self.venue_name,"venue_code":self.venue_code,"meeting_url":self.meeting_url,"state":self.state,"races":self.races,"evidence":self.evidence}

def _norm_space(x):
    return re.sub(r"\s+"," ",str(x or "")).strip()

def discover_venues_from_html(html,target_date):
    if not html or not _norm_space(html):
        return {"state":"UNKNOWN","venues":[],"errors":["EMPTY_DAILY_DOCUMENT"]}
    out={}
    pat = r'(?:data-venue-code=["\']?(\d{1,3})["\']?[^>]*data-venue-name=["\']([^"\\\']+)["\']|data-venue-name=["\']([^"\\\']+)["\'][^>]*data-venue-code=["\']?(\d{1,3})["\']?)'
    for m in re.finditer(pat,html,re.I):
        code=m.group(1) or m.group(4) or ""
        name=_norm_space(m.group(2) or m.group(3))
        if name: out[(code,name)]={"venue_name":name,"venue_code":code}
    venues=[DiscoveredVenue(**v,evidence={"target_date":target_date,"discovery":"daily_schedule"}).__dict__ for v in out.values()]
    return {"state":"AVAILABLE" if venues else "UNKNOWN","venues":venues,"errors":[] if venues else ["NO_VERIFIED_VENUE_CANDIDATE"]}

def discover_races_from_html(html, venue_name):
    if not html or not _norm_space(html):
        return {"state":"UNKNOWN","races":[],"errors":["EMPTY_RACE_PROGRAM"],"race_count":0}
    found={}
    for m in re.finditer(r'data-race-no=["\']?(\d{1,2})["\']?',html,re.I):
        n=int(m.group(1))
        if 1 <= n <= 20: found.setdefault(n,DiscoveredRace(n,evidence={"venue":venue_name}))
    for m in re.finditer(r'(\d{1,2})\s*R\\b',html,re.I):
        n=int(m.group(1))
        if 1 <= n <= 20: found.setdefault(n,DiscoveredRace(n,evidence={"venue":venue_name}))
    races=[found[n].__dict__ for n in sorted(found)]
    return {"state":"AVAILABLE" if races else "UNKNOWN","races":races,"race_count":len(races),"errors":[] if races else ["RACE_DISCOVERY_FAILED"]}

def build_daily_manifest(target_date, daily_html, race_program_html_by_venue):
    vd=discover_venues_from_html(daily_html,target_date)
    manifest={"target_date":target_date,"state":vd["state"],"venues":[],"recovery_queue":[]}
    for v in vd["venues"]:
        name=v["venue_name"]; rd=discover_races_from_html(race_program_html_by_venue.get(name),name)
        v["races"]=rd["races"]; v["race_count"]=rd["race_count"]; v["race_state"]=rd["state"]
        if rd["state"]!="AVAILABLE":
            v["state"]="PARTIAL"
            manifest["recovery_queue"].append({"venue":name,"domain":"RACE_DISCOVERY","state":rd["state"],"errors":rd["errors"]})
        manifest["venues"].append(v)
    if manifest["venues"] and all(v.get("race_state")=="AVAILABLE" for v in manifest["venues"]): manifest["state"]="AVAILABLE"
    elif manifest["venues"]: manifest["state"]="PARTIAL"
    return manifest

# ===== IC1.4 Source Adapter / Failover (DEV-B5) =====
class SourceAdapter:
    """Minimal adapter contract. Concrete adapters supply fetch callables."""
    def __init__(self,name,fetch_daily=None,fetch_program=None,priority=100):
        self.name=name
        self.fetch_daily=fetch_daily
        self.fetch_program=fetch_program
        self.priority=priority

def _adapter_call(fn,*args):
    if not fn:
        return {"ok":False,"error":"UNSUPPORTED"}
    try:
        body=fn(*args)
        if body is None or not str(body).strip():
            return {"ok":False,"error":"EMPTY_RESPONSE"}
        return {"ok":True,"body":str(body)}
    except TimeoutError:
        return {"ok":False,"error":"TIMEOUT"}
    except Exception as e:
        return {"ok":False,"error":type(e).__name__.upper()}

def reconcile_venue_candidates(source_results,target_date):
    """Union candidates, retain provenance/conflicts; no majority-vote suppression."""
    merged={}
    trace=[]
    for source_name,result in source_results:
        trace.append({"source":source_name,"state":result.get("state"),"errors":result.get("errors",[])})
        for v in result.get("venues",[]):
            key=(v.get("venue_code") or "",v.get("venue_name") or "")
            if not key[1]: continue
            item=merged.setdefault(key,dict(v))
            item.setdefault("sources",[])
            item["sources"].append(source_name)
    return {"state":"AVAILABLE" if merged else "UNKNOWN",
            "venues":list(merged.values()),"trace":trace,"target_date":target_date}

def discover_daily_with_failover(target_date,adapters):
    """Try every configured source; successful sources are reconciled."""
    results=[]; engine_trace=[]
    for a in sorted(adapters,key=lambda x:x.priority):
        raw=_adapter_call(a.fetch_daily,target_date)
        if not raw["ok"]:
            engine_trace.append({"source":a.name,"stage":"DAILY","state":"ERROR","error":raw["error"]})
            continue
        parsed=discover_venues_from_html(raw["body"],target_date)
        results.append((a.name,parsed))
        engine_trace.append({"source":a.name,"stage":"DAILY","state":parsed["state"],"errors":parsed.get("errors",[])})
    reconciled=reconcile_venue_candidates(results,target_date)
    reconciled["engine_trace"]=engine_trace
    if not results:
        reconciled["state"]="ERROR"
    return reconciled

def discover_program_with_failover(target_date,venue,adapters):
    """Race discovery failover. First verified manifest may qualify; trace is retained."""
    trace=[]
    for a in sorted(adapters,key=lambda x:x.priority):
        raw=_adapter_call(a.fetch_program,target_date,venue)
        if not raw["ok"]:
            trace.append({"source":a.name,"stage":"RACE_PROGRAM","state":"ERROR","error":raw["error"]})
            continue
        parsed=discover_races_from_html(raw["body"],venue.get("venue_name",""))
        trace.append({"source":a.name,"stage":"RACE_PROGRAM","state":parsed["state"],"race_count":parsed.get("race_count",0)})
        if parsed["state"]=="AVAILABLE" and parsed.get("races"):
            parsed["source"]=a.name; parsed["trace"]=trace
            return parsed
    return {"state":"ERROR" if trace else "UNKNOWN","races":[],"race_count":0,"trace":trace,
            "errors":["ALL_RACE_PROGRAM_SOURCES_FAILED"]}

def build_daily_manifest_from_adapters(target_date,adapters):
    daily=discover_daily_with_failover(target_date,adapters)
    manifest={"target_date":target_date,"state":daily["state"],"venues":[],
              "recovery_queue":[],"engine_trace":daily.get("engine_trace",[])}
    for v in daily.get("venues",[]):
        rp=discover_program_with_failover(target_date,v,adapters)
        item=dict(v); item["races"]=rp["races"]; item["race_count"]=rp["race_count"]; item["race_state"]=rp["state"]
        item["race_source"]=rp.get("source"); item["race_trace"]=rp.get("trace",[])
        if rp["state"]!="AVAILABLE":
            item["state"]="PARTIAL"
            manifest["recovery_queue"].append({"venue":v.get("venue_name"),"domain":"RACE_DISCOVERY",
                                               "state":rp["state"],"trace":rp.get("trace",[])})
        manifest["venues"].append(item)
    if manifest["venues"] and all(v["race_state"]=="AVAILABLE" for v in manifest["venues"]):
        manifest["state"]="AVAILABLE"
    elif manifest["venues"]:
        manifest["state"]="PARTIAL"
    return manifest

# ===== IC1.4 Venue Reconciliation / Meeting Classification (DEV-B6) =====
MEETING_ACTIVE="ACTIVE_MEETING"
MEETING_VERIFIED="VERIFIED_VENUE"
SALE_ONLY="SALE_REFERENCE_ONLY"
MEETING_UNKNOWN="UNKNOWN"

def classify_venue_evidence(candidate):
    """Classify venue evidence without confusing sales references with actual meetings."""
    ev=candidate.get("evidence",{}) or {}
    active=bool(ev.get("active_schedule") or ev.get("meeting_period_match"))
    race_ok=bool(ev.get("race_discovery_success"))
    sale=bool(ev.get("sale_reference"))
    if race_ok:
        return MEETING_VERIFIED
    if active:
        return MEETING_ACTIVE
    if sale:
        return SALE_ONLY
    return MEETING_UNKNOWN

def reconcile_meeting_evidence(candidates):
    """Merge evidence for same venue; conflicts remain visible rather than majority-voted away."""
    merged={}
    for c in candidates:
        key=(str(c.get("venue_code") or ""),str(c.get("venue_name") or ""))
        if not key[1]: continue
        m=merged.setdefault(key,{
            "venue_code":key[0],"venue_name":key[1],"sources":[],
            "evidence":{"active_schedule":False,"meeting_period_match":False,
                        "race_discovery_success":False,"sale_reference":False},
            "conflicts":[]
        })
        src=c.get("source")
        if src and src not in m["sources"]: m["sources"].append(src)
        ev=c.get("evidence",{}) or {}
        for k in m["evidence"]:
            m["evidence"][k]=m["evidence"][k] or bool(ev.get(k))
    out=[]
    for m in merged.values():
        ev=m["evidence"]
        # A venue may appear in sales references and still host a real meeting. Race/schedule evidence wins,
        # but the dual evidence is retained for audit.
        if ev["sale_reference"] and (ev["active_schedule"] or ev["meeting_period_match"] or ev["race_discovery_success"]):
            m["conflicts"].append("SALE_AND_ACTIVE_EVIDENCE")
        m["meeting_state"]=classify_venue_evidence(m)
        out.append(m)
    return out

def filter_active_meetings(candidates):
    reconciled=reconcile_meeting_evidence(candidates)
    active=[v for v in reconciled if v["meeting_state"] in (MEETING_ACTIVE,MEETING_VERIFIED)]
    excluded=[v for v in reconciled if v["meeting_state"]==SALE_ONLY]
    unresolved=[v for v in reconciled if v["meeting_state"]==MEETING_UNKNOWN]
    return {"active":active,"excluded_sale_only":excluded,"unresolved":unresolved}

def promote_race_discovery_evidence(venue, race_result):
    """Successful Race Discovery upgrades an active candidate to VERIFIED_VENUE."""
    v=dict(venue)
    ev=dict(v.get("evidence",{}) or {})
    if race_result.get("state")=="AVAILABLE" and race_result.get("race_count",0)>0:
        ev["race_discovery_success"]=True
    v["evidence"]=ev
    v["meeting_state"]=classify_venue_evidence(v)
    return v

# ===== IC1.4 End-to-End Orchestrator (DEV-B7) =====
def _safe_block(state="UNKNOWN",data=None,error=None):
    return {"state":state,"data":data,"error":error}

def run_race_pipeline(target_date,venue,race,acquirers):
    """One race, fail-soft. Acquirers are injected so source adapters remain replaceable."""
    packet={"target_date":target_date,"venue":venue,"race":race,"blocks":{},"recovery_queue":[],"engine_trace":[]}
    active=[]
    # ENTRY
    try:
        raw=acquirers["entry"](target_date,venue,race)
        entry=parse_entry(raw)
        active=sorted(int(e["car_no"]) for e in entry)
        state="AVAILABLE" if entry else "ERROR"
        packet["blocks"]["entry"]=_safe_block(state,entry,None if entry else "ENTRY_EMPTY")
    except Exception as e:
        packet["blocks"]["entry"]=_safe_block("ERROR",[],type(e).__name__.upper())
    if packet["blocks"]["entry"]["state"]!="AVAILABLE":
        packet["recovery_queue"].append({"domain":"ENTRY","race_no":race.get("race_no"),"state":"ERROR"})
        # Downstream blocks cannot be safely bound without Entry.
        for d in ("rider_stats","odds"):
            packet["blocks"][d]=_safe_block("UNKNOWN",None,"BLOCKED_BY_ENTRY")
        packet["state"]="PARTIAL"
        return packet

    # RIDER STATS
    try:
        raw=acquirers["rider_stats"](target_date,venue,race)
        rows,ok,meta=parse_stats(raw,packet["blocks"]["entry"]["data"])
        packet["blocks"]["rider_stats"]=_safe_block(meta["state"],rows)
        packet["blocks"]["rider_stats"]["meta"]=meta
        if not ok:
            packet["recovery_queue"].append({"domain":"RIDER_STATS","race_no":race.get("race_no"),
                                             "state":meta["state"],"missing_car_nos":meta["missing_car_nos"]})
    except Exception as e:
        packet["blocks"]["rider_stats"]=_safe_block("ERROR",[],type(e).__name__.upper())
        packet["recovery_queue"].append({"domain":"RIDER_STATS","race_no":race.get("race_no"),"state":"ERROR"})

    # ODDS: caller may return raw KDreams-like document; explicit bet labels are required.
    try:
        raw=acquirers["odds"](target_date,venue,race)
        odds=parse_kd_odds_sections(raw,active)
        available=[k for k,v in odds.items() if v.get("state")=="AVAILABLE"]
        states=[v.get("state") for v in odds.values()]
        if available:
            ost="AVAILABLE"
        elif "NOT_PUBLISHED" in states and all(x in ("NOT_PUBLISHED","UNKNOWN") for x in states):
            ost="NOT_PUBLISHED"
        elif "ERROR" in states:
            ost="ERROR"
        else:
            ost="UNKNOWN"
        packet["blocks"]["odds"]=_safe_block(ost,odds)
        packet["blocks"]["odds"]["available_bet_types"]=available
        if ost in ("ERROR","UNKNOWN"):
            packet["recovery_queue"].append({"domain":"ODDS","race_no":race.get("race_no"),"state":ost})
    except Exception as e:
        packet["blocks"]["odds"]=_safe_block("ERROR",{},type(e).__name__.upper())
        packet["recovery_queue"].append({"domain":"ODDS","race_no":race.get("race_no"),"state":"ERROR"})

    packet["state"]="AVAILABLE" if all(packet["blocks"][k]["state"]=="AVAILABLE" for k in ("entry","rider_stats","odds")) else "PARTIAL"
    return packet

def run_daily_e2e(target_date,adapters,acquirers):
    """target_date -> venues -> races -> Entry/Rider/Odds packets. One race failure never aborts the day."""
    manifest=build_daily_manifest_from_adapters(target_date,adapters)
    output={"target_date":target_date,"state":manifest["state"],"venues":[],"recovery_queue":list(manifest.get("recovery_queue",[])),
            "engine_trace":manifest.get("engine_trace",[]),"coverage":{}}
    total=available=partial=0
    for venue in manifest.get("venues",[]):
        # Only race-discovered venues proceed; this is the practical VERIFIED_VENUE gate.
        if venue.get("race_state")!="AVAILABLE":
            continue
        vout=dict(venue); vout["meeting_state"]=MEETING_VERIFIED; vout["race_packets"]=[]
        for race in venue.get("races",[]):
            total+=1
            try:
                rp=run_race_pipeline(target_date,venue,race,acquirers)
            except Exception as e:
                rp={"target_date":target_date,"venue":venue,"race":race,"state":"PARTIAL","blocks":{},
                    "recovery_queue":[{"domain":"RACE_PIPELINE","race_no":race.get("race_no"),"state":"ERROR","error":type(e).__name__.upper()}]}
            if rp["state"]=="AVAILABLE": available+=1
            else: partial+=1
            output["recovery_queue"].extend(rp.get("recovery_queue",[]))
            vout["race_packets"].append(rp)
        output["venues"].append(vout)
    output["coverage"]={"total_races":total,"available_races":available,"partial_races":partial,
                        "availability_rate":(available/total if total else 0.0)}
    if total and partial==0: output["state"]="AVAILABLE"
    elif total: output["state"]="PARTIAL"
    elif output["state"]=="AVAILABLE": output["state"]="UNKNOWN"
    return output

# ===== IC1.4 JFE -> Johnny Engine Normalized Packet (DEV-B8) =====
def build_je_race_packet(race_packet, now_epoch=None):
    """Convert a verified JFE race packet into a strict JE-facing contract.
    Fail closed: incomplete Entry/Rider/Odds never becomes ready_for_je=True.
    """
    blocks=race_packet.get("blocks",{})
    entry_b=blocks.get("entry",{})
    rider_b=blocks.get("rider_stats",{})
    odds_b=blocks.get("odds",{})
    entry=entry_b.get("data") or []
    riders=rider_b.get("data") or []
    odds=odds_b.get("data") or {}
    active=sorted(int(e["car_no"]) for e in entry if e.get("car_no") is not None)
    retrieved=sorted(int(r["car_no"]) for r in riders if r.get("car_no") is not None)
    missing=sorted(set(active)-set(retrieved))

    market=[]
    for bet_type,section in odds.items():
        if section.get("state")!="AVAILABLE":
            continue
        for q in section.get("quotes",[]) or section.get("values",[]) or []:
            if isinstance(q,dict):
                sel=q.get("selection") or q.get("combo")
                val=q.get("odds") or q.get("value")
                if sel is not None and val is not None:
                    market.append({"bet_type":bet_type,"selection":sel,"odds":val,
                                   "source_timestamp":section.get("source_timestamp")})
    available_types=odds_b.get("available_bet_types",[])
    integrity={
        "race_binding":"PASS" if race_packet.get("race") and race_packet.get("venue") else "ERROR",
        "entry_state":entry_b.get("state","UNKNOWN"),
        "rider_state":rider_b.get("state","UNKNOWN"),
        "odds_state":odds_b.get("state","UNKNOWN"),
        "active_car_numbers":active,
        "retrieved_car_numbers":retrieved,
        "missing_car_nos":missing,
        "available_bet_types":available_types,
    }
    ready=(integrity["race_binding"]=="PASS" and
           integrity["entry_state"]=="AVAILABLE" and
           integrity["rider_state"]=="AVAILABLE" and
           integrity["odds_state"]=="AVAILABLE" and
           not missing and bool(available_types))
    reasons=[]
    if integrity["race_binding"]!="PASS": reasons.append("JFE-B01_RACE_BINDING")
    if integrity["entry_state"]!="AVAILABLE": reasons.append("JFE-B02_ENTRY")
    if integrity["rider_state"]!="AVAILABLE" or missing: reasons.append("JFE-B03_RIDER_COMPLETENESS")
    if integrity["odds_state"]!="AVAILABLE" or not available_types: reasons.append("JFE-B04_MARKET")
    return {
        "schema":"JFE-JE-PACKET/0.2",
        "target_date":race_packet.get("target_date"),
        "venue":race_packet.get("venue"),
        "race":race_packet.get("race"),
        "riders":riders,
        "market":market,
        "market_sections":odds,
        "integrity":integrity,
        "ready_for_je":ready,
        "block_reasons":reasons,
        "recovery_queue":race_packet.get("recovery_queue",[])
    }

def attach_je_packets(daily_output):
    """Attach JE packets race-by-race without allowing one failure to contaminate the day."""
    out=dict(daily_output)
    venues=[]
    ready=blocked=0
    for v in daily_output.get("venues",[]):
        nv=dict(v); packets=[]
        for rp in v.get("race_packets",[]):
            nr=dict(rp)
            try:
                jp=build_je_race_packet(rp)
            except Exception as e:
                jp={"schema":"JFE-JE-PACKET/0.2","ready_for_je":False,
                    "block_reasons":["JFE-B99_PACKET_BUILD"],"error":type(e).__name__.upper()}
            nr["je_packet"]=jp
            ready += 1 if jp.get("ready_for_je") else 0
            blocked += 0 if jp.get("ready_for_je") else 1
            packets.append(nr)
        nv["race_packets"]=packets; venues.append(nv)
    out["venues"]=venues
    out["je_coverage"]={"ready":ready,"blocked":blocked,"total":ready+blocked,
                        "ready_rate":ready/(ready+blocked) if ready+blocked else 0.0}
    return out

# ===== IC1.4 Real Johnny Engine Bridge (DEV-B9) =====
def _num(v,default=70.0):
    try:return float(v)
    except:return float(default)

def _selection_tuple(sel):
    if isinstance(sel,(list,tuple)): return tuple(int(x) for x in sel)
    import re as _re
    return tuple(int(x) for x in _re.findall(r"\d+",str(sel)))

def je_packet_to_race_input(jp, lines=None, market_age_minutes=1.0):
    if not jp.get("ready_for_je"):
        raise ValueError("JFE_PACKET_NOT_READY")
    from johnny_engine_v1_0_proto import Rider,Line,MarketQuote,RaceInput
    riders=[]
    for r in jp.get("riders",[]):
        riders.append(Rider(
            number=int(r["car_no"]),
            rating=_num(r.get("score"),70),
            form=_num(r.get("form",r.get("score")),70),
            tactical=_num(r.get("tactical",r.get("score")),70),
            venue_fit=_num(r.get("venue_fit"),70),
            distance_fit=_num(r.get("distance_fit"),70),
            opponent_context=_num(r.get("opponent_context"),70)))
    active=[r.number for r in riders]
    raw_lines=lines or [[n] for n in active]
    jlines=[Line([int(x) for x in members],75.0) for members in raw_lines]
    market=[]
    for q in jp.get("market",[]):
        typ={"exacta":"2exacta","quinella":"2quinella","trio":"trio","trifecta":"trifecta",
             "2exacta":"2exacta","2quinella":"2quinella"}.get(q.get("bet_type"))
        if not typ: continue
        sel=_selection_tuple(q.get("selection"))
        if sel and all(n in active for n in sel):
            market.append(MarketQuote(typ,sel,float(q["odds"]),float(q.get("age_minutes",market_age_minutes))))
    race=jp.get("race") or {}; venue=jp.get("venue") or {}
    rid=str(race.get("race_id") or f'{jp.get("target_date")}|{venue.get("venue_name","UNKNOWN")}|{race.get("race_no","?")}R')
    completeness=100.0 if not jp["integrity"].get("missing_car_nos") else 60.0
    return RaceInput(rid,riders,jlines,market,completeness=completeness,
                     source_reliability=90.0,cross_source_match=90.0,schema_validity=100.0,
                     outlier_safety=100.0,timestamp_integrity=100.0,coverage_score=90.0)

def run_johnny_from_jfe_packet(jp, lines=None, market_age_minutes=1.0):
    if not jp.get("ready_for_je"):
        return {"state":"BLOCKED_BY_JFE","decision":"PASS","status_code":"JFE-BLOCK",
                "block_reasons":jp.get("block_reasons",[])}
    from johnny_engine_v1_0_proto import JohnnyEngineProto
    ri=je_packet_to_race_input(jp,lines,market_age_minutes)
    result=JohnnyEngineProto().run(ri)
    from dataclasses import asdict
    return {"state":"JE_EXECUTED","race_input":ri,"result":asdict(result)}

# ===== IC1.4 Dynamic URL/ID Resolver (DEV-B10) =====
from urllib.parse import urljoin as _urljoin

def discover_venues_from_links(html,target_date,base_url=""):
    """Discover venue code/name and source URL from actual links; no legacy VENUES dependency."""
    import re as _re
    out=[]; seen=set()
    for m in _re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',html or "",_re.I|_re.S):
        href=m.group(1); body=_norm_space(_re.sub(r"<[^>]+>"," ",m.group(2)))
        # Supports explicit venue code in common path/query shapes without assuming a fixed venue list.
        cm=_re.search(r'(?:venue|jyo|jo|place)[=/\-](\d{1,3})',href,_re.I)
        if not cm:
            cm=_re.search(r'[?&](?:venue|jyo|jo|place)(?:_?code)?=(\d{1,3})',href,_re.I)
        if not cm or not body: continue
        key=(cm.group(1),body)
        if key in seen: continue
        seen.add(key)
        out.append({"venue_code":cm.group(1),"venue_name":body,"source_url":_urljoin(base_url,href),
                    "target_date":target_date,"evidence":{"link_binding":True}})
    return {"state":"AVAILABLE" if out else "UNKNOWN","venues":out,
            "errors":[] if out else ["NO_BOUND_VENUE_LINK"]}

def discover_races_from_links(html,target_date,venue,base_url=""):
    """Discover actual race numbers/IDs/URLs; dedupe links and reject explicit date mismatch."""
    import re as _re
    races={}; conflicts=[]
    expected=str(target_date).replace("-","")
    for m in _re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',html or "",_re.I|_re.S):
        href=m.group(1); body=_norm_space(_re.sub(r"<[^>]+>"," ",m.group(2)))
        rm=_re.search(r'(?:race|r)[=/\-]?0?(\d{1,2})(?:\D|$)',href,_re.I) or _re.search(r'\b(\d{1,2})R\b',body,_re.I)
        if not rm: continue
        race_no=int(rm.group(1))
        # If URL contains an 8-digit date, it must bind to target_date.
        dates=_re.findall(r'(?<!\d)(20\d{6})(?!\d)',href)
        if dates and expected not in dates:
            conflicts.append({"race_no":race_no,"url":_urljoin(base_url,href),"error":"DATE_MISMATCH"})
            continue
        # Race ID is derived from explicit source URL token where possible, otherwise canonical dynamic key.
        idm=_re.search(r'(?:race(?:_?id)?)[=/\-]([A-Za-z0-9_-]{4,})',href,_re.I)
        rid=idm.group(1) if idm else f'{expected}-{venue.get("venue_code","UNK")}-{race_no:02d}'
        races[race_no]={"race_no":race_no,"race_id":rid,"source_url":_urljoin(base_url,href),
                        "target_date":target_date,"venue_code":venue.get("venue_code")}
    state="AVAILABLE" if races else ("ERROR" if conflicts else "UNKNOWN")
    return {"state":state,"races":[races[k] for k in sorted(races)],"race_count":len(races),
            "conflicts":conflicts,"errors":[] if races else ["NO_BOUND_RACE_LINK"]}

def resolve_kdreams_event_from_links(html,target_date,venue_code,base_url="https://keirin.kdreams.jp/"):
    """Resolve KDreams event base dynamically from observed racecard links."""
    import re as _re
    expected=str(target_date).replace("-","")
    candidates=[]
    for href in _re.findall(r'href=["\']([^"\']+)["\']',html or "",_re.I):
        m=_re.search(r'/racecard/(\d{12,16})/',href)
        if not m: continue
        token=m.group(1)
        # KDreams token begins with venue code and contains meeting date material.
        if venue_code and not token.startswith(str(venue_code)): continue
        # Require at least YYYYMMDD substring when present in token.
        if expected not in token and expected[2:] not in token: continue
        candidates.append((token,_urljoin(base_url,href)))
    if not candidates:
        return {"state":"UNKNOWN","event_base":None,"source_url":None,"error":"KD_EVENT_NOT_RESOLVED"}
    token,url=candidates[0]
    return {"state":"AVAILABLE","event_base":token,"source_url":url,"error":None}

# ===== IC1.4 Immutable Pre-Race Lock + Result/Learning (DEV-B11) =====
import hashlib
import html as _hashlib, json as _json, copy as _copy
from datetime import datetime as _dt, timezone as _tz
def _canonical_hash(obj):
    raw=_json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":"),default=str)
    return _hashlib.sha256(raw.encode("utf-8")).hexdigest()
def _lock_payload(lock):
    return {k:v for k,v in lock.items() if k not in ("lock_id","content_hash")}
def create_pre_race_lock(race_packet,je_packet=None,locked_at=None):
    snap={"level":"LEVEL_2_PRE_RACE_LOCK","target_date":race_packet.get("target_date"),
          "venue":_copy.deepcopy(race_packet.get("venue")),"race":_copy.deepcopy(race_packet.get("race")),
          "blocks":_copy.deepcopy(race_packet.get("blocks",{})),"je_packet":_copy.deepcopy(je_packet),
          "locked_at":locked_at or _dt.now(_tz.utc).isoformat()}
    snap["content_hash"]=_canonical_hash(_lock_payload(snap))
    snap["lock_id"]="PRL-"+snap["content_hash"][:20].upper()
    return snap
def verify_pre_race_lock(lock):
    expected=_canonical_hash(_lock_payload(lock))
    return {"valid":expected==lock.get("content_hash"),"expected_hash":expected,"stored_hash":lock.get("content_hash")}
def revise_pre_race_lock(old_lock,race_packet,je_packet=None,locked_at=None):
    new=create_pre_race_lock(race_packet,je_packet,locked_at)
    new["supersedes_lock_id"]=old_lock.get("lock_id")
    new["content_hash"]=_canonical_hash(_lock_payload(new))
    new["lock_id"]="PRL-"+new["content_hash"][:20].upper()
    return new
def normalize_result(finish_order=None,payouts=None,events=None,source=None,acquired_at=None):
    events=events or []; kinds={str(e.get("type","")).upper() for e in events if isinstance(e,dict)}
    abnormal=kinds & {"FALL","DNF","DISQUALIFICATION","WITHDRAWAL"}
    cls="MULTIPLE_EVENT" if len(abnormal)>1 else (next(iter(abnormal)) if abnormal else "NORMAL")
    return {"level":"LEVEL_3_RESULT","state":"AVAILABLE" if finish_order else "UNKNOWN",
            "finish_order":finish_order or [],"payouts":payouts or {},"events":events,"event_class":cls,
            "source":source,"acquired_at":acquired_at or _dt.now(_tz.utc).isoformat()}
def build_learning_candidate(pre_race_lock,result,je_result=None):
    if not verify_pre_race_lock(pre_race_lock)["valid"]:
        return {"level":"LEVEL_5_LEARNING_CANDIDATE","state":"ERROR","error":"PRE_RACE_LOCK_TAMPERED"}
    if result.get("state")!="AVAILABLE":
        return {"level":"LEVEL_5_LEARNING_CANDIDATE","state":"UNKNOWN","error":"RESULT_NOT_AVAILABLE"}
    return {"level":"LEVEL_5_LEARNING_CANDIDATE","state":"AVAILABLE","pre_race_lock_id":pre_race_lock.get("lock_id"),
            "result":_copy.deepcopy(result),"je_result":_copy.deepcopy(je_result),
            "evaluation_mode":"ABNORMAL_EVENT_REVIEW" if result.get("event_class")!="NORMAL" else "NORMAL_PREDICTION_REVIEW",
            "production_feature_eligible":False,"feature_lifecycle":"DISCOVERED_FEATURE"}

# ===== IC1.4 Post-Race Evaluation + Learning Repository (DEV-B12) =====
def evaluate_post_race(pre_race_lock,result,je_result=None,external_intelligence=None):
    if not verify_pre_race_lock(pre_race_lock)["valid"]:
        return {"level":"LEVEL_4_POST_RACE_EVALUATION","state":"ERROR","error":"PRE_RACE_LOCK_TAMPERED"}
    if result.get("state")!="AVAILABLE":
        return {"level":"LEVEL_4_POST_RACE_EVALUATION","state":"UNKNOWN","error":"RESULT_NOT_AVAILABLE"}
    finish=list(result.get("finish_order") or []); winner=finish[0] if finish else None
    je=je_result or {}
    if isinstance(je,dict) and isinstance(je.get("result"),dict): je=je["result"]
    model_pick=list(je.get("model_pick") or []) if isinstance(je,dict) else []
    bt=je.get("best_ticket") if isinstance(je,dict) else None
    typ=je.get("best_bet_type") if isinstance(je,dict) else None
    ticket_hit=None
    if bt and finish:
        bt=tuple(bt)
        if typ=="trifecta": ticket_hit=tuple(finish[:3])==bt
        elif typ=="trio": ticket_hit=tuple(sorted(finish[:3]))==tuple(sorted(bt))
        elif typ=="2exacta": ticket_hit=tuple(finish[:2])==bt
        elif typ=="2quinella": ticket_hit=tuple(sorted(finish[:2]))==tuple(sorted(bt))
    ext=[]
    for x in external_intelligence or []:
        picks=x.get("picks") or {}; main=picks.get("main") or picks.get("◎")
        ext.append({"source_id":x.get("source_id"),"prediction_id":x.get("prediction_id"),"main_pick":main,
                    "winner_hit":main==winner if main is not None else None,"reason_tags":list(x.get("reason_tags") or [])})
    abnormal=result.get("event_class")!="NORMAL"
    return {"level":"LEVEL_4_POST_RACE_EVALUATION","state":"AVAILABLE","pre_race_lock_id":pre_race_lock.get("lock_id"),
            "event_class":result.get("event_class"),"evaluation_mode":"ABNORMAL_EVENT_REVIEW" if abnormal else "NORMAL_PREDICTION_REVIEW",
            "winner":winner,"je":{"decision":je.get("decision"),"model_pick":model_pick,
            "winner_hit":winner in model_pick[:1] if model_pick and winner is not None else None,
            "best_bet_type":typ,"best_ticket":je.get("best_ticket"),"ticket_hit":ticket_hit},"external":ext}
class LearningRepository:
    def __init__(self): self._items=[]
    def append(self,candidate):
        item=_copy.deepcopy(candidate)
        if item.get("level")!="LEVEL_5_LEARNING_CANDIDATE": raise ValueError("INVALID_LEARNING_LEVEL")
        if item.get("state")!="AVAILABLE": raise ValueError("LEARNING_CANDIDATE_NOT_AVAILABLE")
        item["repository_index"]=len(self._items)
        item["repository_hash"]=_canonical_hash(item)
        self._items.append(item); return _copy.deepcopy(item)
    def all(self): return _copy.deepcopy(self._items)
    def verify(self):
        return all(_canonical_hash({k:v for k,v in x.items() if k!="repository_hash"})==x.get("repository_hash") for x in self._items)
def close_learning_loop(pre_race_lock,result,je_result=None,external_intelligence=None,repository=None):
    ev=evaluate_post_race(pre_race_lock,result,je_result,external_intelligence)
    if ev.get("state")!="AVAILABLE": return {"state":ev.get("state"),"evaluation":ev,"candidate":None,"stored":None}
    c=build_learning_candidate(pre_race_lock,result,je_result)
    c["post_race_evaluation"]=_copy.deepcopy(ev); c["external_intelligence"]=_copy.deepcopy(external_intelligence or [])
    stored=repository.append(c) if repository is not None else None
    return {"state":"AVAILABLE","evaluation":ev,"candidate":c,"stored":stored}

# ===== IC1.4 Feature Validation Pipeline (DEV-B13) =====
FEATURE_STAGES=("DISCOVERED_FEATURE","BACKTEST","SHADOW_TEST","OUT_OF_SAMPLE","ADOPT","REJECT")

def create_feature_candidate(feature_id,description,evidence_ids=None):
    return {"feature_id":feature_id,"description":description,"stage":"DISCOVERED_FEATURE",
            "history":[],"evidence_ids":list(evidence_ids or []),"production_enabled":False}

def advance_feature(candidate,target_stage,metrics=None,thresholds=None,note=None):
    c=_copy.deepcopy(candidate)
    if target_stage not in FEATURE_STAGES: raise ValueError("INVALID_FEATURE_STAGE")
    cur=c.get("stage","DISCOVERED_FEATURE")
    if cur in ("ADOPT","REJECT"): raise ValueError("TERMINAL_FEATURE_STATE")
    allowed={"DISCOVERED_FEATURE":{"BACKTEST","REJECT"},"BACKTEST":{"SHADOW_TEST","REJECT"},
             "SHADOW_TEST":{"OUT_OF_SAMPLE","REJECT"},"OUT_OF_SAMPLE":{"ADOPT","REJECT"}}
    if target_stage not in allowed.get(cur,set()): raise ValueError("INVALID_FEATURE_TRANSITION")
    metrics=metrics or {}; thresholds=thresholds or {}
    failures=[]
    for k,v in thresholds.items():
        if k not in metrics or float(metrics[k]) < float(v): failures.append(k)
    # Cannot advance a validation stage when its declared thresholds fail.
    if failures and target_stage!="REJECT":
        raise ValueError("FEATURE_THRESHOLD_FAIL:"+",".join(failures))
    c["history"].append({"from":cur,"to":target_stage,"metrics":_copy.deepcopy(metrics),
                         "thresholds":_copy.deepcopy(thresholds),"note":note})
    c["stage"]=target_stage
    c["production_enabled"]=(target_stage=="ADOPT")
    return c

def validate_feature_pipeline(candidate,backtest,shadow,out_of_sample):
    """Strict sequential validation; any failed gate ends in REJECT."""
    c=_copy.deepcopy(candidate)
    stages=[("BACKTEST",backtest),("SHADOW_TEST",shadow),("OUT_OF_SAMPLE",out_of_sample)]
    for stage,spec in stages:
        metrics=spec.get("metrics",{}); thresholds=spec.get("thresholds",{})
        failed=[k for k,v in thresholds.items() if k not in metrics or float(metrics[k])<float(v)]
        if failed:
            return advance_feature(c,"REJECT",metrics,{},note=f"{stage}_FAIL:"+",".join(failed))
        c=advance_feature(c,stage,metrics,thresholds,note=f"{stage}_PASS")
    return advance_feature(c,"ADOPT",out_of_sample.get("metrics",{}),{},note="ALL_VALIDATION_GATES_PASS")

def feature_can_enter_production(candidate):
    return candidate.get("stage")=="ADOPT" and candidate.get("production_enabled") is True

# ===== IC1.4 KDreams Live-Structure Adapter (DEV-B14) =====
def parse_kdreams_daily_text(text,target_date):
    """Parse rendered KDreams daily page text. Uses observed headings; never assumes venue list."""
    import re as _re
    date_j=f"{int(target_date[0:4])}年{int(target_date[5:7])}月{int(target_date[8:10])}日"
    if date_j not in text:
        return {"state":"ERROR","venues":[],"error":"DATE_BINDING_ERROR"}
    names=[]
    for m in _re.finditer(r"(?:###\s*)?([^\s#]+)競輪",text):
        n=m.group(1).strip()
        if n and n not in names: names.append(n)
    return {"state":"AVAILABLE" if names else "UNKNOWN",
            "venues":[{"venue_name":n,"target_date":target_date,"source":"kdreams"} for n in names],
            "error":None if names else "NO_VERIFIED_VENUE_CANDIDATE"}

def parse_kdreams_racecard_text(text,target_date,venue_name):
    """Parse KDreams racecard rendered text into race manifest + entry snapshots."""
    import re as _re
    expected=f"{target_date[0:4]}年{target_date[5:7]}月{target_date[8:10]}日"
    if expected not in text or f"{venue_name}競輪" not in text:
        return {"state":"ERROR","races":[],"error":"RACE_BINDING_ERROR"}
    # Sections begin with '* 1R...' in rendered page text.
    marks=list(_re.finditer(r"(?:^|\n)\s*\*\s*(\d{1,2})R([^\n]*)",text))
    races=[]
    for i,m in enumerate(marks):
        no=int(m.group(1)); section=text[m.start():marks[i+1].start() if i+1<len(marks) else len(text)]
        start=_re.search(r"発走\s*\n?\s*(\d{1,2}:\d{2})",section)
        close=_re.search(r"締切\s*\n?\s*(\d{1,2}:\d{2})",section)
        entries=[]
        # Observed rendered KDreams rows: mark | ... | car | car | name | prefecture | age | class...
        for row in section.splitlines():
            mm=_re.search(r"\|\s*(\d{1,2})\s*\|\s*(\d{1,2})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\d{1,3})\s*\|",row)
            if mm and mm.group(1)==mm.group(2):
                car=int(mm.group(1))
                if 1<=car<=9 and not any(e["car_no"]==car for e in entries):
                    entries.append({"car_no":car,"name":mm.group(3).strip(),"prefecture":mm.group(4).strip(),"age":int(mm.group(5))})
        races.append({"race_no":no,"title":m.group(2).strip(),"start_time":start.group(1) if start else None,
                      "close_time":close.group(1) if close else None,"entries":entries})
    return {"state":"AVAILABLE" if races else "UNKNOWN","races":races,"race_count":len(races),
            "error":None if races else "NO_BOUND_RACE_SECTION"}

def kd_event_base_to_race_id(event_base,race_no):
    """Observed KDreams final-day base 56202609140300 -> detail ...030001 etc."""
    token=str(event_base)
    if not token.isdigit() or len(token)<14: raise ValueError("INVALID_KD_EVENT_BASE")
    return token+f"{int(race_no):02d}"

# ===== IC1.4 Cross-Source Binding + Nationwide Orchestrator (DEV-B15) =====
def normalize_source_race(source_id,target_date,venue_name,race):
    return {"source_id":source_id,"target_date":target_date,"venue_name":venue_name,
            "race_no":int(race.get("race_no")),"race_id":race.get("race_id"),
            "source_url":race.get("source_url"),"entries":_copy.deepcopy(race.get("entries") or [])}

def cross_source_bind_race(primary,secondary):
    keys=("target_date","venue_name","race_no")
    mismatch=[k for k in keys if primary.get(k)!=secondary.get(k)]
    if mismatch:
        return {"state":"ERROR","binding":"SOURCE_CONFLICT","mismatch_fields":mismatch}
    pnums={int(e["car_no"]) for e in primary.get("entries",[]) if "car_no" in e}
    snums={int(e["car_no"]) for e in secondary.get("entries",[]) if "car_no" in e}
    if pnums and snums and pnums!=snums:
        return {"state":"PARTIAL","binding":"ENTRY_SET_CONFLICT",
                "primary_car_nos":sorted(pnums),"secondary_car_nos":sorted(snums)}
    return {"state":"AVAILABLE","binding":"QUALIFIED_CROSS_SOURCE",
            "race_key":f'{primary["target_date"]}|{primary["venue_name"]}|{primary["race_no"]}R',
            "sources":[primary.get("source_id"),secondary.get("source_id")],
            "active_car_numbers":sorted(pnums or snums)}

def run_nationwide_from_rendered_sources(target_date,kdreams_daily_text,racecards_by_venue,
                                         secondary_races_by_key=None):
    """Adapter-driven target_date -> all discovered venues -> all races.
       Per-venue/race failure is isolated and placed in Recovery Queue."""
    d=parse_kdreams_daily_text(kdreams_daily_text,target_date)
    out={"target_date":target_date,"state":d.get("state"),"venues":[],"recovery_queue":[]}
    if d.get("state")!="AVAILABLE": return out
    sec=secondary_races_by_key or {}
    total=ready=cross=0
    for v in d["venues"]:
        name=v["venue_name"]; raw=racecards_by_venue.get(name)
        if not raw:
            out["venues"].append({"venue_name":name,"state":"ERROR","races":[]})
            out["recovery_queue"].append({"venue_name":name,"stage":"RACE_PROGRAM","error":"MISSING_RACECARD_SOURCE"})
            continue
        rc=parse_kdreams_racecard_text(raw,target_date,name)
        vr={"venue_name":name,"state":rc.get("state"),"races":[]}
        if rc.get("state")!="AVAILABLE":
            out["recovery_queue"].append({"venue_name":name,"stage":"RACE_DISCOVERY","error":rc.get("error")})
        for r in rc.get("races",[]):
            total+=1
            pr=normalize_source_race("kdreams",target_date,name,r)
            key=f"{target_date}|{name}|{r['race_no']}R"
            sr=sec.get(key)
            binding={"state":"AVAILABLE","binding":"QUALIFIED_SINGLE_SOURCE","race_key":key,
                     "sources":["kdreams"],"active_car_numbers":[e["car_no"] for e in r.get("entries",[])]}
            if sr:
                binding=cross_source_bind_race(pr,normalize_source_race(sr.get("source_id","secondary"),target_date,name,sr))
                if binding.get("binding")=="QUALIFIED_CROSS_SOURCE": cross+=1
            rr=_copy.deepcopy(r); rr["binding"]=binding
            if binding.get("state")=="AVAILABLE": ready+=1
            else: out["recovery_queue"].append({"venue_name":name,"race_no":r["race_no"],"stage":"CROSS_SOURCE_BINDING","error":binding.get("binding")})
            vr["races"].append(rr)
        out["venues"].append(vr)
    out["coverage"]={"total_races":total,"bound_races":ready,"cross_source_bound":cross,
                     "single_source_bound":ready-cross,"binding_rate":ready/total if total else 0.0}
    if any(v["state"]=="ERROR" for v in out["venues"]) or ready<total: out["state"]="PARTIAL"
    else: out["state"]="AVAILABLE"
    return out

# ===== IC1.4 Live Integration Gate / Provenance (DEV-B16) =====
def make_live_evidence(source_id,source_url,published_at=None,acquired_at=None,parser_version=None,evidence=None):
    return {"source":source_id,"source_url":source_url,"published_at":published_at,
            "acquired_at":acquired_at or _dt.now(_tz.utc).isoformat(),
            "parser_version":parser_version or VERSION,"evidence":_copy.deepcopy(evidence)}

def live_integration_gate(target_date, daily_document, venue_documents, source_id="kdreams"):
    """Consumes externally acquired live documents; distinguishes transport from parser truth.
    No direct-network success is implied by this function."""
    daily_text=daily_document.get("text","")
    d=parse_kdreams_daily_text(daily_text,target_date)
    manifest={"target_date":target_date,"source_id":source_id,"state":d.get("state"),
              "venues":[],"recovery_queue":[],"provenance":[]}
    manifest["provenance"].append(make_live_evidence(source_id,daily_document.get("url"),
        daily_document.get("published_at"),daily_document.get("acquired_at"),VERSION,
        {"kind":"DAILY_DISCOVERY","state":d.get("state")}))
    if d.get("state")!="AVAILABLE": return manifest
    total=bound=0
    for v in d["venues"]:
        name=v["venue_name"]; doc=venue_documents.get(name)
        if not doc:
            manifest["venues"].append({"venue_name":name,"state":"ERROR","races":[]})
            manifest["recovery_queue"].append({"venue_name":name,"stage":"LIVE_DOCUMENT","error":"DOCUMENT_NOT_ACQUIRED"})
            continue
        rc=parse_kdreams_racecard_text(doc.get("text",""),target_date,name)
        item={"venue_name":name,"state":rc.get("state"),"races":rc.get("races",[])}
        manifest["venues"].append(item)
        manifest["provenance"].append(make_live_evidence(source_id,doc.get("url"),
            doc.get("published_at"),doc.get("acquired_at"),VERSION,
            {"kind":"RACECARD","venue_name":name,"state":rc.get("state"),"race_count":rc.get("race_count",0)}))
        if rc.get("state")=="AVAILABLE":
            total+=rc.get("race_count",0); bound+=rc.get("race_count",0)
        else:
            manifest["recovery_queue"].append({"venue_name":name,"stage":"LIVE_PARSE","error":rc.get("error")})
    manifest["coverage"]={"discovered_venues":len(d["venues"]),"acquired_venue_documents":len(venue_documents),
                          "bound_races":bound,"total_parsed_races":total}
    manifest["state"]="AVAILABLE" if not manifest["recovery_queue"] else "PARTIAL"
    return manifest

def release_candidate_gate(test_pass,compile_pass,live_manifest):
    blockers=[]
    if not test_pass: blockers.append("REGRESSION_TEST_FAILURE")
    if not compile_pass: blockers.append("COMPILE_FAILURE")
    if not live_manifest or live_manifest.get("state")!="AVAILABLE": blockers.append("LIVE_INTEGRATION_INCOMPLETE")
    if live_manifest and live_manifest.get("recovery_queue"): blockers.append("LIVE_RECOVERY_QUEUE_NOT_EMPTY")
    return {"rc_ready":not blockers,"blockers":blockers,
            "status":"RC_CANDIDATE" if not blockers else "DEV"}

# ===== IC1.4 RC Audit / Live Manifest Evidence (DEV-B17) =====
def audit_live_manifest(manifest, expected_venues=None):
    expected=set(expected_venues or [])
    actual={v.get("venue_name") for v in manifest.get("venues",[])}
    missing=sorted(expected-actual)
    bad=[v.get("venue_name") for v in manifest.get("venues",[]) if v.get("state")!="AVAILABLE"]
    prov=manifest.get("provenance",[])
    prov_ok=bool(prov) and all(x.get("source") and x.get("source_url") and x.get("acquired_at") and x.get("parser_version") for x in prov)
    blockers=[]
    if missing: blockers.append("VENUE_COVERAGE_MISSING")
    if bad: blockers.append("VENUE_PARSE_INCOMPLETE")
    if manifest.get("recovery_queue"): blockers.append("RECOVERY_QUEUE_NOT_EMPTY")
    if not prov_ok: blockers.append("PROVENANCE_INCOMPLETE")
    return {"pass":not blockers,"blockers":blockers,"missing_venues":missing,
            "bad_venues":bad,"provenance_ok":prov_ok,
            "venue_count":len(actual),"race_count":sum(len(v.get("races",[])) for v in manifest.get("venues",[]))}

def rc_audit(test_pass,compile_pass,manifest,expected_venues=None,direct_runtime_http_verified=False):
    live=audit_live_manifest(manifest,expected_venues)
    blockers=[]
    if not test_pass: blockers.append("REGRESSION_TEST_FAILURE")
    if not compile_pass: blockers.append("COMPILE_FAILURE")
    blockers.extend(live["blockers"])
    if not direct_runtime_http_verified: blockers.append("DIRECT_RUNTIME_HTTP_NOT_VERIFIED")
    return {"rc_ready":not blockers,"status":"RC_CANDIDATE" if not blockers else "DEV",
            "blockers":blockers,"live_audit":live}

# ===== IC1.4 Direct HTTP Acquisition (DEV-B18) =====
def direct_http_get(url, timeout=12, retries=2, user_agent="Mozilla/5.0 JFE/1.0"):
    import urllib.request as _ur, urllib.error as _ue, time as _time
    attempts=[]
    for n in range(retries+1):
        t0=_time.time()
        try:
            req=_ur.Request(url,headers={"User-Agent":user_agent,"Accept":"text/html,application/xhtml+xml"})
            with _ur.urlopen(req,timeout=timeout) as r:
                raw=r.read()
                ctype=r.headers.get_content_charset() or "utf-8"
                try: text=raw.decode(ctype,errors="replace")
                except LookupError: text=raw.decode("utf-8",errors="replace")
                return {"state":"AVAILABLE","url":url,"http_status":getattr(r,"status",200),
                        "text":text,"bytes":len(raw),"acquired_at":_dt.now(_tz.utc).isoformat(),
                        "attempts":attempts+[{"attempt":n+1,"ok":True,"elapsed_ms":round((_time.time()-t0)*1000,1)}]}
        except Exception as e:
            attempts.append({"attempt":n+1,"ok":False,"error_type":type(e).__name__,
                             "error":str(e)[:240],"elapsed_ms":round((_time.time()-t0)*1000,1)})
            if n<retries: _time.sleep(min(.25*(2**n),1.0))
    return {"state":"ERROR","url":url,"error":"DIRECT_HTTP_FETCH_FAILED",
            "acquired_at":_dt.now(_tz.utc).isoformat(),"attempts":attempts}

def direct_http_live_probe(url, expected_tokens=None, timeout=12):
    doc=direct_http_get(url,timeout=timeout)
    if doc["state"]!="AVAILABLE": return doc
    missing=[x for x in (expected_tokens or []) if x not in doc["text"]]
    doc["content_binding"]="AVAILABLE" if not missing else "ERROR"
    doc["missing_tokens"]=missing
    return doc

INGRESS_SCHEMA="JFE-EXTERNAL-INGRESS/1.0"
def build_ingress_document(source,source_url,text,acquired_at,transport="EXTERNAL_WEB"):
 import hashlib
 return {"schema":INGRESS_SCHEMA,"source":source,"source_url":source_url,"acquired_at":acquired_at,"transport":transport,"content_sha256":hashlib.sha256(text.encode()).hexdigest(),"text":text}
def verify_ingress_document(d):
 import hashlib
 ok=all(d.get(k) for k in ("source","source_url","acquired_at","transport","content_sha256")) and d.get("schema")==INGRESS_SCHEMA and d.get("text") is not None and hashlib.sha256(d["text"].encode()).hexdigest()==d.get("content_sha256")
 return {"state":"AVAILABLE" if ok else "ERROR"}
def run_external_ingress_live_gate(target_date,daily,venues):
 if verify_ingress_document(daily)["state"]!="AVAILABLE":return {"state":"ERROR"}
 docs={n:{"url":d["source_url"],"text":d["text"],"acquired_at":d["acquired_at"]} for n,d in venues.items() if verify_ingress_document(d)["state"]=="AVAILABLE"}
 out=live_integration_gate(target_date,{"url":daily["source_url"],"text":daily["text"],"acquired_at":daily["acquired_at"]},docs,source_id=daily["source"]);out["ingress_schema"]=INGRESS_SCHEMA;return out

# ===== IC1.4 Web Acquisition -> Trusted Ingress Bridge (DEV-B20) =====
def web_payload_to_ingress(payload, source, acquired_at, published_at=None):
    """Convert a normalized external web payload into immutable JFE ingress.
    Payload must carry the exact source URL and extracted text."""
    if not isinstance(payload, dict):
        raise ValueError("WEB_PAYLOAD_INVALID")
    url=payload.get("url") or payload.get("source_url")
    text=payload.get("text")
    if not url or text is None:
        raise ValueError("WEB_PAYLOAD_REQUIRED_FIELD_MISSING")
    return build_ingress_document(source,url,text,acquired_at,transport="EXTERNAL_WEB")

def build_ingress_bundle(target_date, daily_payload, venue_payloads, source="kdreams", acquired_at=None):
    if not acquired_at:
        raise ValueError("ACQUIRED_AT_REQUIRED")
    daily=web_payload_to_ingress(daily_payload,source,acquired_at)
    venues={}
    errors=[]
    for venue,payload in (venue_payloads or {}).items():
        try:
            venues[venue]=web_payload_to_ingress(payload,source,acquired_at)
        except Exception as e:
            errors.append({"venue_name":venue,"state":"ERROR","error":type(e).__name__+":"+str(e)})
    return {"schema":"JFE-INGRESS-BUNDLE/1.0","target_date":target_date,
            "daily":daily,"venues":venues,"errors":errors}

def run_web_payload_e2e(target_date,daily_payload,venue_payloads,source="kdreams",acquired_at=None):
    bundle=build_ingress_bundle(target_date,daily_payload,venue_payloads,source,acquired_at)
    manifest=run_external_ingress_live_gate(target_date,bundle["daily"],bundle["venues"])
    manifest["bundle_schema"]=bundle["schema"]
    manifest["bundle_errors"]=bundle["errors"]
    if bundle["errors"]:
        manifest["state"]="PARTIAL"
        manifest.setdefault("recovery_queue",[]).extend(bundle["errors"])
    return {"bundle":bundle,"manifest":manifest}

# ===== IC1.4 Reproducible Ingress Artifact (DEV-B21) =====
INGRESS_ARTIFACT_SCHEMA="JFE-INGRESS-ARTIFACT/1.0"

def build_ingress_artifact(target_date,daily_payload,venue_payloads,source,acquired_at):
    bundle=build_ingress_bundle(target_date,daily_payload,venue_payloads,source,acquired_at)
    core={"schema":INGRESS_ARTIFACT_SCHEMA,"target_date":target_date,"source":source,
          "created_at":acquired_at,"bundle":bundle}
    raw=json.dumps(core,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    core["artifact_sha256"]=__import__("hashlib").sha256(raw).hexdigest()
    return core

def verify_ingress_artifact(artifact):
    import hashlib
    errors=[]
    if artifact.get("schema")!=INGRESS_ARTIFACT_SCHEMA: errors.append("ARTIFACT_SCHEMA_INVALID")
    supplied=artifact.get("artifact_sha256")
    core={k:v for k,v in artifact.items() if k!="artifact_sha256"}
    raw=json.dumps(core,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    if not supplied or hashlib.sha256(raw).hexdigest()!=supplied: errors.append("ARTIFACT_HASH_MISMATCH")
    b=artifact.get("bundle") or {}
    if b.get("target_date")!=artifact.get("target_date"): errors.append("ARTIFACT_DATE_MISMATCH")
    docs=[]
    if b.get("daily"): docs.append(b["daily"])
    docs.extend((b.get("venues") or {}).values())
    for d in docs:
        if verify_ingress_document(d).get("state")!="AVAILABLE":
            errors.append("ARTIFACT_INGRESS_DOCUMENT_INVALID"); break
    return {"state":"AVAILABLE" if not errors else "ERROR","errors":errors}

def save_ingress_artifact(path,artifact):
    v=verify_ingress_artifact(artifact)
    if v["state"]!="AVAILABLE": raise ValueError("INVALID_INGRESS_ARTIFACT:"+",".join(v["errors"]))
    with open(path,"w",encoding="utf-8") as f: json.dump(artifact,f,ensure_ascii=False,indent=2)
    return path

def load_ingress_artifact(path):
    with open(path,encoding="utf-8") as f: a=json.load(f)
    v=verify_ingress_artifact(a)
    if v["state"]!="AVAILABLE": raise ValueError("INVALID_INGRESS_ARTIFACT:"+",".join(v["errors"]))
    return a

def run_ingress_artifact_e2e(artifact):
    v=verify_ingress_artifact(artifact)
    if v["state"]!="AVAILABLE": return {"state":"ERROR","error":"INGRESS_ARTIFACT_INVALID","details":v}
    b=artifact["bundle"]
    manifest=run_external_ingress_live_gate(artifact["target_date"],b["daily"],b["venues"])
    manifest["artifact_sha256"]=artifact["artifact_sha256"]
    manifest["artifact_schema"]=artifact["schema"]
    return manifest

# ===== DEV-B22: Web Evidence Artifact / parser compatibility =====
def normalize_web_evidence_text(text):
    # Strip citation UI markers/line labels while preserving source-visible content.
    text=re.sub(r'cite[^]+','',text)
    text=re.sub(r'(?m)^L\d+:\s?','',text)
    return text

def build_web_evidence_artifact(target_date, source_url, text, acquired_at, source="kdreams"):
    normalized=normalize_web_evidence_text(text)
    payload={"url":source_url,"text":normalized}
    art=build_ingress_artifact(target_date,payload,{},source,acquired_at)
    art["evidence_kind"]="WEB_RENDERED_TEXT"
    # recompute artifact hash after adding evidence kind
    core={k:v for k,v in art.items() if k!="artifact_sha256"}
    art["artifact_sha256"]=hashlib.sha256(json.dumps(core,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return art

def extract_daily_live_facts(text,target_date):
    t=normalize_web_evidence_text(text)
    m=re.search(r'本日\s+(\d{4})年(\d{1,2})月(\d{1,2})日\s+開催一覧',t)
    if not m:return {"state":"ERROR","error":"DATE_BINDING_NOT_FOUND"}
    got=f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    if got!=target_date:return {"state":"ERROR","error":"DATE_MISMATCH","found":got}
    venues=re.findall(r'([^\s#*|]+?)競輪(?:\s|$)',t)
    # preserve order / remove navigation noise
    out=[]
    for v in venues:
        v=v.strip("[]() ")
        if v and v not in out and len(v)<=8:out.append(v)
    return {"state":"AVAILABLE","target_date":got,"venues":out}

def extract_kishiwada_reg_b001(text):
    t=normalize_web_evidence_text(text)
    date_ok="2026年09月16日 出走表一覧" in t
    race_ok=bool(re.search(r'1Rチャレンジ一般',t))
    row_ok=bool(re.search(r'5\s*\|\s*5\s*\|\s*吉川誠',t))
    return {"state":"AVAILABLE" if date_ok and race_ok and row_ok else "ERROR",
            "date_bound":date_ok,"race_1_bound":race_ok,"car5_yoshikawa_bound":row_ok}

# ===== DEV-B23 Nationwide Live Coverage Gate =====
def nationwide_live_coverage_gate(target_date, venue_evidence):
    rows=[]; verified=0
    for venue,e in venue_evidence.items():
        date_ok=e.get("target_date")==target_date
        race_count=e.get("race_count")
        source_ok=bool(e.get("source_url"))
        state="AVAILABLE" if date_ok and source_ok and isinstance(race_count,int) and race_count>0 else "ERROR"
        if state=="AVAILABLE":verified+=1
        rows.append({"venue":venue,"state":state,"race_count":race_count,"source_url":e.get("source_url"),
                     "target_date":e.get("target_date"),"evidence_level":e.get("evidence_level","UNKNOWN")})
    total=len(rows)
    return {"target_date":target_date,"venues":rows,"verified_venues":verified,"total_venues":total,
            "coverage_rate":verified/total if total else 0.0,
            "state":"AVAILABLE" if total and verified==total else "PARTIAL"}

# ===== DEV-B24 strict pre-JE evidence gate =====
def _b24_dt(v):
    import datetime as d
    try:
        x=d.datetime.fromisoformat(v.replace("Z","+00:00")); return x if x.tzinfo else None
    except:return None
def validate_je_contract_evidence(jp):
    r=[]; active=sorted(int(e["car_no"]) for e in (jp.get("entries") or []))
    lines=jp.get("lines"); flat=[]
    if not lines:r.append("JFE-B05_LINE")
    else:
        try:flat=[int(c) for line in lines for c in line]
        except:flat=[]
        if sorted(flat)!=active or len(flat)!=len(set(flat)):r.append("JFE-B05_LINE")
    I=jp.get("integrity") or {}
    for k in ("source_reliability","cross_source_match","schema_validity","outlier_safety","timestamp_integrity","coverage_score"):
        q=I.get(k)
        if not isinstance(q,dict) or not isinstance(q.get("value"),(int,float)) or not q.get("evidence"):
            r.append("JFE-B06_QUALITY");break
    M=jp.get("market") or []
    if not M or any(not _b24_dt(q.get("source_timestamp","")) or not _b24_dt(q.get("acquired_at","")) for q in M):
        r.append("JFE-B07_FRESHNESS")
    return {"state":"BLOCKED" if r else "AVAILABLE","reasons":list(dict.fromkeys(r))}
def derive_je_evidence(jp,now):
    v=validate_je_contract_evidence(jp)
    if v["state"]!="AVAILABLE":return {"state":"BLOCKED","reasons":v["reasons"]}
    n=_b24_dt(now)
    if not n:return {"state":"BLOCKED","reasons":["JFE-B07_FRESHNESS"]}
    vals={k:float(jp["integrity"][k]["value"]) for k in ("source_reliability","cross_source_match","schema_validity","outlier_safety","timestamp_integrity","coverage_score")}
    ages=[max(0,(n-_b24_dt(q["source_timestamp"])).total_seconds()/60) for q in jp["market"]]
    return {"state":"AVAILABLE","quality":vals,"lines":jp["lines"],"market_age_minutes":max(ages)}
def run_johnny_from_jfe_packet(jp,now=None):
    e=derive_je_evidence(jp,now) if now else validate_je_contract_evidence(jp)
    if e["state"]!="AVAILABLE":return {"state":"BLOCKED","reasons":e["reasons"],"je_executed":False}
    # Legacy B8/B9 readiness is still required after B24 evidence gate.
    try:
        ri=je_packet_to_race_input(jp,now)
    except Exception as ex:
        return {"state":"BLOCKED","reasons":["JFE-B08_LEGACY_PACKET_READY"],"je_executed":False,"detail":str(ex)}
    return {"state":"AVAILABLE","race_input":ri,"je_executed":False}

# ===== DEV-B25 parser-to-RaceInput strict adapter =====
def market_from_parsed_odds(parsed, source_timestamp, acquired_at):
    out=[]
    for bt,b in (parsed or {}).items():
        if not isinstance(b,dict) or b.get("state")!="AVAILABLE" or not b.get("bet_type_bound"):continue
        for q in b.get("data") or []:
            out.append({"bet_type":bt,"selection":q["selection"],"odds":float(q["odds"]),
                        "source_timestamp":source_timestamp,"acquired_at":acquired_at})
    return out
def strict_packet_from_parser(race_id,entries,riders,lines,parsed,integrity,source_timestamp,acquired_at):
    return {"race_id":race_id,"entries":entries,"riders":riders,"lines":lines,
            "market":market_from_parsed_odds(parsed,source_timestamp,acquired_at),"integrity":integrity}
def parser_packet_to_race_input(jp,now):
    import johnny_engine_v1_0_proto as _je
    ev=derive_je_evidence(jp,now)
    if ev["state"]!="AVAILABLE":return {"state":"BLOCKED","reasons":ev["reasons"]}
    rs=[]
    for r in jp["riders"]:
        # These fields are required evidence, not defaults.
        need=("car_no","rating","form","tactical","venue_fit","distance_fit","opponent_context")
        if any(k not in r for k in need):return {"state":"BLOCKED","reasons":["JFE-B09_RIDER_FEATURES"]}
        rs.append(_je.Rider(int(r["car_no"]),float(r["rating"]),float(r["form"]),float(r["tactical"]),
                            float(r["venue_fit"]),float(r["distance_fit"]),float(r["opponent_context"])))
    ls=[]
    for line in jp["lines"]:
        if not isinstance(line,dict) or "members" not in line or "cohesion" not in line:
            return {"state":"BLOCKED","reasons":["JFE-B10_LINE_FEATURES"]}
        ls.append(_je.Line([int(x) for x in line["members"]],float(line["cohesion"])))
    mq=[_je.MarketQuote(q["bet_type"],tuple(q["selection"]),float(q["odds"]),ev["market_age_minutes"]) for q in jp["market"]]
    I=ev["quality"]
    ri=_je.RaceInput(jp["race_id"],rs,ls,mq,I["coverage_score"],I["source_reliability"],I["cross_source_match"],
                     I["schema_validity"],I["outlier_safety"],I["timestamp_integrity"],I["coverage_score"])
    return {"state":"AVAILABLE","race_input":ri,"market_age_minutes":ev["market_age_minutes"]}

# ===== DEV-B26 Cross-Venue Live Evidence Coverage Matrix =====
def live_evidence_coverage_matrix(records):
    out=[]; counts={}
    for r in records:
        missing=[]
        if not r.get("race_bound"): missing.append("RACE_BINDING")
        if not r.get("entries_verified"): missing.append("ENTRY")
        if not r.get("rider_features_verified"): missing.append("JFE-B09_RIDER_FEATURES")
        if not r.get("line_features_verified"): missing.append("JFE-B10_LINE_FEATURES")
        if not r.get("odds_verified"): missing.append("ODDS")
        if not r.get("timestamp_verified"): missing.append("JFE-B07_FRESHNESS")
        if not r.get("quality_evidence_verified"): missing.append("JFE-B06_QUALITY")
        state="AVAILABLE" if not missing else "BLOCKED"
        for x in missing: counts[x]=counts.get(x,0)+1
        out.append({"venue":r["venue"],"race":r["race"],"state":state,"blockers":missing,
                    "source_url":r.get("source_url"),"evidence":r.get("evidence",{})})
    return {"records":out,"blocker_counts":counts,
            "available":sum(x["state"]=="AVAILABLE" for x in out),
            "blocked":sum(x["state"]=="BLOCKED" for x in out)}

# ===== DEV-B27 Racecard Rider/Line Evidence Adapter =====
def parse_racecard_rider_evidence(rows):
    out=[]
    for r in rows:
        need=("car_no","name","score","style")
        if any(k not in r for k in need): continue
        out.append({"car_no":int(r["car_no"]),"name":r["name"],"score":float(r["score"]),
                    "style":r["style"],"state":"AVAILABLE","evidence":r.get("evidence")})
    return out

def parse_line_prediction_evidence(text, active):
    # Source format: ← 3先行 6追込 2追上 4追上 1追込 5押え先 7追込
    toks=re.findall(r'([1-9])\s*(先行|追込|追上|押え先|自在|捲り|マーク)',text or "")
    cars=[int(x[0]) for x in toks]
    if not toks or sorted(cars)!=sorted(active) or len(cars)!=len(set(cars)):
        return {"state":"BLOCKED","reason":"JFE-B05_LINE","raw":text}
    # This is ordered tactical evidence, not fabricated cohesion.
    return {"state":"AVAILABLE","ordered":[{"car_no":int(c),"role":role} for c,role in toks],
            "raw":text,"cohesion_state":"UNKNOWN"}

def b27_feature_gate(riders,line):
    reasons=[]
    if len(riders)==0: reasons.append("JFE-B09_RIDER_FEATURES")
    if line.get("state")!="AVAILABLE": reasons.append("JFE-B05_LINE")
    # Johnny's cohesion is not published by source, so B10 remains closed.
    if line.get("cohesion_state")!="AVAILABLE": reasons.append("JFE-B10_LINE_FEATURES")
    return {"state":"BLOCKED" if reasons else "AVAILABLE","reasons":reasons}

# DEV-B28 Explicit Feature Engineering
FEATURE_SCHEMA="JFE-JE-FEATURES/0.1"
FEATURE_VERSION="b28-linear-v1"
def _fe_clamp(x): return max(0.0,min(100.0,float(x)))
def derive_rider_features(r):
    req=("car_no","score","win_rate","top2_rate","top3_rate","venue_rate","distance_rate","opponent_context")
    miss=[k for k in req if r.get(k) is None]
    if miss:return {"state":"BLOCKED","reason":"JFE-B09_RIDER_FEATURES","missing":miss,"feature_version":FEATURE_VERSION}
    win,t2,t3=float(r["win_rate"]),float(r["top2_rate"]),float(r["top3_rate"])
    return {"state":"AVAILABLE","car_no":int(r["car_no"]),
      "rating":_fe_clamp((float(r["score"])-60)*2.5),
      "form":_fe_clamp(.50*win+.30*t2+.20*t3),
      "tactical":_fe_clamp(.25*win+.35*t2+.40*t3),
      "venue_fit":_fe_clamp(r["venue_rate"]),"distance_fit":_fe_clamp(r["distance_rate"]),
      "opponent_context":_fe_clamp(r["opponent_context"]),"feature_version":FEATURE_VERSION,
      "source_evidence":r.get("evidence",[])}
def derive_line_features(members,riders):
    by={x["car_no"]:x for x in riders if x.get("state")=="AVAILABLE"}
    if not members or len(set(members))!=len(members) or any(int(c) not in by for c in members):
        return {"state":"BLOCKED","reason":"JFE-B10_LINE_FEATURES"}
    vals=[by[int(c)]["tactical"] for c in members]; mean=sum(vals)/len(vals)
    sd=(sum((x-mean)**2 for x in vals)/len(vals))**.5
    return {"state":"AVAILABLE","members":list(members),"cohesion":_fe_clamp(100-sd),
            "feature_version":FEATURE_VERSION}
def feature_engineering_gate(rows,lines):
    riders=[derive_rider_features(x) for x in rows]
    if any(x["state"]!="AVAILABLE" for x in riders):
        return {"state":"BLOCKED","reason":"JFE-B09_RIDER_FEATURES","riders":riders}
    lf=[derive_line_features(x,riders) for x in lines]
    if any(x["state"]!="AVAILABLE" for x in lf):
        return {"state":"BLOCKED","reason":"JFE-B10_LINE_FEATURES","riders":riders,"lines":lf}
    return {"state":"CANDIDATE","feature_schema":FEATURE_SCHEMA,"feature_version":FEATURE_VERSION,
            "riders":riders,"lines":lf,"validation_stage":"DISCOVERED_FEATURE","production_eligible":False}

# ===== DEV-B29 Feature Backtest Harness =====
BACKTEST_SCHEMA="JFE-FEATURE-BACKTEST/0.1"

def rank_riders_from_features(feature_gate):
    if feature_gate.get("state")!="CANDIDATE": return []
    scored=[]
    for r in feature_gate["riders"]:
        # Candidate composite, explicit and versioned; not production logic.
        score=.45*r["rating"]+.30*r["form"]+.25*r["tactical"]
        scored.append((int(r["car_no"]),score))
    return [c for c,_ in sorted(scored,key=lambda x:(-x[1],x[0]))]

def backtest_feature_candidate(races):
    rows=[]; top1=top3=0; valid=0
    for race in races:
        fg=feature_engineering_gate(race["source_rows"],race["lines"])
        if fg.get("state")!="CANDIDATE":
            rows.append({"race_id":race["race_id"],"state":"BLOCKED","reason":fg.get("reason")}); continue
        ranking=rank_riders_from_features(fg); winner=int(race["winner"])
        valid+=1; top1+=int(ranking and ranking[0]==winner); top3+=int(winner in ranking[:3])
        rows.append({"race_id":race["race_id"],"state":"EVALUATED","winner":winner,"ranking":ranking,
                     "top1_hit":ranking[0]==winner,"top3_hit":winner in ranking[:3]})
    return {"schema":BACKTEST_SCHEMA,"feature_version":FEATURE_VERSION,"sample_size":valid,
            "top1_accuracy":top1/valid if valid else None,"top3_recall":top3/valid if valid else None,
            "rows":rows,"validation_stage":"BACKTEST",
            "production_eligible":False}

def compare_candidate_to_baseline(candidate, baseline_top1_accuracy):
    if candidate["sample_size"]<20:
        return {"state":"INSUFFICIENT_EVIDENCE","reason":"MIN_SAMPLE_20","production_eligible":False}
    delta=candidate["top1_accuracy"]-float(baseline_top1_accuracy)
    return {"state":"BACKTEST_PASS" if delta>0 else "BACKTEST_FAIL","delta_top1":delta,
            "production_eligible":False}

# ===== DEV-B30 Immutable Historical Dataset Builder =====
HIST_SCHEMA="JFE-HISTORICAL-DATASET/1.0"
def _hist_hash(x):
 import hashlib
 return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def normalize_historical_race(raw):
 from datetime import date as _date
 req=("race_id","target_date","venue","race_no","source_rows","lines","winner","source_url","acquired_at")
 miss=[k for k in req if raw.get(k) in (None,"",[])]
 if miss:return {"state":"BLOCKED","reason":"HIST_REQUIRED_MISSING","missing":miss}
 try:_date.fromisoformat(raw["target_date"])
 except:return {"state":"BLOCKED","reason":"HIST_DATE_INVALID"}
 cars=sorted(int(x["car_no"]) for x in raw["source_rows"])
 if int(raw["winner"]) not in cars:return {"state":"BLOCKED","reason":"HIST_WINNER_NOT_IN_ENTRY"}
 payload={k:raw[k] for k in req};payload["source_rows"]=sorted(payload["source_rows"],key=lambda x:int(x["car_no"]))
 payload["provenance"]={"source_url":raw["source_url"],"acquired_at":raw["acquired_at"],"evidence":raw.get("evidence",[]),"parser_version":raw.get("parser_version","UNKNOWN")}
 payload["content_sha256"]=_hist_hash(payload)
 return {"state":"AVAILABLE","race":payload}
def build_historical_dataset(records):
 races=[];rejected=[]
 for x in records:
  n=normalize_historical_race(x)
  if n["state"]=="AVAILABLE":races.append(n["race"])
  else:rejected.append({"race_id":x.get("race_id"),**n})
 core={"schema":HIST_SCHEMA,"races":races,"rejected":rejected,"race_count":len(races),"rejected_count":len(rejected)}
 core["dataset_sha256"]=_hist_hash(core);return core
def verify_historical_dataset(ds):
 h=ds.get("dataset_sha256");core=dict(ds);core.pop("dataset_sha256",None)
 if h!=_hist_hash(core):return False
 for r in ds.get("races",[]):
  rh=r.get("content_sha256");rr=dict(r);rr.pop("content_sha256",None)
  if rh!=_hist_hash(rr):return False
 return True
def historical_dataset_to_backtest(ds):
 if not verify_historical_dataset(ds):return {"state":"BLOCKED","reason":"HIST_HASH_INVALID"}
 return backtest_feature_candidate([{"race_id":r["race_id"],"source_rows":r["source_rows"],"lines":r["lines"],"winner":r["winner"]} for r in ds["races"]])

# ===== DEV-B31 Historical Web Evidence Adapter =====
HIST_WEB_SCHEMA="JFE-HIST-WEB-EVIDENCE/1.0"
def parse_result_summary_text(text,target_date,venue,source_url,acquired_at):
    if target_date.replace("-","年",1)[:4] not in text and target_date.replace("-","/") not in text:
        pass
    races=[]
    # Supports KDreams rendered text fragments: "1R... 1着 ... 3小堺..."
    blocks=re.split(r'(?=\b\d{1,2}R)',text)
    for b in blocks:
        mm=re.match(r'(\d{1,2})R',b.strip())
        if not mm:continue
        rm=re.search(r'1着\s*(?:\||:)?\s*(\d+)\s*([^\s|]+(?:\s+[^\s|]+)?)',b)
        if not rm:continue
        races.append({"race_no":int(mm.group(1)),"winner":int(rm.group(1)),
                      "winner_name":rm.group(2).strip(),"evidence_text":b[:500]})
    return {"schema":HIST_WEB_SCHEMA,"target_date":target_date,"venue":venue,
            "source_url":source_url,"acquired_at":acquired_at,"races":races,
            "state":"AVAILABLE" if races else "PARTIAL"}
def historical_web_gate(evidence):
    reasons=[]
    if not evidence.get("source_url"):reasons.append("SOURCE_URL")
    if not evidence.get("acquired_at"):reasons.append("ACQUIRED_AT")
    if not evidence.get("races"):reasons.append("NO_RESULTS")
    return {"state":"AVAILABLE" if not reasons else "BLOCKED","reasons":reasons}

# ===== DEV-B32 Historical Meeting Batch Adapter =====
HIST_BATCH_SCHEMA="JFE-HIST-MEETING-BATCH/1.0"
def build_historical_meeting_batch(target_date,venue,source_url,races,acquired_at):
    seen=set(); out=[]; rejected=[]
    for r in races:
        rn=int(r["race_no"])
        if rn in seen: rejected.append({"race_no":rn,"reason":"DUPLICATE_RACE"});continue
        seen.add(rn)
        if not r.get("top3") or len(r["top3"])<3: rejected.append({"race_no":rn,"reason":"RESULT_INCOMPLETE"});continue
        if not r.get("line_order"): rejected.append({"race_no":rn,"reason":"LINE_MISSING"});continue
        out.append(r)
    return {"schema":HIST_BATCH_SCHEMA,"target_date":target_date,"venue":venue,"source_url":source_url,
            "acquired_at":acquired_at,"races":out,"rejected":rejected,
            "race_count":len(out),"state":"AVAILABLE" if out and not rejected else "PARTIAL"}

# ===== DEV-B33 Historical Snapshot Reconciliation =====
RECON_SCHEMA="JFE-HIST-RECONCILIATION/1.0"

def _race_key(r):
    return (str(r.get("target_date","")), str(r.get("venue","")), int(r.get("race_no",0)))

def reconcile_historical_snapshots(list_snapshot, individual_snapshots):
    """
    Fail-closed reconciliation.
    List snapshot remains immutable. Individual race evidence may recover stale/missing list races
    only when date/venue/race binding is exact and result is complete.
    """
    date=str(list_snapshot.get("target_date",""))
    venue=str(list_snapshot.get("venue",""))
    merged={}
    conflicts=[]
    recovered=[]
    rejected=[]

    for r in list_snapshot.get("races",[]):
        x=dict(r); x["target_date"]=date; x["venue"]=venue
        merged[_race_key(x)]={"record":x,"authority":"LIST","state":"AVAILABLE"}

    for raw in individual_snapshots:
        r=dict(raw)
        reasons=[]
        if str(r.get("target_date","")) != date: reasons.append("DATE_BINDING_ERROR")
        if str(r.get("venue","")) != venue: reasons.append("VENUE_BINDING_ERROR")
        if not r.get("race_no"): reasons.append("RACE_BINDING_ERROR")
        if not r.get("top3") or len(r.get("top3",[])) < 3: reasons.append("RESULT_INCOMPLETE")
        if reasons:
            rejected.append({"race_no":r.get("race_no"),"reasons":reasons}); continue
        key=_race_key(r)
        if key in merged:
            old=merged[key]["record"]
            if old.get("top3") and list(old["top3"]) != list(r["top3"]):
                conflicts.append({"race_no":r["race_no"],"list_top3":old["top3"],
                                  "individual_top3":r["top3"],"state":"SOURCE_CONFLICT"})
                merged[key]["state"]="CONFLICT"
                continue
            # Same result: individual evidence enriches but does not rewrite the list evidence.
            merged[key]={"record":r,"authority":"INDIVIDUAL_CONFIRMED","state":"AVAILABLE",
                         "list_evidence":old}
        else:
            merged[key]={"record":r,"authority":"INDIVIDUAL_RECOVERY","state":"AVAILABLE"}
            recovered.append(int(r["race_no"]))

    available=[v["record"] | {"reconciliation_authority":v["authority"]}
               for k,v in sorted(merged.items(),key=lambda kv:kv[0][2]) if v["state"]=="AVAILABLE"]
    state="AVAILABLE" if available and not conflicts and not rejected else "PARTIAL"
    return {"schema":RECON_SCHEMA,"target_date":date,"venue":venue,"state":state,
            "races":available,"race_count":len(available),
            "recovered_races":sorted(recovered),"conflicts":conflicts,"rejected":rejected}

def reconciliation_gate(recon, expected_race_numbers=None):
    if recon.get("conflicts"): return {"state":"BLOCKED","reason":"SOURCE_CONFLICT"}
    if expected_race_numbers is not None:
        got={int(r["race_no"]) for r in recon.get("races",[])}
        exp={int(x) for x in expected_race_numbers}
        if got != exp:
            return {"state":"PARTIAL","reason":"RACE_COVERAGE_INCOMPLETE",
                    "missing":sorted(exp-got),"unexpected":sorted(got-exp)}
    return {"state":"AVAILABLE","race_count":len(recon.get("races",[]))}


# DEV-B36 actual production server start after all integrated definitions.
if __name__=="__main__":
 ThreadingHTTPServer(("0.0.0.0",int(os.getenv("PORT","10000"))),S).serve_forever()
