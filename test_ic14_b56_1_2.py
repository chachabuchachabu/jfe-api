import start

def html(date='2026年09月30日',venue='防府',race='1',st='08:30'):
    return f'''<html><head><title>{venue}競輪 レース詳細 | X {race}R Ａ級一般 | {date}【楽天Kドリームス】</title></head><body><div class="racecard_header"><dl class="time"><dt class="start">発走予定</dt><dd>{st}</dd><dt class="bet">投票締切</dt><dd>08:25</dd></dl></div><p>2026/09/30 00:00現在</p><p>投票締切22:31</p></body></html>'''

e=start._b5612_page_identity_and_start(html())
assert e['page_date']=='2026-09-30' and e['page_venue_name']=='防府' and e['page_race_no']==1
assert (e['start_hh'],e['start_mm'])==(8,30)
# Generic odds/sidebar times must not replace racecard header start.
e2=start._b5612_page_identity_and_start(html(st='10:45'))
assert (e2['start_hh'],e2['start_mm'])==(10,45)
# Missing start contract remains unresolved.
e3=start._b5612_page_identity_and_start(html().replace('class="start"','class="other"'))
assert e3['start_hh'] is None
print('B56.1.2 parser tests PASS')
