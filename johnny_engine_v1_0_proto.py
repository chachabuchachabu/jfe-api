from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Optional
from math import exp, log
import hashlib, json, itertools
@dataclass
class Rider:
    number:int; rating:float; form:float; tactical:float
    venue_fit:float=70.0; distance_fit:float=70.0; opponent_context:float=70.0
@dataclass
class Line:
    members:List[int]; cohesion:float=75.0
@dataclass
class MarketQuote:
    bet_type:str; selection:Tuple[int,...]; odds:float; age_minutes:float
@dataclass
class RaceInput:
    race_id:str; riders:List[Rider]; lines:List[Line]; market:List[MarketQuote]
    completeness:float=95.0; source_reliability:float=90.0; cross_source_match:float=90.0
    schema_validity:float=100.0; outlier_safety:float=100.0; timestamp_integrity:float=100.0
    coverage_score:float=90.0
@dataclass
class EngineResult:
    engine_version:str; race_id:str; input_hash:str; data_gate:str; iis:float; dq:float
    model_pick:list; scenario_probabilities:dict; win_probabilities:dict; pic_pass:bool
    best_bet_type:Optional[str]; best_ticket:Optional[Tuple[int,...]]
    model_probability:Optional[float]; odds:Optional[float]; ev:Optional[float]
    ev_score:Optional[float]; je_edge:Optional[float]; confidence:float; consensus:float
    mdi:float; conflict:str; risk:float; risk_band:str; kos:float; decision:str
    status_code:str; warnings:list=field(default_factory=list)
class JohnnyEngineProto:
    VERSION="JE 1.0.0-proto"
    def _hash_input(self,race):
        return hashlib.sha256(json.dumps(asdict(race),sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:16].upper()
    def _freshness_score(self,race):
        if not race.market:return 0.0
        a=sum(q.age_minutes for q in race.market)/len(race.market)
        return 100.0 if a<=2 else 85.0 if a<=5 else 65.0 if a<=10 else 30.0
    def _input_integrity(self,race):
        f=self._freshness_score(race)
        iis=(race.completeness*.25+f*.20+race.source_reliability*.15+race.cross_source_match*.15+race.schema_validity*.10+race.outlier_safety*.10+race.timestamp_integrity*.05)
        dq=iis*.70+race.coverage_score*.30; w=[]
        if f<60:w.append("D02 STALE_ODDS")
        if race.cross_source_match<60:w.append("D04 SOURCE_CONFLICT")
        if race.completeness<70:w.append("D01 MISSING_REQUIRED")
        return iis,dq,w
    def _rider_score(self,r): return r.rating*.40+r.form*.20+r.tactical*.20+r.venue_fit*.07+r.distance_fit*.05+r.opponent_context*.08
    def _line_scores(self,race,rs):
        out={}
        for idx,line in enumerate(race.lines,1):
            v=[rs[n] for n in line.members]
            s=v[0]*.45+v[1]*.35+v[2]*.10+line.cohesion*.10 if len(v)>=3 else v[0]*.55+v[1]*.35+line.cohesion*.10 if len(v)==2 else v[0]*.90+line.cohesion*.10
            out[f"L{idx}"]=s
        return out
    def _scenario_probs(self,race,ls,rs):
        sc={}
        for idx,line in enumerate(race.lines,1):
            rr=[next(r for r in race.riders if r.number==n) for n in line.members]
            ini=min(100,rs[line.members[0]]+5); tac=sum(r.tactical for r in rr)/len(rr); rp=sum(rs[n] for n in line.members)/len(line.members); form=sum(r.form for r in rr)/len(rr); rf=sum((r.venue_fit+r.distance_fit)/2 for r in rr)/len(rr)
            sc[f"S{idx}_LINE_{'-'.join(map(str,line.members))}"]=(ini*.25+ls[f"L{idx}"]*.20+tac*.20+rp*.15+form*.10+rf*.10)/100
        sc["S_CHAOS"]=.45; ex={k:exp(v/.35) for k,v in sc.items()}; z=sum(ex.values()); return {k:v/z for k,v in ex.items()}
    def _scenario_strengths(self,race,rs,sname):
        st=rs.copy()
        if sname!="S_CHAOS":
            nums=[int(x) for x in sname.split("_")[-1].split("-")]
            for pos,n in enumerate(nums): st[n]+=8 if pos==0 else 6 if pos==1 else 3
        else:
            m=sum(st.values())/len(st); st={n:m+(v-m)*.55 for n,v in st.items()}
        return st
    def _pl(self,strengths,k=3):
        w={n:exp(s/12.0) for n,s in strengths.items()}; out={}
        for perm in itertools.permutations(w,k):
            rem=w.copy(); p=1.0
            for n in perm:p*=rem[n]/sum(rem.values()); rem.pop(n)
            out[perm]=p
        return out
    def _probabilities(self,race,sp,rs):
        tri={}
        for sn,sprob in sp.items():
            for order,p in self._pl(self._scenario_strengths(race,rs,sn),3).items():tri[order]=tri.get(order,0)+sprob*p
        z=sum(tri.values()); tri={k:v/z for k,v in tri.items()}; ex={}; qu={}; trio={}; win={r.number:0.0 for r in race.riders}
        for o,p in tri.items():
            ex[o[:2]]=ex.get(o[:2],0)+p; q=tuple(sorted(o[:2])); qu[q]=qu.get(q,0)+p; t=tuple(sorted(o)); trio[t]=trio.get(t,0)+p; win[o[0]]+=p
        return win,ex,qu,trio,tri
    def _pic(self,win,exacta,trifecta): return all(abs(sum(x.values())-1.0)<=1e-4 for x in (win,exacta,trifecta))
    def _bet_prob(self,typ,sel,exacta,quinella,trio,trifecta):
        mp={"2exacta":exacta,"2quinella":quinella,"trio":trio,"trifecta":trifecta}[typ]; key=tuple(sorted(sel)) if typ in ("2quinella","trio") else tuple(sel); return mp.get(key,0)
    def run(self,race):
        ih=self._hash_input(race); iis,dq,w=self._input_integrity(race)
        if iis<70 or dq<60:return EngineResult(self.VERSION,race.race_id,ih,"BLOCKED",iis,dq,[],{}, {},False,None,None,None,None,None,None,None,0,0,100,"CF3",100,"R5",0,"PASS","JE-200",w)
        rs={r.number:self._rider_score(r) for r in race.riders}; ls=self._line_scores(race,rs); sp=self._scenario_probs(race,ls,rs); win,exa,qui,trio,tri=self._probabilities(race,sp,rs); pic=self._pic(win,exa,tri)
        ranked=[n for n,_ in sorted(win.items(),key=lambda kv:kv[1],reverse=True)]; rr=[n for n,_ in sorted(rs.items(),key=lambda kv:kv[1],reverse=True)]; overlap=len(set(ranked[:3])&set(rr[:3])); consensus=min(100,55+overlap*10); mdi=100-consensus; conflict="CF0" if consensus>=85 else "CF1" if consensus>=70 else "CF2" if consensus>=55 else "CF3"
        ps=list(sp.values()); h=-sum(p*log(p) for p in ps if p>0); hs=100*(1-h/log(len(ps))); ss=sorted(ps,reverse=True); ms=min(100,(ss[0]-ss[1])*400) if len(ss)>1 else 100; scen=hs*.60+ms*.40; pv=sorted(win.values(),reverse=True); edge=min(100,max(0,(pv[0]-pv[1])*500)); mkt=self._freshness_score(race); confidence=dq*.20+consensus*.25+scen*.20+edge*.15+mkt*.10+75*.10; risk=mdi*.20+(100-scen)*.20+(100-mkt)*.15+(100-dq)*.15+20*.10+10*.10+25*.10; risk=max(0,min(100,risk)); rb="R1" if risk<25 else "R2" if risk<45 else "R3" if risk<60 else "R4" if risk<75 else "R5"
        best=None
        for q in race.market:
            if q.odds<=1:continue
            p=self._bet_prob(q.bet_type,q.selection,exa,qui,trio,tri); ev=p*q.odds; je=p-(1/q.odds)
            if best is None or ev>best["ev"]:best={"q":q,"p":p,"ev":ev,"edge":je}
        if best:
            evs=100*(1-exp(-6*max(best["ev"]-1,0))); kos=evs*.30+confidence*.25+dq*.10+consensus*.15+(100-risk)*.15+mkt*.05; gate=pic and dq>=70 and confidence>=65 and best["ev"]>=1.08 and best["edge"]>0 and conflict!="CF3" and risk<60
            if gate and kos>=90:dec,code="BET A+","JE-130"
            elif gate and kos>=80:dec,code="BET A","JE-120"
            elif gate and kos>=70:dec,code="BET B","JE-110"
            else:dec,code="PASS","JE-100"
        else:evs=kos=0; best={"q":None,"p":None,"ev":None,"edge":None}; dec,code="PASS","JE-100"
        return EngineResult(self.VERSION,race.race_id,ih,"PASS",iis,dq,ranked[:4],sp,win,pic,best["q"].bet_type if best["q"] else None,tuple(best["q"].selection) if best["q"] else None,best["p"],best["q"].odds if best["q"] else None,best["ev"],evs,best["edge"],confidence,consensus,mdi,conflict,risk,rb,kos,dec,code,w)
