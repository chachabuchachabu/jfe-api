import ast,pathlib,unittest
S=(pathlib.Path(__file__).parent/"start.py").read_text()
class T(unittest.TestCase):
 def test_ast(self): ast.parse(S)
 def test_version(self): self.assertIn('VERSION="1.0.0-ic1.4-dev-b43.1"',S)
 def test_endpoint(self): self.assertIn('/v1/entry-summary/',S)
 def test_reuses_b43(self): self.assertIn("full=live_entry_acquisition(target_date)",S)
 def test_compact_fields(self):
  for x in ["racer_link_count","car_tokens","sample_racer_links","sample_context","recovery_count"]: self.assertIn(x,S)
 def test_link_cap(self): self.assertIn("links[:3]",S)
 def test_context_cap(self): self.assertIn("ctx[0][:350]",S)
 def test_no_full_context_array(self):
  b=S[S.index("def compact_entry_diagnostic"):S.index("# ===== DEV-B43",S.index("def compact_entry_diagnostic"))]
  self.assertNotIn('"contexts":ctx',b)
 def test_no_notpublished(self):
  b=S[S.index("def compact_entry_diagnostic"):S.index("# ===== DEV-B43",S.index("def compact_entry_diagnostic"))]
  self.assertNotIn("NOT_PUBLISHED",b)
 def test_no_rider_count_assumption(self):
  b=S[S.index("def compact_entry_diagnostic"):S.index("# ===== DEV-B43",S.index("def compact_entry_diagnostic"))]
  self.assertNotIn("range(1,8)",b); self.assertNotIn("range(1,10)",b)
 def test_totals(self): self.assertIn('"http_200"',S); self.assertIn('"car_token_races"',S)
if __name__=="__main__": unittest.main()
