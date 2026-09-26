import unittest, importlib.util, math
from pathlib import Path
P=Path(__file__).with_name('start.py')
spec=importlib.util.spec_from_file_location('jfe_b49',P); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
class B49(unittest.TestCase):
 def test_expected_counts_dynamic(self):
  self.assertEqual(m._b49_expected_unique_count(9,'wide'),36); self.assertEqual(m._b49_expected_unique_count(7,'wide'),21)
  self.assertEqual(m._b49_expected_unique_count(9,'exacta'),72); self.assertEqual(m._b49_expected_unique_count(9,'trio'),84); self.assertEqual(m._b49_expected_unique_count(9,'trifecta'),504)
 def test_unordered_canonical(self): self.assertEqual(m._b49_canonical_selection('wide',[9,1]),(1,9))
 def test_ordered_canonical(self): self.assertEqual(m._b49_canonical_selection('exacta',[9,1]),(9,1))
 def test_duplicate_same_dedup(self):
  p={'wide':{'state':'AVAILABLE','bet_type_bound':True,'label_evidence':'ワイド','data':[{'selection':[1,2],'odds':2.5},{'selection':[2,1],'odds':2.5}]}}
  s=m.bind_market_snapshot(p,[1,2,3],'2026/09/26 15:29','2026-09-26T06:29:00Z','u','h')
  self.assertEqual(s['sections']['wide']['unique_odds_count'],1); self.assertEqual(s['sections']['wide']['duplicate_same_value_count'],1); self.assertEqual(s['conflict_count'],0)
 def test_duplicate_conflict_fail_closed(self):
  p={'wide':{'state':'AVAILABLE','bet_type_bound':True,'label_evidence':'ワイド','data':[{'selection':[1,2],'odds':2.5},{'selection':[2,1],'odds':3.0}]}}
  s=m.bind_market_snapshot(p,[1,2,3],'t','a','u','h')
  self.assertEqual(s['sections']['wide']['state'],'PARTIAL'); self.assertEqual(s['conflict_count'],1)
 def test_inactive_rejected(self):
  p={'wide':{'state':'AVAILABLE','bet_type_bound':True,'data':[{'selection':[1,9],'odds':2.5}]}}
  s=m.bind_market_snapshot(p,[1,2,3],'t','a','u','h'); self.assertEqual(s['sections']['wide']['unique_odds_count'],0); self.assertGreater(s['sections']['wide']['rejected_count'],0)
 def test_complete_dynamic(self):
  data=[{'selection':[a,b],'odds':2.0+a/10+b/100} for a in [1,2,3] for b in range(a+1,4)]
  s=m.bind_market_snapshot({'wide':{'state':'AVAILABLE','bet_type_bound':True,'data':data}},[1,2,3],'t','a','u','h')
  self.assertTrue(s['sections']['wide']['table_complete']); self.assertEqual(s['sections']['wide']['expected_unique_count'],3)
 def test_snapshot_provenance(self):
  s=m.bind_market_snapshot({},[1,2],'t','a','https://x','abc'); self.assertEqual(s['content_sha256'],'abc'); self.assertFalse(s['fabricated_data']); self.assertFalse(s['bet_type_inference'])
 def test_version(self): self.assertEqual(m.VERSION,'1.0.0-ic1.4-dev-b49')
if __name__=='__main__': unittest.main()
