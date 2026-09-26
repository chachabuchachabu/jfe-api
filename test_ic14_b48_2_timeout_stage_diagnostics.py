import unittest, pathlib, importlib.util
P=pathlib.Path(__file__).with_name('start.py')
spec=importlib.util.spec_from_file_location('jfe',P); j=importlib.util.module_from_spec(spec); spec.loader.exec_module(j)
class B482(unittest.TestCase):
 def test_version(self): self.assertEqual(j.VERSION,'1.0.0-ic1.4-dev-b48.2')
 def test_schema_present(self): self.assertIn('JFE-LIVE-ODDS-DOM-PROBE/0.3',P.read_text())
 def test_hard_stage_guard(self):
  r=j._bounded_stage('X',.05,lambda:__import__('time').sleep(.2))
  self.assertEqual(r['state'],'TIMEOUT')
 def test_stage_success(self):
  r=j._bounded_stage('X',1,lambda:123); self.assertEqual(r['state'],'COMPLETED'); self.assertEqual(r['value'],123)
 def test_always_respond_flag(self): self.assertIn('"always_respond_policy":True',P.read_text())
 def test_budget(self): self.assertIn('"time_budget_seconds":30',P.read_text())
 def test_single_fetch_timeout(self): self.assertIn('urlopen(q,timeout=5)',P.read_text())
 def test_no_not_published(self): self.assertNotIn('"NOT_PUBLISHED"',P.read_text()[P.read_text().index('def live_odds_dom_probe'):P.read_text().index('# ===== DEV-B43.2')])
 def test_diagnostic_stages(self):
  t=P.read_text(); self.assertIn('"pre_race_lock"',t); self.assertIn('"entry_binding"',t); self.assertIn('"odds_fetch"',t)
if __name__=='__main__': unittest.main()
