# JFE IC1.4 B58.4.7

- Adds fail-closed Target Resolver diagnostics for zero-candidate cases.
- Preserves race-verification state, raw/filtered identity row counts, meeting IDs, venue codes, bound dates, discovered race numbers, attempted racecard URLs, HTTP status/byte length, and discovery errors.
- Does not alter candidate selection, multiday normalization, official-result parsing, or B58.4.6 integrity behavior.
- Intended to diagnose the 2026-09-23 Komatsushima 6R `candidate_count=0` cross-venue test.
