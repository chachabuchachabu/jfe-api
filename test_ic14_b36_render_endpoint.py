import ast,pathlib,re,unittest
P=pathlib.Path(__file__).parent/"start.py"; S=P.read_text()
class T(unittest.TestCase):
 def test_compile_ast(self): ast.parse(S)
 def test_version_b36(self): self.assertIn('VERSION="1.0.0-ic1.4-dev-b36"',S)
 def test_endpoint_exists(self): self.assertIn('p=="/v1/acquisition/test"',S)
 def test_available_requires_body(self):
  self.assertIn('"state":"AVAILABLE"',S); self.assertIn("body=x.read()",S); self.assertIn("hashlib.sha256(body)",S)
 def test_error_not_notpublished(self):
  block=S[S.index('if p=="/v1/acquisition/test"'):S.index('tm=re.fullmatch',S.index('if p=="/v1/acquisition/test"'))]
  self.assertIn('"state":"ERROR"',block); self.assertNotIn("NOT_PUBLISHED",block)
 def test_server_start_once_and_at_end(self):
  self.assertEqual(S.count('serve_forever()'),1)
  self.assertGreater(S.rfind('serve_forever()'),S.rfind('def reconciliation_gate'))
 def test_provenance_fields(self):
  for x in ["source_url","acquired_at","transport","http_status","byte_length","content_sha256","fabricated_data"]: self.assertIn(x,S)
if __name__=="__main__":unittest.main()
