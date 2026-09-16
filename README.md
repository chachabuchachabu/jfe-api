# JFE v1.0 Integrated Candidate IC1.3.1

Qualification diagnostic hotfix.

- Adds `/v1/trace/{date}/{venue}/{race}` for Odds routing and missing RiderStats raw-row evidence.
- Fixes KDreams probe regex escaping and flexible Japanese date binding.
- Secondary Odds remains QUALIFYING, never READY, until bet-type mapping/freshness qualification.
- Fail-closed and silent-wrong-data UNKNOWN semantics preserved.
- Free-tier deployment only; no paid dependencies.
