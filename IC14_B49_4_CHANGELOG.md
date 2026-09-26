# IC1.4 B49.4 — Canonical Market Binding
- Version: 1.0.0-ic1.4-dev-b49.4
- New endpoint: `/v1/canonical-market-binding/YYYY-MM-DD`.
- Canonical table selection is structural: explicit selection syntax + dynamic expected combination count; no fixed table index.
- Wide is represented as `odds_min` / `odds_max`; `9999.9` and `9999.9～9999.9` are preserved unmodified as source values.
- Quinella, exacta and trio bind only when a complete canonical table is found.
- Equivalent ascending/descending tables must agree exactly or the section fails closed.
- Trifecta remains PARTIAL until the `odds_table bt5` cell coordinates are source-bound; no fabricated 210-quote promotion.
