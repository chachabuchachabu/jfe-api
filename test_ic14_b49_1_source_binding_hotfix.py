import unittest, importlib.util
from pathlib import Path
P=Path(__file__).with_name('start.py'); spec=importlib.util.spec_from_file_location('jfe',P); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
class T(unittest.TestCase):
 def fixture(self):
  return {'candidate_count':3,'verified_venue_count':1,'venues':[{'state':'VERIFIED_VENUE','venue_code':'43','kaisai_date_id':'43202609260100','races':[1], 'evidence':[{'race_identity_evidence':{1:['https://keirin.kdreams.jp/gifu/racedetail/4320260926010001/']}}]}]}
 def test_b48_4_shape_selects(self):
  c,d=m.select_source_bound_race_b491(self.fixture()); self.assertIsNotNone(c); self.assertEqual(c[1],1); self.assertIn('/gifu/racedetail/',c[2])
 def test_string_key_selects(self):
  x=self.fixture(); x['venues'][0]['evidence'][0]['race_identity_evidence']={'1':['https://keirin.kdreams.jp/gifu/racedetail/4320260926010001/']}; self.assertIsNotNone(m.select_source_bound_race_b491(x)[0])
 def test_old_meeting_state_not_required(self):
  x=self.fixture(); x['venues'][0]['meeting_state']='OTHER'; self.assertIsNotNone(m.select_source_bound_race_b491(x)[0])
 def test_nonverified_rejected(self):
  x=self.fixture(); x['venues'][0]['state']='PARTIAL'; c,d=m.select_source_bound_race_b491(x); self.assertIsNone(c); self.assertEqual(d['rejected'][0]['reason'],'NOT_VERIFIED_VENUE')
 def test_diag_counts(self):
  c,d=m.select_source_bound_race_b491(self.fixture()); self.assertEqual(d['evidence_items_scanned'],1); self.assertEqual(d['identity_keys_found'],1); self.assertEqual(d['url_candidates_checked'],1)
 def test_no_identity_fails_closed(self):
  x=self.fixture(); x['venues'][0]['evidence']=[{}]; c,d=m.select_source_bound_race_b491(x); self.assertIsNone(c); self.assertEqual(d['identity_keys_found'],0)
 def test_version(self): self.assertEqual(m.VERSION,'1.0.0-ic1.4-dev-b49.1')
if __name__=='__main__': unittest.main()
