# IC1.4 B56.1
- Added source-bound scheduled-start acquisition from each KDreams racedetail URL.
- Added URL venue/date/race identity guard before accepting start time.
- NOW mode filters strictly on scheduled_start > requested_at_jst.
- Started races are excluded; unresolved start times remain explicit and cause PARTIAL.
- Added bounded parallel start-time acquisition.
- Propagates verified scheduled_start into targeted strict-contract quality evidence.
- No inferred/default start times.
