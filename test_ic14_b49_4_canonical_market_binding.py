import importlib.util
spec=importlib.util.spec_from_file_location('jfe','/mnt/data/b494/start.py'); j=importlib.util.module_from_spec(spec); spec.loader.exec_module(j)

def table(text,cls=''):
 return f'<table class="{cls}"><tr><td>{text}</td></tr></table>'
active=[1,2,3]
# complete 3-car fixtures: wide/quinella 3, exacta 6, trio 1; trifecta deliberately pending via bt5
raw=''.join([
 table('1 1=2 2.3～6.7 2 1=3 9999.9～9999.9 3 2=3 4.0～13.5'),
 table('1 1=2 10.5 2 1=3 9999.9 3 2=3 5.2'),
 table('1 1-2 9.7 2 1-3 4.8 3 2-1 9999.9 4 2-3 9.7 5 3-1 9.7 6 3-2 9999.9'),
 table('1 1=2=3 7.9'),
 table('1 2 3 9.7 9999.9','odds_table bt5')
])
r=j.canonical_market_bind_b494(raw,active)
assert r['state']=='PARTIAL'
for bt in ('wide','quinella','exacta','trio'): assert r['sections'][bt]['state']=='AVAILABLE',bt
assert r['sections']['wide']['quotes'][1]['odds_min']==9999.9
assert r['sections']['wide']['quotes'][1]['odds_max']==9999.9
assert r['sections']['quinella']['expected_unique_count']==3
assert r['sections']['exacta']['expected_unique_count']==6
assert r['sections']['trio']['expected_unique_count']==1
assert r['sections']['trifecta']['state']=='PARTIAL'
assert r['sections']['trifecta']['reason']=='BT5_CELL_COORDINATE_BINDING_PENDING'
assert j.VERSION.endswith('b49.4')
print('9/9 PASS')
