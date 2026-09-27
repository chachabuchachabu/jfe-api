import importlib.util
spec=importlib.util.spec_from_file_location('jfe','start.py'); j=importlib.util.module_from_spec(spec); spec.loader.exec_module(j)
base={'race_id':{'kaisai_date_id':'x','venue_code':'13','race_no':1},'riders':[{'car_no':i,'grade':'L1'} for i in range(1,8)],'lines':{'state':'UNKNOWN','formations':[]},'market':{'state':'AVAILABLE'},'quality':{'completeness':{'entry':True,'market_all_5_bet_types':True},'schema_validity':True,'timestamp_integrity':True,'cross_source_match':{'state':'UNKNOWN'},'outlier_safety':{'state':'UNKNOWN'}},'provenance':{}}
a=j.build_je_integration_b51(base)
assert a['race_type']=='GIRLS_KEIRIN' and a['lines']['state']=='NOT_APPLICABLE'
assert 'LINES_UNKNOWN' not in a['data_gate']['blockers']
assert set(a['data_gate']['blockers'])=={'CROSS_SOURCE_MATCH_UNKNOWN','OUTLIER_SAFETY_UNKNOWN'}
assert a['execution']['state']=='NOT_EXECUTED' and not a['legacy_neutral_default_adapter_used']
b=dict(base); b['riders']=[{'car_no':1,'grade':'A1'},{'car_no':2,'grade':'A1'}]
c=j.build_je_integration_b51(b)
assert 'LINES_UNKNOWN' in c['data_gate']['blockers']
d=dict(base); d['quality']=dict(base['quality']); d['quality']['cross_source_match']={'state':'AVAILABLE'}; d['quality']['outlier_safety']={'state':'AVAILABLE'}
e=j.build_je_integration_b51(d)
assert e['data_gate']['state']=='PASS' and e['execution']['state']=='READY'
print('B51_LOCAL_TEST_PASS')
