# IC1.4 development branch — B1

- Preserves IC1.3.1 source flow and fail-closed behavior.
- Replaces rider-stats completeness logic with Entry-first expected-car binding.
- Adds explicit AVAILABLE/PARTIAL/ERROR state for rider stats.
- Adds targeted recovery history for only missing cars.
- Exposes expected/missing/unexpected car numbers in rider_stats block.
- Regression rule: a missing #5 is PARTIAL acquisition/parser failure, never NOT_PUBLISHED.

Local synthetic regression: 3/3 PASS. Network/live-site regression is not claimed by this package.

## IC1.4 DEV-B2 — Market/Odds Integrity
- Added explicit KDreams bet-type section binding for Wide / Quinella / Exacta / Trio / Trifecta.
- Odds values are never promoted without explicit bet-type heading evidence.
- Added active-entry combination guard and duplicate-selection rejection.
- Added per-bet-type states: AVAILABLE / NOT_PUBLISHED / ERROR / UNKNOWN.
- NOT_PUBLISHED requires explicit source evidence; empty/unparsed data remains UNKNOWN or ERROR.
- KDreams fallback may reach READY only after race identity + explicit bet-type binding + valid odds.
- Source timestamp is retained; missing timestamp is UNKNOWN, not silently treated as fresh.
- Preserved IC1.4-B regression suite.
- Tests: IC1.4-B 3/3 PASS; IC1.4-C 5/5 PASS.
