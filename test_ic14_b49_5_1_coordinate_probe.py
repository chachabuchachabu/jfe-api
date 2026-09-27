import importlib.util
spec=importlib.util.spec_from_file_location('jfe','start.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
raw='''<table class="odds_table bt5"><tr class="r"><th rowspan="2">1</th><td data-x="a">2</td><td>3</td><td>12.3</td></tr></table>'''
r=m._b4951_bt5_cell_probe(raw,[1,2,3])
assert r['bt5_table_count']==1
assert r['tables'][0]['axis_text_candidate']==1
c=r['tables'][0]['rows'][0]['cells']
assert c[0]['rowspan']=='2' and c[1]['data_attrs']['data-x']=='a' and c[2]['text']=='3'
assert r['promotion']=='NONE_DIAGNOSTIC_ONLY'
print('PASS 4/4')
