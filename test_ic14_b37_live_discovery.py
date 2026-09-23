import ast,pathlib,unittest
S=(pathlib.Path(__file__).parent/"start.py").read_text()
class T(unittest.TestCase):
 def test_ast(self):ast.parse(S)
 def test_version(self):self.assertIn('VERSION="1.0.0-ic1.4-dev-b37"',S)
 def test_endpoint(self):self.assertIn('/v1/discovery/',S)
 def test_dynamic_parser_reuse(self):self.assertIn('discover_venues_from_html(raw,target_date)',S)
 def test_no_false_not_published(self):
  b=S[S.index("def live_daily_discovery"):S.index("class S(",S.index("def live_daily_discovery"))]
  self.assertNotIn("NOT_PUBLISHED",b);self.assertIn('"state":"ERROR"',b);self.assertIn('"UNKNOWN"',b)
 def test_evidence(self):
  for x in ["content_sha256","byte_length","acquired_at","source_url","http_status","fabricated_data"]:self.assertIn(x,S)
 def test_no_fixed_count(self):
  b=S[S.index("def live_daily_discovery"):S.index("class S(",S.index("def live_daily_discovery"))]
  self.assertIn("len(venues)",b);self.assertNotIn("range(12)",b)
if __name__=="__main__":unittest.main()
