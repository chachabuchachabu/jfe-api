# IC1.4 B48.2 — Timeout / Stage Diagnostics

- Version: 1.0.0-ic1.4-dev-b48.2
- Schema: JFE-LIVE-ODDS-DOM-PROBE/0.3
- Bounded stages: PRE_RACE_LOCK 12s, ENTRY_BINDING 10s, ODDS_FETCH 6s.
- Uses daemon worker threads so the HTTP request can return stage diagnostics after timeout.
- Limits live odds diagnostic fetch to one source-bound locked race globally.
- Adds stage_diagnostics, request_elapsed_ms, time_budget_seconds=30, always_respond_policy=true.
- No bet-type inference, fabricated odds, or diagnostic-to-production promotion.
