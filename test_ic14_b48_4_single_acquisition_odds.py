import unittest, importlib.util, pathlib
P=pathlib.Path(__file__).with_name('start.py'); spec=importlib.util.spec_from_file_location('jfe',P); j=importlib.util.module_from_spec(spec); spec.loader.exec_module(j)
class T(unittest.TestCase):
 def test_version(self): self.assertEqual(j.VERSION,'1.0.0-ic1.4-dev-b48.4')
 def test_odds_url(self): self.assertEqual(j._odds_url_from_racedetail('https://x/racedetail/4320260926010001/'),'https://x/racedetail/4320260926010001/?pageType=odds')
 def test_bad_url(self): self.assertIsNone(j._odds_url_from_racedetail('https://x/racecard/x'))
 def test_bounded_timeout(self): self.assertEqual(j._bounded_stage('X',.01,lambda:__import__('time').sleep(.05))['state'],'TIMEOUT')
 def test_schema_literal(self): self.assertIn('JFE-SINGLE-ACQUISITION-ODDS-PROBE/0.1',P.read_text())
 def test_route_literal(self): self.assertIn('/v1/single-acquisition-odds-probe/',P.read_text())
 def test_no_all_race_pipeline(self): self.assertIn('"all_race_pipeline_executed":False',P.read_text())
 def test_no_bet_inference(self): self.assertIn('"bet_type_inference":False',P.read_text())
 def test_active_guard(self): self.assertIn('"invalid_combination_guard":True',P.read_text())
if __name__=='__main__':unittest.main()
