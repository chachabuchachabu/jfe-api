# JFE IC1.4 B58.3

## Fix
- Correct KDreams multi-day `kaisai_date_id` semantics.
- Positions 2:10 are treated as the meeting start date, not necessarily the race date.
- Positions 10:12 are used as the meeting-day sequence (`01`, `02`, `03`, ...).
- Before scheduled-start binding, derive `meeting_start = target_race_date - (meeting_day_no - 1)` and normalize the meeting ID + racedetail URL.
- Keep fail-closed body identity verification: repaired URLs are accepted only when HTML title date, venue, and race number match the requested target.

## Regression target
- 2026-09-30 Sasebo 5R: erroneous `85202609300200` normalizes to `85202609290200` before LIVE body binding.
