# IC1.4 B49 — Market/Odds Binding

- Version: 1.0.0-ic1.4-dev-b49
- Adds `/v1/market-binding/YYYY-MM-DD`.
- Single-acquisition path: Race Verification -> Entry -> Integrity -> Entry Lock material -> Odds fetch -> Market binding.
- Canonicalizes unordered bet types (wide, quinella, trio) while preserving order for exacta/trifecta.
- Deduplicates identical repeated quotes and fail-closes conflicting quotes as PARTIAL.
- Computes theoretical unique-combination counts dynamically from active rider count; no fixed 7/9 rider assumption.
- Preserves source URL, source timestamp, acquisition timestamp and actual odds HTML SHA-256 on each bound quote/snapshot.
- No bet-type inference; explicit source binding remains required.
