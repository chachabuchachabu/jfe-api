# JFE IC1.4 B48.1 — Source-Binding Recovery

- Fixes B48 LIVE zero-sample pre-fetch binding failure.
- Joins B47 LOCK races to B44 source-bound `race_url` through `live_entry_binding()` instead of performing a second B42 evidence reconstruction.
- Exact key: kaisai_date_id + venue_code + race_no; unique venue+race fallback is allowed only when unambiguous and is explicitly labelled.
- Adds binding diagnostics: locked candidates, source-bound candidates, identity matches, source URL matches, fetch attempts, fetch successes.
- Zero samples can no longer fail with an empty recovery queue.
- Venue sampling is consumed only after a source URL is successfully bound.
- No odds values are promoted in B48.1; parser remains diagnostic-only.
