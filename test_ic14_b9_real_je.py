import unittest
import start
from johnny_engine_v1_0_proto import RaceInput
def jp():
 return {"ready_for_je":True,"target_date":"2026-09-16","venue":{"venue_name":"岸和田"},"race":{"race_no":1},
 "riders":[{"car_no":1,"score":100.0},{"car_no":2,"score":90.0},{"car_no":3,"score":80.0}],
 "market":[{"bet_type":"trifecta","selection":"1-2-3","odds":20.0},{"bet_type":"trio","selection":"1-2-3","odds":8.0}],
 "integrity":{"missing_car_nos":[]},"block_reasons":[]}
class B9(unittest.TestCase):
 def test_real_raceinput_constructed(self):
  r=start.je_packet_to_race_input(jp(),lines=[[1,2],[3]])
  self.assertIsInstance(r,RaceInput); self.assertEqual(r.race_id,"2026-09-16|岸和田|1R")
 def test_market_mapping(self):
  r=start.je_packet_to_race_input(jp(),lines=[[1,2],[3]])
  self.assertEqual({q.bet_type for q in r.market},{"trifecta","trio"})
 def test_real_engine_executes(self):
  x=start.run_johnny_from_jfe_packet(jp(),lines=[[1,2],[3]])
  self.assertEqual(x["state"],"JE_EXECUTED")
  self.assertIn(x["result"]["status_code"],{"JE-100","JE-110","JE-120","JE-130","JE-200"})
 def test_jfe_block_prevents_engine(self):
  x=jp(); x["ready_for_je"]=False; x["block_reasons"]=["JFE-B04_MARKET"]
  y=start.run_johnny_from_jfe_packet(x)
  self.assertEqual(y["state"],"BLOCKED_BY_JFE"); self.assertEqual(y["status_code"],"JFE-BLOCK")
 def test_stale_market_reaches_je_gate(self):
  x=start.run_johnny_from_jfe_packet(jp(),lines=[[1,2],[3]],market_age_minutes=30)
  self.assertEqual(x["state"],"JE_EXECUTED")
  self.assertIn("D02 STALE_ODDS",x["result"]["warnings"])
if __name__=="__main__":unittest.main(verbosity=2)
