import unittest, inspect, start
from unittest.mock import patch

class B481(unittest.TestCase):
 def test_version(self): self.assertEqual(start.VERSION,'1.0.0-ic1.4-dev-b48.1')
 def test_schema_and_diagnostics_present(self):
  with patch.object(start,'live_pre_race_lock',return_value={'races':[]}), patch.object(start,'live_entry_binding',return_value={'races':[]}):
   x=start.live_odds_dom_probe('2026-09-23')
  self.assertEqual(x['schema'],'JFE-LIVE-ODDS-DOM-PROBE/0.2'); self.assertIn('binding_diagnostics',x)
  self.assertFalse(x['silent_drop']); self.assertTrue(x['recovery_queue'])
 def test_unique_venue_race_fallback_reaches_fetch(self):
  locks={'races':[{'kaisai_date_id':'OLD','venue_code':'73','race_no':1,'lock_state':'LOCKED','lock_id':'L','active_car_numbers':[1,2]}]}
  binding={'races':[{'kaisai_date_id':'NEW','venue_code':'73','race_no':1,'race_url':'https://keirin.kdreams.jp/x/racedetail/1234567890123456/'}]}
  class Resp:
   status=200; headers={'Content-Type':'text/html'}
   def __enter__(self): return self
   def __exit__(self,*a): pass
   def read(self): return 'ワイド 1-2 2.5'.encode()
  with patch.object(start,'live_pre_race_lock',return_value=locks), patch.object(start,'live_entry_binding',return_value=binding), patch.object(start.urllib.request,'urlopen',return_value=Resp()):
   x=start.live_odds_dom_probe('2026-09-23')
  self.assertEqual(x['sample_count'],1); self.assertEqual(x['samples'][0]['source_binding_mode'],'VENUE_RACE_UNIQUE_FALLBACK')
  self.assertEqual(x['binding_diagnostics']['fetch_attempts'],1)
 def test_ambiguous_binding_fails_closed(self):
  locks={'races':[{'kaisai_date_id':'OLD','venue_code':'73','race_no':1,'lock_state':'LOCKED','lock_id':'L','active_car_numbers':[1,2]}]}
  binding={'races':[{'kaisai_date_id':'A','venue_code':'73','race_no':1,'race_url':'https://keirin.kdreams.jp/x/racedetail/1234567890123456/'},{'kaisai_date_id':'B','venue_code':'73','race_no':1,'race_url':'https://keirin.kdreams.jp/y/racedetail/2234567890123456/'}]}
  with patch.object(start,'live_pre_race_lock',return_value=locks), patch.object(start,'live_entry_binding',return_value=binding): x=start.live_odds_dom_probe('2026-09-23')
  self.assertEqual(x['sample_count'],0); self.assertEqual(x['recovery_queue'][0]['reason'],'AMBIGUOUS_SOURCE_BINDING')
 def test_no_second_b42_walk(self):
  src=inspect.getsource(start.live_odds_dom_probe); self.assertNotIn('live_race_verification',src); self.assertIn('live_entry_binding',src)
 def test_seen_after_source_binding(self):
  src=inspect.getsource(start.live_odds_dom_probe); self.assertLess(src.index('if not odds_url'),src.index('seen.add(vc)'))
 def test_no_not_published_fabrication(self):
  src=inspect.getsource(start.live_odds_dom_probe); self.assertNotIn('NOT_PUBLISHED',src)

if __name__=='__main__': unittest.main()
