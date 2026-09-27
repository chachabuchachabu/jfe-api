# IC1.4 B52.1 — Multi-Source Adapter / Failover

- Version: `1.0.0-ic1.4-dev-b52.1`
- Schema: `JFE-CROSS-SOURCE-VALIDATION/0.2`
- Adds provider-specific adapters rather than assuming identical page structure.
- Primary: OddsPark adapter, bounded to 3s.
- Failover: netkeirin entry adapter, bounded to 5s.
- Each adapter must prove source-bound race identity and full car-number ↔ rider-name row binding.
- Failed/partial attempts are retained in `cross_source_evidence.attempts[]`.
- `cross_source_match=AVAILABLE` only when one independent adapter fully verifies the race.
- No HTTP-success-only promotion, no fuzzy rider identity, no neutral defaults, no fabrication.
- Local focused tests and Python compile: PASS.
- Live/production status: UNVERIFIED until Render endpoint is exercised.
