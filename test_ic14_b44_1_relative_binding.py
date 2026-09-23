import pathlib,unittest
S=(pathlib.Path(__file__).parent/"start.py").read_text(); ns={}; exec(compile(S,"start.py","exec"),ns)
NORMAL='''<table class="racecard_table"><tr><th>車番</th></tr><tr class="n1 "><td></td><td></td><td></td><td class="bracket">1</td><td class="num"><span>1</span></td><td class="rider bdr_r">山田 太郎<br><span class="home">東京/30/100</span></td><td>A1</td><td>逃</td><td>3.92</td><td>88.12</td></tr></table>'''
NO_BRACKET='''<table class="racecard_table"><tr><th>車番</th></tr><tr class="n7 "><td></td><td></td><td></td><td class="num"><span>7</span></td><td class="rider bdr_r">七番 太郎<br><span class="home">大阪/31/101</span></td><td>S1</td><td>追</td><td>3.92</td><td>107.55</td></tr></table>'''
class T(unittest.TestCase):
 def test_version(self): self.assertIn("dev-b44.1",S)
 def test_normal_grade(self): self.assertEqual(ns["parse_primary_racecard_entries"](NORMAL)["entries"][0]["grade"],"A1")
 def test_normal_score(self): self.assertEqual(ns["parse_primary_racecard_entries"](NORMAL)["entries"][0]["race_score"],88.12)
 def test_missing_bracket_grade(self): self.assertEqual(ns["parse_primary_racecard_entries"](NO_BRACKET)["entries"][0]["grade"],"S1")
 def test_missing_bracket_score(self): self.assertEqual(ns["parse_primary_racecard_entries"](NO_BRACKET)["entries"][0]["race_score"],107.55)
 def test_car7(self): self.assertEqual(ns["parse_primary_racecard_entries"](NO_BRACKET)["entries"][0]["car_no"],7)
 def test_no_absolute_grade(self): self.assertNotIn("grade=cells[6]",S)
 def test_no_absolute_score(self): self.assertNotIn("score=float(cells[9])",S)
 def test_rider_anchor(self): self.assertIn("rider_idx",S)
 def test_no_notpublished(self):
  b=S[S.index("# ===== DEV-B44"):S.index("# ===== DEV-B43.2")]; self.assertNotIn("NOT_PUBLISHED",b)
 def test_schema_kept(self): self.assertIn("JFE-COMPACT-ENTRY-BINDING/0.1",S)
if __name__=="__main__": unittest.main()
