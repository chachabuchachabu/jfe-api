import importlib.util
p='/mnt/data/b50work/start.py'
spec=importlib.util.spec_from_file_location('jfe',p); j=importlib.util.module_from_spec(spec); spec.loader.exec_module(j)
market={'state':'AVAILABLE','sections':{k:{'state':'AVAILABLE','table_complete':True,'quotes':[]} for k in ('wide','quinella','exacta','trio','trifecta')},'source_url':'https://example/odds','content_sha256':'abc','acquired_at':'2026-09-27T11:03:53Z'}
b={'schema':'JFE-LIVE-CANONICAL-MARKET-BINDING/0.3','version':'x','acquired_at':'2026-09-27T11:03:53Z','result':{'selected_race':{'kaisai_date_id':'13202609270100','venue_code':'13','race_no':1,'source_racedetail_url':'https://example/race','odds_url':'https://example/odds'},'entry':{'state':'AVAILABLE','entry_count':2,'active_car_numbers':[1,2],'entries':[{'car_no':1,'rider_name':'A','prefecture':'X','age':30,'term':100,'grade':'L1','race_score':50.0},{'car_no':2,'rider_name':'B','prefecture':'Y','age':31,'term':101,'grade':'L1','race_score':51.0}]},'market_snapshot':market}}
r=j.build_gpt_race_input_b50(b)
assert r['state']=='READY_FOR_GPT'
assert r['data_gate']['state']=='BLOCKED'
assert 'LINES_UNKNOWN' in r['data_gate']['blockers']
assert 'CROSS_SOURCE_MATCH_UNKNOWN' in r['data_gate']['blockers']
assert r['quality']['coverage_score'] is None
assert r['handoff']['raw_html_included'] is False
assert len(r['riders'])==2
print('B50 focused contract tests: PASS')
