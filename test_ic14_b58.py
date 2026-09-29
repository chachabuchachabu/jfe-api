import unittest
import start

class TestB58(unittest.TestCase):
    def test_eligible_pre_race(self):
        x={'target_resolution':{'requested_at_jst':'2026-09-30T05:30:00+09:00','target_date':'2026-09-30','selected_target':{'scheduled_start':{'value':'2026-09-30T10:00:00+09:00'}}},
           'strict_contract':{'state':'READY_FOR_MODEL_VALIDATION','race_id':{'kaisai_date_id':'85202609300100','venue_code':'85','race_no':5},'race_type':'STANDARD_KEIRIN','riders':[],'line_model':{},'market':{'exacta':{'quotes':[{'odds':2.3},{'odds':9999.9}]}},'quality_evidence':{}}}
        y=start._b58_calibration_specimen(x)
        self.assertEqual(y['state'],'ELIGIBLE_PRE_RACE_SPECIMEN'); self.assertTrue(y['chronology']['strictly_before_start'])
        self.assertEqual(y['market_formation']['exacta']['formed_quote_count'],1)
    def test_blocks_post_start(self):
        x={'target_resolution':{'requested_at_jst':'2026-09-30T10:01:00+09:00','target_date':'2026-09-30','selected_target':{'scheduled_start':{'value':'2026-09-30T10:00:00+09:00'}}},'strict_contract':{'state':'READY_FOR_MODEL_VALIDATION','race_id':{}}}
        y=start._b58_calibration_specimen(x); self.assertEqual(y['state'],'BLOCKED'); self.assertIn('NOT_PRE_RACE_ACQUISITION',y['blockers'])
if __name__=='__main__': unittest.main()
