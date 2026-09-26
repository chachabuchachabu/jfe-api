# IC1.4 B48.3 — Upstream Stage Decomposition

- Version: 1.0.0-ic1.4-dev-b48.3
- Adds `/v1/upstream-stage-probe/YYYY-MM-DD`.
- Bounded stages: Race Verification (8s), one source-bound Entry Fetch (6s), Entry Parse, Integrity, Snapshot Material, Lock Material.
- Diagnostic scope is one source-bound race only; no production odds promotion.
- Always-respond behavior retained; no fixed rider-count assumption and no fabricated data.
