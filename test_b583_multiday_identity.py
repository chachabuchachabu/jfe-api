import importlib.util, pathlib
p=pathlib.Path(__file__).with_name('start.py')
spec=importlib.util.spec_from_file_location('jfe_b583',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
r={'kaisai_date_id':'85202609300200','venue_code':'85','venue_name':'佐世保','race_no':5,
   'source_racedetail_url':'https://keirin.kdreams.jp/sasebo/racedetail/8520260930020005/'}
o=m._b583_normalize_multiday_row(r,'2026-09-30')
assert o['kaisai_date_id']=='85202609290200',o
assert '8520260929020005' in o['source_racedetail_url'],o
assert o['meeting_identity_normalization']['state']=='REPAIRED',o
r1={'kaisai_date_id':'85202609290100','venue_code':'85','venue_name':'佐世保','race_no':5,
   'source_racedetail_url':'https://keirin.kdreams.jp/sasebo/racedetail/8520260929010005/'}
o1=m._b583_normalize_multiday_row(r1,'2026-09-29')
assert o1['kaisai_date_id']=='85202609290100',o1
assert o1['meeting_identity_normalization']['state']=='UNCHANGED',o1
print('B58.3 multiday identity regression: PASS')
