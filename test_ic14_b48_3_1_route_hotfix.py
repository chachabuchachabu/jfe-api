import unittest
from unittest.mock import patch
import start

class Dummy(start.S):
    def __init__(self): pass
    def j(self,c,o,head=False):
        self.sent=(c,o,head); return self.sent

class T(unittest.TestCase):
    def test_upstream_route_has_real_json_sender(self):
        h=Dummy(); h.path='/v1/upstream-stage-probe/2026-09-26'
        payload={'state':'AVAILABLE','marker':'ok'}
        with patch.object(start,'live_upstream_stage_probe',return_value=payload):
            out=h.do_GET()
        self.assertEqual(out[0],200); self.assertEqual(out[1],payload)
    def test_error_maps_503(self):
        h=Dummy(); h.path='/v1/upstream-stage-probe/2026-09-26'
        with patch.object(start,'live_upstream_stage_probe',return_value={'state':'ERROR'}):
            out=h.do_GET()
        self.assertEqual(out[0],503)
    def test_no_send_json_reference_in_handler(self):
        import inspect
        self.assertNotIn('self.send_json',inspect.getsource(start.S.do_GET))

if __name__=='__main__': unittest.main()
