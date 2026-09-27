import importlib.util
sp=importlib.util.spec_from_file_location('jfe','start.py'); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
r=[{'car_no':1,'rider_name':'太田 瑛美'},{'car_no':2,'rider_name':'松井 優佳'}]
html='車番 1 太田　瑛美 三重 120期 車番 2 松井　優佳 大阪 124期'
ev=m._b52_car_name_evidence(html,r)
assert all(x['name_present'] for x in ev),ev
assert all(x['car_name_neighborhood_match'] for x in ev),ev
assert m._b52_norm_text('太田　瑛美')==m._b52_norm_text('太田 瑛美')
print('B52 focused tests PASS')
