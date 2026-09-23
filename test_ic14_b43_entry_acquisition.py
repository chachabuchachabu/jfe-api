import ast,pathlib,unittest
S=(pathlib.Path(__file__).parent/"start.py").read_text()
class T(unittest.TestCase):
 def test_ast(self): ast.parse(S)
 def test_version(self): self.assertIn('VERSION="1.0.0-ic1.4-dev-b43"',S)
 def test_endpoint(self): self.assertIn('/v1/entry-acquisition/',S)
 def test_verified_only(self): self.assertIn('venue.get("state")!="VERIFIED_VENUE"',S)
 def test_canonical_url(self): self.assertIn("canonical_racedetail_url",S)
 def test_no_fixed_rider_count(self):
  b=S[S.index("def live_entry_acquisition"):S.index("# ===== DEV-B42",S.index("def live_entry_acquisition"))]
  self.assertNotIn("range(1,8)",b); self.assertNotIn("range(1,10)",b)
 def test_probe_only(self): self.assertIn('"entry_binding_state":"PROBE_ONLY"',S)
 def test_no_notpublished(self):
  b=S[S.index("def live_entry_acquisition"):S.index("# ===== DEV-B42",S.index("def live_entry_acquisition"))]
  self.assertNotIn("NOT_PUBLISHED",b)
 def test_isolation(self): self.assertIn("for race_no in venue.get",S); self.assertIn("except Exception as e:",S)
 def test_provenance(self):
  for x in ["content_sha256","byte_length","http_status","race_url","acquired_at"]: self.assertIn(x,S)
 def test_probe_fields(self):
  for x in ["racer_links","contexts","car_tokens"]: self.assertIn(x,S)
 def test_no_available_promotion(self):
  b=S[S.index("def live_entry_acquisition"):S.index("# ===== DEV-B42",S.index("def live_entry_acquisition"))]
  self.assertNotIn('"entry_binding_state":"AVAILABLE"',b)
 def test_recovery(self): self.assertIn("ENTRY_FETCH_ERROR",S); self.assertIn("CANONICAL_RACE_URL_MISSING",S)
if __name__=="__main__": unittest.main()
