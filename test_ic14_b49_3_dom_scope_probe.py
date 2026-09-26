import unittest
import start

class B493(unittest.TestCase):
 def test_version(self): self.assertEqual(start.VERSION,'1.0.0-ic1.4-dev-b49.3')
 def test_preserve_9999(self):
  raw='<h2>ワイド</h2><table class="odds current"><tr><td>1-2 9999.9</td></tr></table>'
  c=start._b493_table_candidates(raw,[1,2,3])
  self.assertEqual(len(c),1); self.assertTrue(c[0]['contains_9999_9'])
 def test_table_metadata(self):
  raw='<h2>ワイド</h2><table id="x" class="odds current"><tr><td>1-2 12.3</td></tr></table>'
  c=start._b493_table_candidates(raw,[1,2,3])[0]
  self.assertEqual(c['id'],'x'); self.assertEqual(c['class'],'odds current')
 def test_nonmarket_ignored(self): self.assertEqual(start._b493_table_candidates('<table><tr><td>hello</td></tr></table>',[1,2]),[])
 def test_no_promotion_flag(self):
  d=start._b493_response('2026-09-27',0,{}, {}, [], 'AVAILABLE')
  self.assertEqual(d['parser_promotion'],'NONE_DIAGNOSTIC_ONLY')
 def test_route_present(self):
  import inspect
  self.assertIn('/v1/market-dom-scope-probe/',inspect.getsource(start.S.do_GET))

if __name__=='__main__': unittest.main()
