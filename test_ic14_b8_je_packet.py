import unittest
import start
def daily(): return '<div data-venue-code="56" data-venue-name="岸和田"></div>'
def program(n): return "".join(f'<a data-race-no="{i}">{i}R</a>' for i in range(1,n+1))
def er(c,n,k): return f'<tr><td>{c}</td><td title="{n}">{n}</td><td>{k}</td></tr>'
def sr(c,n,sc): return f'<tr><td>{c}</td><td>{n}</td><td>{sc:.2f}</td><td>追</td><td>10.0%</td><td>20.0%</td><td>30.0%</td></tr>'
ENTRY='<table>'+er(1,"山田太郎","ヤマダタロウ")+er(2,"佐藤次郎","サトウジロウ")+er(3,"鈴木三郎","スズキサブロウ")+'</table>'
STATS='<table>'+sr(1,"山田太郎",100)+sr(2,"佐藤次郎",99)+sr(3,"鈴木三郎",98)+'</table>'
ODDS="3連単 1-2-3 4.5 3連複 1-2-3 3.1"
def adapters(n=1): return [start.SourceAdapter("A",fetch_daily=lambda d:daily(),fetch_program=lambda d,v:program(n),priority=1)]
def acq(): return {"entry":lambda d,v,r:ENTRY,"rider_stats":lambda d,v,r:STATS,"odds":lambda d,v,r:ODDS}
class B8(unittest.TestCase):
 def test_complete_race_is_ready_for_je(self):
  d=start.run_daily_e2e("2026-09-16",adapters(),acq())
  x=start.attach_je_packets(d)
  jp=x["venues"][0]["race_packets"][0]["je_packet"]
  self.assertTrue(jp["ready_for_je"]); self.assertEqual(jp["block_reasons"],[])
 def test_missing_rider_blocks_je(self):
  a=acq(); a["rider_stats"]=lambda d,v,r:'<table>'+sr(1,"山田太郎",100)+sr(2,"佐藤次郎",99)+'</table>'
  d=start.run_daily_e2e("2026-09-16",adapters(),a)
  jp=start.attach_je_packets(d)["venues"][0]["race_packets"][0]["je_packet"]
  self.assertFalse(jp["ready_for_je"]); self.assertIn("JFE-B03_RIDER_COMPLETENESS",jp["block_reasons"])
 def test_unpublished_odds_blocks_je(self):
  a=acq(); a["odds"]=lambda d,v,r:"3連単 オッズ未発表"
  d=start.run_daily_e2e("2026-09-16",adapters(),a)
  jp=start.attach_je_packets(d)["venues"][0]["race_packets"][0]["je_packet"]
  self.assertFalse(jp["ready_for_je"]); self.assertIn("JFE-B04_MARKET",jp["block_reasons"])
 def test_packet_schema_and_integrity(self):
  d=start.run_daily_e2e("2026-09-16",adapters(),acq())
  jp=start.attach_je_packets(d)["venues"][0]["race_packets"][0]["je_packet"]
  self.assertEqual(jp["schema"],"JFE-JE-PACKET/0.2")
  self.assertEqual(jp["integrity"]["active_car_numbers"],[1,2,3])
  self.assertEqual(jp["integrity"]["missing_car_nos"],[])
 def test_daily_je_coverage_isolated(self):
  a=acq()
  def entry(d,v,r):
   if r["race_no"]==1: return ""
   return ENTRY
  a["entry"]=entry
  d=start.run_daily_e2e("2026-09-16",adapters(2),a)
  x=start.attach_je_packets(d)
  self.assertEqual(x["je_coverage"]["total"],2)
  self.assertEqual(x["je_coverage"]["ready"],1)
  self.assertEqual(x["je_coverage"]["blocked"],1)
if __name__=="__main__": unittest.main(verbosity=2)
