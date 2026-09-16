import unittest
import start
DAILY = """<div data-venue-code="56" data-venue-name="岸和田"></div><div data-venue-code="63" data-venue-name="防府"></div><div data-venue-code="84" data-venue-name="武雄"></div>"""
def program(n): return "\\n".join(f'<a href="/race/{i}" data-race-no="{i}">{i}R</a>' for i in range(1,n+1))
class T(unittest.TestCase):
 def test_venues(self):
  x=start.discover_venues_from_html(DAILY,"2026-09-16"); self.assertEqual([v["venue_name"] for v in x["venues"]],["岸和田","防府","武雄"])
 def test_counts(self):
  for n in (7,9,11,12): self.assertEqual(start.discover_races_from_html(program(n),"X")["race_count"],n)
 def test_unknown(self): self.assertEqual(start.discover_venues_from_html("","2026-09-16")["state"],"UNKNOWN")
 def test_no_fixed_venue(self): self.assertEqual(start.discover_venues_from_html('<div data-venue-code="99" data-venue-name="新規場"></div>',"2026-09-16")["venues"][0]["venue_name"],"新規場")
 def test_partial(self):
  x=start.build_daily_manifest("2026-09-16",DAILY,{"岸和田":program(11),"防府":program(12),"武雄":""}); self.assertEqual(x["state"],"PARTIAL"); self.assertEqual(x["recovery_queue"][0]["venue"],"武雄")
 def test_available(self):
  x=start.build_daily_manifest("2026-09-16",DAILY,{"岸和田":program(11),"防府":program(12),"武雄":program(7)}); self.assertEqual(x["state"],"AVAILABLE"); self.assertEqual([v["race_count"] for v in x["venues"]],[11,12,7])
if __name__=="__main__": unittest.main(verbosity=2)
