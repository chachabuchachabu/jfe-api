import unittest
import start
class B6(unittest.TestCase):
 def test_sale_only_is_excluded(self):
  c={"venue_code":"99","venue_name":"場外参照場","source":"A","evidence":{"sale_reference":True}}
  x=start.filter_active_meetings([c])
  self.assertEqual(len(x["active"]),0); self.assertEqual(x["excluded_sale_only"][0]["meeting_state"],start.SALE_ONLY)
 def test_schedule_is_active(self):
  c={"venue_code":"56","venue_name":"岸和田","source":"A","evidence":{"active_schedule":True}}
  x=start.filter_active_meetings([c])
  self.assertEqual(x["active"][0]["meeting_state"],start.MEETING_ACTIVE)
 def test_race_discovery_promotes_verified(self):
  c={"venue_code":"56","venue_name":"岸和田","evidence":{"active_schedule":True}}
  v=start.promote_race_discovery_evidence(c,{"state":"AVAILABLE","race_count":11})
  self.assertEqual(v["meeting_state"],start.MEETING_VERIFIED)
 def test_sale_and_active_is_not_discarded(self):
  a={"venue_code":"56","venue_name":"岸和田","source":"A","evidence":{"sale_reference":True}}
  b={"venue_code":"56","venue_name":"岸和田","source":"B","evidence":{"active_schedule":True}}
  x=start.filter_active_meetings([a,b])
  self.assertEqual(len(x["active"]),1)
  self.assertIn("SALE_AND_ACTIVE_EVIDENCE",x["active"][0]["conflicts"])
 def test_unknown_remains_unresolved(self):
  c={"venue_code":"56","venue_name":"岸和田","source":"A","evidence":{}}
  x=start.filter_active_meetings([c])
  self.assertEqual(x["unresolved"][0]["meeting_state"],start.MEETING_UNKNOWN)
if __name__=="__main__": unittest.main(verbosity=2)
