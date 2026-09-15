# JFE v1.0 RC3 — Odds Integrity / Pre-Race Lock Foundation

RC3 fixes the RC2 ambiguity where different race requests appeared to yield identical odds snapshots.

Changes:
- Odds fetch bypasses JFE TTL cache and requests no-cache.
- Returned HTML must contain the requested race_id.
- Raw SHA-256 is registered to a race owner; reuse by another race raises JFE-05 SOURCE_CONFLICT.
- Snapshot key/evidence includes race_id, acquisition time, raw/content hashes, bytes, race-id occurrence count,
  odds-like value count and unique value count.
- Transport/content binding can become QUALIFIED_TRANSPORT, but Odds is NOT READY until the actual odds parser
  and pre-race freshness rules are qualified.
- Identity/Entry remain regression-protected.

Recommended live sequence after deploy:
1. 2026-09-15 大宮10R
2. 2026-09-16 岸和田9R
Compare raw_sha256, bytes, race_id_occurrences, odds_value_count and unique_odds_values.
