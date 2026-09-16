import unittest
import start
class B10(unittest.TestCase):
 def test_new_venue_from_link_without_legacy_map(self):
  h='<a href="/venue/99/schedule">新規場</a>'
  x=start.discover_venues_from_links(h,"2026-09-16","https://example.jp")
  self.assertEqual(x["venues"][0]["venue_code"],"99")
  self.assertEqual(x["venues"][0]["venue_name"],"新規場")
 def test_race_links_deduped_and_ids_preserved(self):
  h='<a href="/race/RACEABC/race-1">1R</a><a href="/race/RACEABC/race-1">1R</a><a href="/race/RACEDEF/race-2">2R</a>'
  x=start.discover_races_from_links(h,"2026-09-16",{"venue_code":"56"},"https://x.jp")
  self.assertEqual(x["race_count"],2)
  self.assertEqual([r["race_no"] for r in x["races"]],[1,2])
 def test_explicit_date_mismatch_blocked(self):
  h='<a href="/20260915/race-1">1R</a>'
  x=start.discover_races_from_links(h,"2026-09-16",{"venue_code":"56"},"https://x.jp")
  self.assertEqual(x["state"],"ERROR")
  self.assertEqual(x["conflicts"][0]["error"],"DATE_MISMATCH")
 def test_generic_page_unknown_not_unpublished(self):
  x=start.discover_races_from_links("<html>top page</html>","2026-09-16",{"venue_code":"56"})
  self.assertEqual(x["state"],"UNKNOWN"); self.assertNotEqual(x["state"],"NOT_PUBLISHED")
 def test_kdreams_event_dynamic_resolution(self):
  h='<a href="/kishiwada/racecard/56202609140300/">racecard</a>'
  x=start.resolve_kdreams_event_from_links(h,"2026-09-16","56")
  # meeting token may encode meeting start date, not target day; resolver must not invent a match.
  self.assertEqual(x["state"],"UNKNOWN")
 def test_kdreams_matching_event(self):
  h='<a href="/x/racecard/56202609160300/">racecard</a>'
  x=start.resolve_kdreams_event_from_links(h,"2026-09-16","56")
  self.assertEqual(x["state"],"AVAILABLE"); self.assertEqual(x["event_base"],"56202609160300")
if __name__=="__main__": unittest.main(verbosity=2)
