import unittest, start
class T(unittest.TestCase):
 def test_version(self): self.assertIn('dev-b48.3',start.VERSION)
 def test_route(self): self.assertIn('/v1/upstream-stage-probe/',open('start.py').read())
 def test_schema_source(self): self.assertIn('JFE-UPSTREAM-STAGE-PROBE/0.1',open('start.py').read())
 def test_bounded_discovery(self): self.assertIn('_bounded_stage("RACE_VERIFICATION",8',open('start.py').read())
 def test_bounded_single_fetch(self): self.assertIn('_bounded_stage("SINGLE_ENTRY_FETCH",6',open('start.py').read())
 def test_one_race_scope(self): self.assertIn('ONE_SOURCE_BOUND_RACE',open('start.py').read())
 def test_no_fixed_count(self): self.assertNotIn('range(1,8)',start.live_upstream_stage_probe.__doc__ or '')
 def test_always_respond(self): self.assertIn('always_respond_policy',open('start.py').read())
 def test_no_fabrication(self): self.assertIn('"fabricated_data":False',open('start.py').read())
if __name__=='__main__': unittest.main()
