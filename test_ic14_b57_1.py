import pathlib, importlib.util
p=pathlib.Path(__file__).with_name('start.py'); spec=importlib.util.spec_from_file_location('jfe',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
raw='''<title>佐世保競輪 レース詳細 | 5R Ａ級特予選 | 2026年09月30日【楽天Kドリームス】</title><dl class="racecard_footer-contents"><dt>並び予想</dt><dd><div class="line_position"><span class="icon_p"><span class="p000">←</span></span><span class="icon_p"><span class="p002">2</span></span><span class="icon_p"><span class="p004">4</span></span><span class="icon_p space"></span><span class="icon_p"><span class="p001">1</span></span><span class="icon_p"><span class="p007">7</span></span><span class="icon_p"><span class="p005">5</span></span><span class="icon_p space"></span><span class="icon_p"><span class="p006">6</span></span><span class="icon_p"><span class="p003">3</span></span></div></dd></dl>'''
m.fetch=lambda u,*a:(raw,1.0,'TEST')
m._b5612_page_identity_and_start=lambda raw:{'page_date':'2026-09-30','page_venue_name':'佐世保','page_race_no':5}
riders=[{'car_no':i} for i in range(1,8)]
r=m._b571_bind_line_formation({'source_racedetail_url':'x','venue_name':'佐世保','race_no':5},'2026-09-30',riders)
assert r['state']=='AVAILABLE',r
assert r['formations']==[[2,4],[1,7,5],[6,3]],r
assert r['integrity']['all_active_cars_exactly_once'] is True
print('B57.1 PASS')
