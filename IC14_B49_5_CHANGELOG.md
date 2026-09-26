# IC1.4 B49.5 — Trifecta BT5 Coordinate Binding

- Binds 3連単 from source `odds_table bt5` axis matrices.
- Coordinate contract: first-place = table axis; second-place = row car; third-place = remaining active-car column order.
- Completeness is calculated dynamically from active entries: nP3 = n*(n-1)*(n-2); no fixed rider count.
- Preserves source value `9999.9` unmodified.
- Any missing/ambiguous axis, row-count mismatch, or conflicting coordinate leaves trifecta PARTIAL.
- Canonical market snapshot schema bumped to 0.2. Market becomes AVAILABLE only when all five sections are AVAILABLE.
- Alias endpoint added: `/v1/trifecta-market-binding/YYYY-MM-DD` (canonical endpoint remains supported).

Local focused tests: 7-car 210/210 PASS; 9-car 504/504 PASS; 9999.9 preservation PASS; compile PASS.
LIVE status: NOT YET VERIFIED. Deploy and test against current KDreams source before promotion.
