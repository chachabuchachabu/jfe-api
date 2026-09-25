import unittest
from unittest.mock import patch
import start

class B47(unittest.TestCase):
 def setUp(self): start.PRE_RACE_LOCKS.clear()
 def race(self,sid='s1',h='h1'):
  return {'kaisai_date_id':'X','venue_code':'V','race_no':3,'state':'AVAILABLE','snapshot_id':sid,'source_hash':h,'active_car_numbers':[1,3,7],'withdrawal_state':'UNKNOWN'}
 def payload(self,r): return {'state':'AVAILABLE','races':[r]}
 def test_baseline_lock(self):
  with patch.object(start,'live_entry_snapshot',return_value=self.payload(self.race())):
   x=start.live_pre_race_lock('2026-09-23'); self.assertEqual(x['races'][0]['lock_state'],'LOCKED'); self.assertFalse(x['odds_locked'])
 def test_unchanged_reuses_lock(self):
  with patch.object(start,'live_entry_snapshot',return_value=self.payload(self.race())):
   a=start.live_pre_race_lock('2026-09-23'); b=start.live_pre_race_lock('2026-09-23')
  self.assertEqual(a['races'][0]['lock_id'],b['races'][0]['lock_id'])
 def test_change_requires_relock(self):
  with patch.object(start,'live_entry_snapshot',side_effect=[self.payload(self.race()),self.payload(self.race('s2','h2'))]):
   a=start.live_pre_race_lock('2026-09-23'); b=start.live_pre_race_lock('2026-09-23')
  self.assertEqual(b['races'][0]['lock_state'],'RELOCK_REQUIRED'); self.assertEqual(b['races'][0]['entry_snapshot_id'],'s1')
 def test_explicit_relock(self):
  with patch.object(start,'live_entry_snapshot',side_effect=[self.payload(self.race()),self.payload(self.race('s2','h2')),self.payload(self.race('s2','h2'))]):
   a=start.live_pre_race_lock('2026-09-23'); start.live_pre_race_lock('2026-09-23'); c=start.live_pre_race_lock('2026-09-23',True)
  self.assertEqual(c['races'][0]['lock_state'],'LOCKED'); self.assertEqual(c['races'][0]['entry_snapshot_id'],'s2'); self.assertEqual(c['races'][0]['relock_of'],a['races'][0]['lock_id'])
 def test_noncontiguous(self):
  with patch.object(start,'live_entry_snapshot',return_value=self.payload(self.race())):
   x=start.live_pre_race_lock('2026-09-23')
  self.assertEqual(x['races'][0]['active_car_numbers'],[1,3,7])
 def test_error_isolated(self):
  bad=self.race(); bad['state']='ERROR'; good=self.race(); good['race_no']=4
  with patch.object(start,'live_entry_snapshot',return_value={'state':'PARTIAL','races':[bad,good]}): x=start.live_pre_race_lock('2026-09-23')
  self.assertEqual(x['error_race_count'],1); self.assertEqual(x['locked_race_count'],1)
 def test_storage_disclosure(self):
  with patch.object(start,'live_entry_snapshot',return_value=self.payload(self.race())): x=start.live_pre_race_lock('2026-09-23')
  self.assertEqual(x['storage_mode'],'PROCESS_MEMORY_VOLATILE'); self.assertFalse(x['durable_across_restart'])
 def test_no_fixed_count(self):
  with patch.object(start,'live_entry_snapshot',return_value=self.payload(self.race())): x=start.live_pre_race_lock('2026-09-23')
  self.assertFalse(x['fixed_rider_count_assumption']); self.assertFalse(x['fabricated_data'])
if __name__=='__main__': unittest.main()
