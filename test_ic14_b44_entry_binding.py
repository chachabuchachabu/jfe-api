import ast,pathlib,unittest
S=(pathlib.Path(__file__).parent/"start.py").read_text()
ns={}; exec(compile(S,"start.py","exec"),ns)
FIX='''<table class="racecard_table"><tr><th>車番</th><th>選手名</th></tr>
<tr class="n1 "><td class="tip"></td><td></td><td></td><td class="bracket">1</td><td class="num"><span>1</span></td><td class="rider bdr_r"> 西本 直大<br><span class="home">大 阪/43/92 </span></td><td>A2</td><td>両</td><td>3.92</td><td>86.12</td></tr>
<tr class="n5 "><td class="tip"></td><td></td><td></td><td class="bracket">5</td><td class="num"><span>5</span></td><td class="rider bdr_r"> 増田 仁<br><span class="home">広 島/40/113 </span></td><td>A1</td><td>逃</td><td>3.92</td><td>88.50</td></tr></table>
<table class="racecard_table none"><tr class="n1"><td class="num"><span>1</span></td><td class="rider">DUP<br>広島/1/1</td></tr></table>'''
class T(unittest.TestCase):
 def test_ast(self): ast.parse(S)
 def test_version(self): self.assertIn('dev-b44',S)
 def test_endpoint(self): self.assertIn('/v1/entry-binding/',S)
 def test_parse(self):
  x=ns["parse_primary_racecard_entries"](FIX); self.assertEqual(x["state"],"AVAILABLE"); self.assertEqual(x["retrieved_car_numbers"],[1,5])
 def test_middle_car(self): self.assertEqual(ns["parse_primary_racecard_entries"](FIX)["entries"][1]["rider_name"],"増田 仁")
 def test_home(self):
  e=ns["parse_primary_racecard_entries"](FIX)["entries"][0]; self.assertEqual((e["prefecture"],e["age"],e["term"]),("大阪",43,92))
 def test_grade_score(self):
  e=ns["parse_primary_racecard_entries"](FIX)["entries"][0]; self.assertEqual(e["grade"],"A2"); self.assertEqual(e["race_score"],86.12)
 def test_hidden_duplicate_ignored(self): self.assertEqual(len(ns["parse_primary_racecard_entries"](FIX)["entries"]),2)
 def test_mismatch_blocks(self):
  bad=FIX.replace('class="n5 "','class="n4 "',1); self.assertEqual(ns["parse_primary_racecard_entries"](bad)["state"],"PARTIAL")
 def test_no_fixed_count(self):
  b=S[S.index("def live_entry_binding"):S.index("def compact_entry_binding")]; self.assertNotIn("range(1,8)",b); self.assertNotIn("range(1,10)",b)
 def test_no_notpublished(self):
  b=S[S.index("# ===== DEV-B44"):S.index("# ===== DEV-B43.2")]; self.assertNotIn("NOT_PUBLISHED",b)
 def test_provenance(self):
  for x in ["content_sha256","race_url","http_status","binding_evidence"]: self.assertIn(x,S)
 def test_isolation(self): self.assertIn("ENTRY_FETCH_ERROR",S)
 def test_compact(self): self.assertIn("JFE-COMPACT-ENTRY-BINDING/0.1",S)
if __name__=="__main__": unittest.main()
