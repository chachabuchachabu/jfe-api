import ast,pathlib,unittest
S=(pathlib.Path(__file__).parent/"start.py").read_text()
class T(unittest.TestCase):
 def test_ast(self):ast.parse(S)
 def test_version(self):self.assertIn('VERSION="1.0.0-ic1.4-dev-b40"',S)
 def test_endpoint(self):self.assertIn('/v1/meeting-discovery/',S)
 def test_date_binding(self):self.assertIn('mid[2:10]==compact',S)
 def test_candidate_only(self):self.assertIn('"verification_state":"CANDIDATE_ONLY"',S);self.assertIn('"state":"DISCOVERED_CANDIDATE"',S)
 def test_no_notpublished(self):
  b=S[S.index("def discover_target_meeting_ids"):S.index("# ===== DEV-B39",S.index("def discover_target_meeting_ids"))]
  self.assertNotIn("NOT_PUBLISHED",b)
 def test_dynamic_count(self):self.assertIn('"meeting_count":len(meetings)',S)
 def test_href_extraction(self):self.assertIn('href\\s*=\\s*',S)
 def test_provenance(self):
  for x in ["content_sha256","byte_length","acquired_at","http_status","fabricated_data"]:self.assertIn(x,S)
 def test_no_fixed_venue_count(self):
  b=S[S.index("def discover_target_meeting_ids"):S.index("# ===== DEV-B39",S.index("def discover_target_meeting_ids"))]
  self.assertNotIn("range(12)",b)
if __name__=="__main__":unittest.main()
