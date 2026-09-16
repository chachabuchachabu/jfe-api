import unittest
from start import parse_kd_odds_sections

class OddsTests(unittest.TestCase):
 def test_bet_type_binding_and_values(self):
  raw='<h2>ワイド</h2>1-2 2.4 1-3 3.1 <h2>３連複</h2>1-2-3 4.5 <h2>３連単</h2>3-1-2 8.7'
  x=parse_kd_odds_sections(raw,[1,2,3,4,5,6])
  self.assertEqual(x['wide']['state'],'AVAILABLE');self.assertEqual(len(x['wide']['data']),2)
  self.assertEqual(x['trio']['data'][0]['odds'],4.5);self.assertEqual(x['trifecta']['data'][0]['selection'],[3,1,2])
 def test_no_heading_never_infers_bet_type(self):
  x=parse_kd_odds_sections('3-5-2 4.5 5-3-2 5.7',[1,2,3,4,5,6])
  self.assertTrue(all(v['state']=='UNKNOWN' for v in x.values()))
  self.assertTrue(all(not v['bet_type_bound'] for v in x.values()))
 def test_invalid_car_is_rejected(self):
  x=parse_kd_odds_sections('<h2>３連単</h2>3-7-2 4.5',[1,2,3,4,5,6])
  self.assertEqual(x['trifecta']['state'],'ERROR');self.assertEqual(x['trifecta']['rejected'][0]['reason'],'INVALID_COMBINATION')
 def test_explicit_unpublished_only(self):
  x=parse_kd_odds_sections('<h2>３連複</h2>オッズ未発表',[1,2,3,4,5,6])
  self.assertEqual(x['trio']['state'],'NOT_PUBLISHED')
  self.assertEqual(x['wide']['state'],'UNKNOWN')
 def test_partial_bet_states_can_coexist(self):
  x=parse_kd_odds_sections('<h2>ワイド</h2>1-2 2.2 <h2>３連複</h2>発売前 <h2>３連単</h2>1-8-2 9.9',[1,2,3,4,5,6])
  self.assertEqual(x['wide']['state'],'AVAILABLE')
  self.assertEqual(x['trio']['state'],'NOT_PUBLISHED')
  self.assertEqual(x['trifecta']['state'],'ERROR')
if __name__=='__main__':unittest.main(verbosity=2)
