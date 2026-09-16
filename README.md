# JFE v1.0 Integrated Candidate IC1.3
Qualification candidate; not production ready.

Changes from IC1.2:
- Line Order readiness now requires Entry READY + explicit entry binding.
- Adds a qualification-only KDreams Secondary Odds Adapter for the externally verified 2026-09-16 Kishiwada meeting.
- Primary netkeirin generic odds pages trigger secondary probing.
- Secondary odds must bind date/venue/race/entrant identities and contain explicit combination+decimal-odds evidence.
- Secondary Odds remains QUALIFYING, not READY, until bet-type section mapping and freshness are validated across multiple races.
- Silent wrong data remains UNKNOWN until external ground-truth qualification.

Safety: fail closed; no fabricated data; no paid services required.
