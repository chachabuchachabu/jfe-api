# JFE IC1.4 B58.4

- Replaces B58.3 single-shot multi-day normalization with source-body validated candidate resolution.
- For a target race date, generates day-1/day-2/day-3 KDreams meeting identity candidates.
- Fetches candidates and accepts only the unique page whose HTML identity matches target date, venue and race number and exposes a valid scheduled start.
- Keeps fail-closed behavior when zero or multiple candidates match.
- Regression case: 2026-09-30 Sasebo 5R resolves to 85202609300100 / racedetail 8520260930010005.
