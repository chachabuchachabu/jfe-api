import ast,pathlib,unittest
S=(pathlib.Path(__file__).parent/"start.py").read_text()
class T(unittest.TestCase):
 def test_ast(self): ast.parse(S)
 def test_version(self): self.assertIn('VERSION="1.0.0-ic1.4-dev-b43.2"',S)
 def test_endpoint(self): self.assertIn('/v1/dom-probe/',S)
 def test_one_per_venue(self): self.assertIn('race_no=venue["races"][0]',S)
 def test_source_bound_url(self): self.assertIn("canonical_racedetail_url(urls)",S)
 def test_structure_counts(self):
  for x in ["table_count","tr_count","td_count"]: self.assertIn(x,S)
 def test_structure_names(self):
  for x in ["sample_classes","sample_ids","data_attributes"]: self.assertIn(x,S)
 def test_bounded_tables(self): self.assertIn("len(tables)>=8",S); self.assertIn("700",S)
 def test_bounded_contexts(self): self.assertIn("len(contexts)>=16",S); self.assertIn("650",S)
 def test_keywords(self):
  for x in ["車番","選手名","級班","競走得点","期別"]: self.assertIn(x,S)
 def test_diagnostic_only(self): self.assertIn('"parser_promotion":"NONE_DIAGNOSTIC_ONLY"',S)
 def test_no_notpublished(self):
  b=S[S.index("def live_dom_probe"):S.index("# ===== DEV-B43.1",S.index("def live_dom_probe"))]
  self.assertNotIn("NOT_PUBLISHED",b)
 def test_no_entry_available_claim(self):
  b=S[S.index("def dom_structure_probe"):S.index("def live_dom_probe")]
  self.assertNotIn("entry_binding_state",b)
if __name__=="__main__": unittest.main()
