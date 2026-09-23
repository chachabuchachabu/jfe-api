import ast,pathlib,unittest
S=(pathlib.Path(__file__).parent/"start.py").read_text()
class T(unittest.TestCase):
 def test_ast(self):ast.parse(S)
 def test_version(self):self.assertIn('VERSION="1.0.0-ic1.4-dev-b38"',S)
 def test_probe_endpoint(self):self.assertIn('/v1/discovery-probe/',S)
 def test_structure_fields(self):
  for x in ["href_count","unique_href_count","relevant_hrefs","date_tokens","truncated"]:self.assertIn(x,S)
 def test_no_promotion(self):
  b=S[S.index("def live_discovery_probe"):S.index("# ===== DEV-B37",S.index("def live_discovery_probe"))]
  self.assertNotIn("VERIFIED_VENUE",b);self.assertNotIn("NOT_PUBLISHED",b)
 def test_provenance(self):
  for x in ["content_sha256","byte_length","acquired_at","http_status","fabricated_data"]:self.assertIn(x,S)
 def test_bounded_output(self):self.assertIn("relevant[:80]",S);self.assertIn("date_tokens[:80]",S)
if __name__=="__main__":unittest.main()
