import importlib.util,time
p='start.py'; spec=importlib.util.spec_from_file_location('jfe',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
rows=[{'kaisai_date_id':'85202609300100','venue_code':'85','venue_name':'佐世保','race_no':5,'source_racedetail_url':'https://example.invalid/a'} for _ in range(3)]
orig=m._b561_bind_start
def slow(r,d): time.sleep(6); return r
m._b561_bind_start=slow
t=time.time(); out=m._b561_bind_many(rows,'2026-09-30'); elapsed=time.time()-t
assert elapsed < 5.8, elapsed
assert len(out)==3 and all(x['scheduled_start']['reason']=='IDENTITY_PROBE_DEADLINE_EXCEEDED' for x in out)
m._b561_bind_start=orig
print('PASS bounded deadline',round(elapsed,2))
