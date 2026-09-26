import importlib.util, pathlib, time
P=pathlib.Path(__file__).with_name('start.py')
spec=importlib.util.spec_from_file_location('jfe',P); j=importlib.util.module_from_spec(spec); spec.loader.exec_module(j)

def test_version_and_schema():
 assert j.VERSION.endswith('b49.2')
 r=j._b49_response('2026-09-27',time.time(),{}, {}, [], 'ERROR')
 assert r['schema']=='JFE-LIVE-MARKET-BINDING/0.2'

def test_bounded_stage_times_out():
 def hang(): time.sleep(.15)
 r=j._bounded_stage('TEST',.02,hang)
 assert r['state']=='TIMEOUT'

def test_source_binding_reuses_verified_evidence():
 base={'candidate_count':1,'verified_venue_count':1,'venues':[{'state':'VERIFIED_VENUE','venue_code':'43','kaisai_date_id':'x','races':[1],'evidence':[{'race_identity_evidence':{1:['https://keirin.kdreams.jp/gifu/racedetail/4320260926010001/']}}]}]}
 c,d=j.select_source_bound_race_b491(base)
 assert c and c[1]==1 and d['url_candidates_checked']==1

def test_expected_counts_dynamic():
 assert j._b49_expected_unique_count(9,'wide')==36
 assert j._b49_expected_unique_count(7,'wide')==21
 assert j._b49_expected_unique_count(9,'trifecta')==504
