import importlib.util
spec=importlib.util.spec_from_file_location('jfe','/mnt/data/b521work/start.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ri={'race_id':{'venue_code':'13','race_no':1},'riders':[{'car_no':1,'rider_name':'太田 瑛美'},{'car_no':2,'rider_name':'松井 優佳'}],'quality':{},'provenance':{}}
old=m._B521_ADAPTERS
def fail(*a):return {'source':'ODDSPARK','adapter':'x','state':'UNKNOWN','error_type':'TimeoutError'}
def ok(*a):return {'source':'NETKEIRIN','adapter':'y','state':'AVAILABLE','checks':{'full_car_rider_binding':True}}
m._B521_ADAPTERS=(('ODDSPARK',fail),('NETKEIRIN',ok))
o,e=m.apply_cross_source_b521(ri,'2026-09-27')
assert e['selected_source']=='NETKEIRIN' and len(e['attempts'])==2
assert o['quality']['cross_source_match']['state']=='AVAILABLE'
def no(*a):return {'source':'NETKEIRIN','adapter':'y','state':'PARTIAL'}
m._B521_ADAPTERS=(('ODDSPARK',fail),('NETKEIRIN',no))
o,e=m.apply_cross_source_b521(ri,'2026-09-27')
assert e['state']=='UNKNOWN' and o['quality']['cross_source_match']['state']=='UNKNOWN'
raw='<table><tr><td>1</td><td>太田 瑛美</td></tr><tr><td>2</td><td>松井 優佳</td></tr></table>'
ev=m._b521_row_car_name_evidence(raw,ri['riders']);assert all(x['car_name_row_match'] for x in ev)
print('B52.1 focused failover tests: PASS')
m._B521_ADAPTERS=old
