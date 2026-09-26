# IC1.4 B49.3 — Market DOM Scope Isolation Probe

- Version: 1.0.0-ic1.4-dev-b49.3
- Adds `/v1/market-dom-scope-probe/YYYY-MM-DD`.
- Diagnostic-only: does not promote a canonical market table yet.
- Enumerates bounded market-looking HTML tables with class/id, nearby explicit bet-type labels, per-table parse counts, decimal count, and bounded text sample.
- Preserves source value `9999.9` unchanged; it is not classified as a parser error.
- Reuses B49.2 bounded acquisition path and source-bound race selection.
- Goal: identify the exact current-odds DOM scope before changing the production market parser.
