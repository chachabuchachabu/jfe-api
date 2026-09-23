import ast,pathlib,re,unittest
S=(pathlib.Path(__file__).parent/"start.py").read_text()
class T(unittest.TestCase):
 def test_ast(self): ast.parse(S)
 def test_version(self): self.assertIn('VERSION="1.0.0-ic1.4-dev-b42"',S)
 def test_endpoint(self): self.assertIn('/v1/race-identity-gate/',S)
 def test_link_bound_gate(self): self.assertIn("def race_identity_evidence",S); self.assertIn('if "race" not in h.lower()',S)
 def test_meeting_binding(self): self.assertIn("re.escape(meeting_id)",S); self.assertIn("if meeting_id in h:",S)
 def test_no_12_assumption(self):
  b=S[S.index("def race_identity_evidence"):S.index("# ===== DEV-B41",S.index("def race_identity_evidence"))]
  self.assertNotIn("range(1,13)",b); self.assertNotIn("<= 12",b)
 def test_no_24_patch(self):
  b=S[S.index("def race_identity_evidence"):S.index("# ===== DEV-B41",S.index("def race_identity_evidence"))]
  self.assertNotIn("!= 24",b); self.assertNotIn("== 24",b)
 def test_verifier_uses_gate(self): self.assertIn("races,race_ev=enumerate_bound_races(raw,mid)",S)
 def test_evidence_preserved(self): self.assertIn('"race_identity_evidence":race_ev',S)
 def test_notpublished_absent(self):
  b=S[S.index("def race_identity_evidence"):S.index("# ===== DEV-B41",S.index("def race_identity_evidence"))]
  self.assertNotIn("NOT_PUBLISHED",b)
 def test_false_positive_fixture_shape(self):
  # Ensure a generic 24R text is not itself an accepted identity source.
  self.assertNotIn(r'(\d{1,2})\s*R\b', S[S.index("def race_identity_evidence"):S.index("# ===== DEV-B41")])
if __name__=="__main__": unittest.main()
