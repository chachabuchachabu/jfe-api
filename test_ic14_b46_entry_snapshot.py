import unittest, pathlib, ast, importlib.util
P=pathlib.Path(__file__).with_name('start.py'); S=P.read_text(); ast.parse(S)
spec=importlib.util.spec_from_file_location('jfe',P); j=importlib.util.module_from_spec(spec); spec.loader.exec_module(j)
class T(unittest.TestCase):
 def test_version(self): self.assertEqual(j.VERSION,'1.0.0-ic1.4-dev-b46')
 def test_endpoint(self): self.assertIn('/v1/entry-snapshot/',S)
 def snap(self,name='A',state='AVAILABLE',withdrawals=None):
  payload={'entries':[{'car_no':1,'rider_name':name,'state':state}], 'withdrawals':withdrawals or []}
  return {'snapshot_id':'x','source_hash':'h','payload':payload}
 def test_baseline(self): self.assertEqual(j.compare_entry_snapshots(None,self.snap())['state'],'BASELINE')
 def test_unchanged(self): self.assertEqual(j.compare_entry_snapshots(self.snap(),self.snap())['state'],'UNCHANGED')
 def test_added(self):
  a=self.snap(); b=self.snap(); b['payload']['entries'].append({'car_no':5,'rider_name':'B','state':'AVAILABLE'})
  self.assertEqual(j.compare_entry_snapshots(a,b)['changes'][0]['type'],'ADDED')
 def test_removed_not_withdrawal(self):
  a=self.snap(); a['payload']['entries'].append({'car_no':5,'rider_name':'B','state':'AVAILABLE'}); b=self.snap()
  d=j.compare_entry_snapshots(a,b)['changes'][0]; self.assertEqual(d['type'],'REMOVED'); self.assertFalse(d['withdrawal_inferred'])
 def test_rider_changed(self): self.assertEqual(j.compare_entry_snapshots(self.snap('A'),self.snap('B'))['changes'][0]['type'],'RIDER_CHANGED')
 def test_field_changed(self): self.assertEqual(j.compare_entry_snapshots(self.snap(state='AVAILABLE'),self.snap(state='ERROR'))['changes'][0]['type'],'FIELD_CHANGED')
 def test_withdrawal_explicit_only(self):
  d=j.compare_entry_snapshots(self.snap(),self.snap(withdrawals=[{'car_no':1,'evidence':'source'}])); self.assertTrue(d['changes'][0]['explicit_source_evidence'])
 def test_hash_deterministic(self):
  x={'b':2,'a':1}; self.assertEqual(j._entry_snapshot_hash(x),j._entry_snapshot_hash({'a':1,'b':2}))
 def test_no_fixed_count(self): self.assertNotRegex(S[S.index('# ===== DEV-B46'):S.index('# ===== DEV-B43.2')],r'range\(1,\s*[789]')
 def test_no_not_published(self): self.assertNotIn('NOT_PUBLISHED',S[S.index('# ===== DEV-B46'):S.index('# ===== DEV-B43.2')])
 def test_flags(self):
  sec=S[S.index('def live_entry_snapshot'):S.index('# ===== DEV-B43.2')]; self.assertIn('"withdrawal_inference":False',sec); self.assertIn('"fabricated_data":False',sec)
 def test_immutable_policy(self): self.assertIn('IMMUTABLE_CONTENT_VERSION',S)
 def test_recovery(self): self.assertIn('ENTRY_SNAPSHOT_SOURCE_NOT_AVAILABLE',S)
if __name__=='__main__': unittest.main()
