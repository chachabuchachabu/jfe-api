import unittest, start

class B48(unittest.TestCase):
 def test_version(self): self.assertEqual(start.VERSION,'1.0.0-ic1.4-dev-b48')
 def test_odds_url_source_bound(self):
  self.assertEqual(start._odds_url_from_racedetail('https://keirin.kdreams.jp/x/racedetail/1234567890123456/'),'https://keirin.kdreams.jp/x/racedetail/1234567890123456/?pageType=odds')
  self.assertIsNone(start._odds_url_from_racedetail('https://example.com/foo'))
 def test_explicit_labels_only(self):
  raw='<html><body>ワイド 1-2 2.5 ２車複 1-3 4.2</body></html>'
  d=start.odds_dom_probe(raw,[1,2,3])
  self.assertTrue(any(x['bet_type']=='wide' for x in d['explicit_bet_type_labels']))
  self.assertTrue(any(x['bet_type']=='quinella' for x in d['explicit_bet_type_labels']))
 def test_invalid_active_car_rejected(self):
  raw='<html><body>ワイド 1-7 2.5</body></html>'
  d=start.odds_dom_probe(raw,[1,2,3,4,5,6])
  self.assertEqual(d['bet_type_summary']['wide']['verified_odds_count'],0)
  self.assertGreaterEqual(d['bet_type_summary']['wide']['rejected_count'],1)
 def test_no_label_no_promotion(self):
  d=start.odds_dom_probe('<html>1-2 2.5</html>',[1,2])
  self.assertEqual(d['verified_odds_count'],0)
  self.assertFalse(any(x['bet_type_bound'] for x in d['bet_type_summary'].values()))
 def test_unpublished_not_failure(self):
  d=start.odds_dom_probe('<html>３連複 オッズ未発表</html>',[1,2,3])
  self.assertEqual(d['bet_type_summary']['trio']['state'],'NOT_PUBLISHED')
 def test_flags_in_source(self):
  src=open('start.py',encoding='utf-8').read()
  self.assertIn('"bet_type_inference":False',src)
  self.assertIn('"invalid_combination_guard":True',src)
  self.assertIn('"parser_promotion":"NONE_DIAGNOSTIC_ONLY"',src)
 def test_endpoint(self):
  src=open('start.py',encoding='utf-8').read(); self.assertIn('/v1/odds-dom-probe/',src)

if __name__=='__main__': unittest.main()
