import unittest
import start

def daily(): return '<div data-venue-code="56" data-venue-name="岸和田"></div>'
def program(n): return "".join(f'<a data-race-no="{i}">{i}R</a>' for i in range(1,n+1))
def entry_row(car,name,kana):
    return f'<tr><td>{car}</td><td title="{name}">{name}</td><td>{kana}</td></tr>'
def stats_row(car,name,score,style):
    return f'<tr><td>{car}</td><td>{name}</td><td>{score:.2f}</td><td>{style}</td><td>10.0%</td><td>20.0%</td><td>30.0%</td></tr>'

ENTRY='<table>'+entry_row(1,"山田太郎","ヤマダタロウ")+entry_row(2,"佐藤次郎","サトウジロウ")+entry_row(3,"鈴木三郎","スズキサブロウ")+'</table>'
STATS='<table>'+stats_row(1,"山田太郎",100,"逃")+stats_row(2,"佐藤次郎",99,"追")+stats_row(3,"鈴木三郎",98,"両")+'</table>'
ODDS="3連単 1-2-3 4.5 3連複 1-2-3 3.1"

class B7(unittest.TestCase):
 def adapters(self,n=2):
  return [start.SourceAdapter("A",fetch_daily=lambda d:daily(),fetch_program=lambda d,v:program(n),priority=1)]
 def acq(self):
  return {"entry":lambda d,v,r:ENTRY,"rider_stats":lambda d,v,r:STATS,"odds":lambda d,v,r:ODDS}

 def test_fixture_is_available_before_isolation_test(self):
  rp=start.run_race_pipeline("2026-09-16",{"venue_name":"岸和田"},{"race_no":2},self.acq())
  self.assertEqual(rp["blocks"]["entry"]["state"],"AVAILABLE")
  self.assertEqual(rp["blocks"]["rider_stats"]["state"],"AVAILABLE")
  self.assertEqual(rp["blocks"]["odds"]["state"],"AVAILABLE")
  self.assertEqual(rp["state"],"AVAILABLE")

 def test_target_date_to_all_races(self):
  x=start.run_daily_e2e("2026-09-16",self.adapters(2),self.acq())
  self.assertEqual(x["coverage"]["total_races"],2)
  self.assertEqual(x["coverage"]["available_races"],2)

 def test_verified_gate(self):
  x=start.run_daily_e2e("2026-09-16",self.adapters(1),self.acq())
  self.assertEqual(x["venues"][0]["meeting_state"],start.MEETING_VERIFIED)

 def test_one_race_failure_does_not_abort_day(self):
  acq=self.acq()
  def entry(d,v,r):
   if r["race_no"]==1: raise RuntimeError("boom")
   return ENTRY
  acq["entry"]=entry
  x=start.run_daily_e2e("2026-09-16",self.adapters(2),acq)
  self.assertEqual(x["coverage"]["total_races"],2)
  self.assertEqual(x["coverage"]["partial_races"],1)
  self.assertEqual(x["coverage"]["available_races"],1)
  self.assertEqual(x["venues"][0]["race_packets"][1]["state"],"AVAILABLE")

 def test_entry_failure_blocks_downstream(self):
  acq=self.acq(); acq["entry"]=lambda d,v,r:""
  rp=start.run_daily_e2e("2026-09-16",self.adapters(1),acq)["venues"][0]["race_packets"][0]
  self.assertEqual(rp["blocks"]["rider_stats"]["error"],"BLOCKED_BY_ENTRY")
  self.assertEqual(rp["blocks"]["odds"]["error"],"BLOCKED_BY_ENTRY")

 def test_odds_unpublished_is_preserved(self):
  acq=self.acq(); acq["odds"]=lambda d,v,r:"3連単 オッズ未発表"
  rp=start.run_daily_e2e("2026-09-16",self.adapters(1),acq)["venues"][0]["race_packets"][0]
  self.assertEqual(rp["blocks"]["odds"]["state"],"NOT_PUBLISHED")

if __name__=="__main__": unittest.main(verbosity=2)
