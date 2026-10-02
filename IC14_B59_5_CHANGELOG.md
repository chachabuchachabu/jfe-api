# JFE IC1.4 B59.5 Changelog

## Scope
Historical meeting identity fallback expansion only. B59.4.3 Race Package, five-bet market parsing, trifecta semantic gate, and Wide 1.0 lower-bound handling are unchanged.

## Changes
- Version: `1.0.0-ic1.4-dev-b59.5`.
- Expanded KDreams meeting-day candidates from day 1–3 to day 1–6.
- Candidate ID remains `venue + meeting_start_date + day_no + tail`.
- Every candidate remains untrusted until the fetched source body verifies target date, venue, race number, and source-published start time.
- Unique-match requirement remains fail-closed; zero or multiple source-verified candidates are not promoted.
- Existing bounded parallel probe policy remains: 3.0 s per URL, 5.0 s aggregate identity deadline.

## Regression intent
- Existing day-1/day-2/day-3 historical races must resolve identically to B59.4.3.
- Day-4/day-5/day-6 races can now be resolved when KDreams source-body identity uniquely verifies them.
- No change to market odds parsing or official-result parsing.
