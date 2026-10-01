import importlib.util
sp=importlib.util.spec_from_file_location('j','/mnt/data/jfe_b58_1_work/start.py'); j=importlib.util.module_from_spec(sp); sp.loader.exec_module(j)
assert j.VERSION=='1.0.0-ic1.4-dev-b58.2'
assert j._b581_result_urls('https://keirin.kdreams.jp/sasebo/racedetail/X/?foo=1') == [
 'https://keirin.kdreams.jp/sasebo/racedetail/X/?pageType=showResult',
 'https://keirin.kdreams.jp/sasebo/racedetail/X/?pageType=result']
raw='''<html><title>佐世保競輪 レース詳細 | 5R | 2026年09月30日</title><table><tr><th>予想</th><th>着<br>順</th><th>車<br>番</th><th>選手名</th></tr><tr><td>◎</td><td>1</td><td>2</td><td>福島 栄一</td></tr><tr><td></td><td>2</td><td>1</td><td>上野 恭哉</td></tr><tr><td></td><td>3</td><td>4</td><td>眞砂 英作</td></tr></table></html>'''
riders=[{'car_no':1,'rider_name':'上野 恭哉'},{'car_no':2,'rider_name':'福島 栄一'},{'car_no':4,'rider_name':'眞砂 英作'}]
rows=j._b581_parse_result_table(raw,riders)
assert [x['car_no'] for x in rows]==[2,1,4],rows
print('B58.2 tests PASS')
