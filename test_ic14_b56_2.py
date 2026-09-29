import start
from datetime import datetime, timezone, timedelta

JST=timezone(timedelta(hours=9))
start._b56_jst_now=lambda: datetime(2026,9,30,1,3,tzinfo=JST)
start.live_race_verification=lambda td:{'state':'AVAILABLE'}
start._b56_identity_rows=lambda rv:[
 {'kaisai_date_id':'A','venue_code':'85','venue_name':'佐世保','race_no':2,'source_racedetail_url':'u2','identity_state':'VERIFIED'},
 {'kaisai_date_id':'A','venue_code':'85','venue_name':'佐世保','race_no':1,'source_racedetail_url':'u1','identity_state':'VERIFIED'}]
def bind(rows,td):
 out=[]
 for r in rows:
  x=dict(r); x['scheduled_start']={'state':'AVAILABLE','value':td+('T09:00:00+09:00' if r['race_no']==2 else 'T08:40:00+09:00')}; out.append(x)
 return out
start._b561_bind_many=bind
r=start.resolve_target_b56('NOW')
assert r['state']=='AVAILABLE'
assert r['candidate_count']==2
assert r['selected_target']['race_no']==1
assert r['selected_target']['selection_basis']=='EARLIEST_SOURCE_VERIFIED_UNSTARTED_RACE'
assert r['selection_policy']=='EARLIEST_SOURCE_VERIFIED_UNSTARTED_RACE'
assert r['fabricated_data'] is False
print('PASS')
