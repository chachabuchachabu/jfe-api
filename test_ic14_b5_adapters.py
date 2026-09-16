import unittest
import start
def daily(*venues):
    return "".join(f'<div data-venue-code="{code}" data-venue-name="{name}"></div>' for code,name in venues)
def program(n):
    return "".join(f'<a data-race-no="{i}">{i}R</a>' for i in range(1,n+1))
class B5(unittest.TestCase):
 def test_primary_fail_secondary_daily_recovers(self):
  a=start.SourceAdapter("P",fetch_daily=lambda d: (_ for _ in ()).throw(TimeoutError()),priority=1)
  b=start.SourceAdapter("S",fetch_daily=lambda d: daily(("56","岸和田")),priority=2)
  x=start.discover_daily_with_failover("2026-09-16",[a,b])
  self.assertEqual(x["state"],"AVAILABLE"); self.assertEqual(x["venues"][0]["venue_name"],"岸和田")
  self.assertEqual(x["engine_trace"][0]["state"],"ERROR")
 def test_sources_are_reconciled(self):
  a=start.SourceAdapter("A",fetch_daily=lambda d: daily(("56","岸和田")),priority=1)
  b=start.SourceAdapter("B",fetch_daily=lambda d: daily(("63","防府")),priority=2)
  x=start.discover_daily_with_failover("2026-09-16",[a,b])
  self.assertEqual({v["venue_name"] for v in x["venues"]},{"岸和田","防府"})
 def test_program_failover(self):
  a=start.SourceAdapter("A",fetch_program=lambda d,v:"",priority=1)
  b=start.SourceAdapter("B",fetch_program=lambda d,v:program(11),priority=2)
  x=start.discover_program_with_failover("2026-09-16",{"venue_name":"岸和田"},[a,b])
  self.assertEqual(x["race_count"],11); self.assertEqual(x["source"],"B")
 def test_all_program_sources_fail_is_error_not_unpublished(self):
  a=start.SourceAdapter("A",fetch_program=lambda d,v:"",priority=1)
  x=start.discover_program_with_failover("2026-09-16",{"venue_name":"X"},[a])
  self.assertEqual(x["state"],"ERROR")
  self.assertNotEqual(x["state"],"NOT_PUBLISHED")
 def test_full_manifest_mixed_counts(self):
  venues=daily(("56","岸和田"),("63","防府"),("84","武雄"))
  counts={"岸和田":11,"防府":12,"武雄":7}
  a=start.SourceAdapter("A",fetch_daily=lambda d:venues,
    fetch_program=lambda d,v:program(counts[v["venue_name"]]),priority=1)
  x=start.build_daily_manifest_from_adapters("2026-09-16",[a])
  self.assertEqual(x["state"],"AVAILABLE")
  self.assertEqual([v["race_count"] for v in x["venues"]],[11,12,7])
if __name__=="__main__": unittest.main(verbosity=2)
