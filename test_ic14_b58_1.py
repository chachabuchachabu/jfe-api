import importlib.util
sp=importlib.util.spec_from_file_location('j','/mnt/data/b581/start.py'); j=importlib.util.module_from_spec(sp); sp.loader.exec_module(j)
# Parser fixture mirrors discovered KDreams result semantics; no network.
raw='''<html><title>佐世保競輪 レース詳細 | 5R | 2026年09月30日</title><table><tr><th>予想</th><th>着順</th><th>車番</th><th>選手名</th></tr><tr><td>◎</td><td>1</td><td>2</td><td>福島 栄一</td></tr><tr><td></td><td>2</td><td>1</td><td>上野 恭哉</td></tr><tr><td></td><td>3</td><td>4</td><td>眞砂 英作</td></tr></table></html>'''
riders=[{'car_no':1,'rider_name':'上野 恭哉'},{'car_no':2,'rider_name':'福島 栄一'},{'car_no':4,'rider_name':'眞砂 英作'}]
rows=j._b581_parse_result_table(raw,riders)
assert [x['car_no'] for x in rows]==[2,1,4],rows
# Pre-start must be NOT_PUBLISHED without network fetch.
j._b56_jst_now=lambda: j.datetime.fromisoformat('2026-09-30T07:00:00+09:00')
tr={'target_date':'2026-09-30','selected_target':{'kaisai_date_id':'85202609300100','venue_code':'85','venue_name':'佐世保','race_no':5,'source_racedetail_url':'https://example.invalid/x','scheduled_start':{'value':'2026-09-30T10:00:00+09:00'}}}
r=j._b581_official_result(tr,riders)
assert r['state']=='NOT_PUBLISHED' and r['chronology']['after_scheduled_start'] is False,r
print('B58.1 tests PASS')
