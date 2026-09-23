import ast,pathlib,unittest
S=(pathlib.Path(__file__).parent/"start.py").read_text()
class T(unittest.TestCase):
 def test_ast(self): ast.parse(S)
 def test_version(self): self.assertIn('VERSION="1.0.0-ic1.4-dev-b39"',S)
 def test_endpoint(self): self.assertIn('/v1/body-diagnostics/',S)
 def test_identity_encoding(self): self.assertIn('"Accept-Encoding":"identity"',S)
 def test_diagnostic_fields(self):
  for x in ["body_prefix","tag_counts","keyword_counts","content_encoding","api_like_urls","replacement_char_count"]: self.assertIn(x,S)
 def test_bounded(self): self.assertIn("raw[:1800]",S); self.assertIn("api_like[:40]",S)
 def test_no_promotion(self):
  b=S[S.index("def live_body_diagnostics"):S.index("# ===== DEV-B38",S.index("def live_body_diagnostics"))]
  self.assertNotIn("VERIFIED_VENUE",b); self.assertNotIn("NOT_PUBLISHED",b)
 def test_provenance(self):
  for x in ["content_sha256","byte_length","acquired_at","http_status","fabricated_data","diagnostic_only"]: self.assertIn(x,S)
if __name__=="__main__":unittest.main()
