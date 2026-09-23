import ast,pathlib,unittest
S=(pathlib.Path(__file__).parent/"start.py").read_text()
class T(unittest.TestCase):
 def test_ast(self):ast.parse(S)
 def test_version(self):self.assertIn('VERSION="1.0.0-ic1.4-dev-b41"',S)
 def test_endpoint(self):self.assertIn('/v1/race-verification/',S)
 def test_source_url_binding(self):self.assertIn('"racecard" not in h.lower()',S)
 def test_date_binding(self):self.assertIn('mid[2:10] != compact',S)
 def test_dynamic_races(self):self.assertIn('enumerate_races_from_racecard',S);self.assertNotIn('range(1,13)',S)
 def test_verification_gate(self):self.assertIn('status==200 and races',S);self.assertIn('"VERIFIED_VENUE"',S)
 def test_failure_not_notpublished(self):
  b=S[S.index("def live_race_verification"):S.index("# ===== DEV-B40",S.index("def live_race_verification"))]
  self.assertNotIn("NOT_PUBLISHED",b);self.assertIn("RACE_VERIFICATION_INCOMPLETE",b)
 def test_hashes(self):self.assertIn("content_sha256",S);self.assertIn("root_content_sha256",S)
 def test_isolation(self):self.assertIn("for mid,urls in candidates.items()",S);self.assertIn("except Exception as e:",S)
 def test_candidate_no_fixed_venue_map(self):
  b=S[S.index("def discover_meeting_racecard_urls"):S.index("# ===== DEV-B40",S.index("def discover_meeting_racecard_urls"))]
  self.assertNotIn("VENUES",b)
if __name__=="__main__":unittest.main()
