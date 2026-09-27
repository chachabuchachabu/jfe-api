# IC1.4 B49.5.2 — Trifecta BT5 Coordinate Binding

Promotes the B49.5.1 live-proven BT5 coordinate structure into canonical market binding.

Binding contract:
- BT5 table heading `th.nX` = first place.
- Data-row heading `th.nY` = second place.
- Column heading `th.nZ` = third place.
- Intersecting non-empty `td` = trifecta odds.
- Diagonal second==third cells must be `empty` and are never emitted.
- Car axes are bound from explicit `nN` CSS classes, not positional inference.
- Expected count is dynamic `n*(n-1)*(n-2)`; no fixed seven-car assumption.
- Source value `9999.9` is preserved unmodified.
- Any axis/cell anomaly, conflict, missing quote, or unexpected empty keeps trifecta PARTIAL.

Canonical market schema bumped to `JFE-LIVE-CANONICAL-MARKET-BINDING/0.3`.
Version: `1.0.0-ic1.4-dev-b49.5.2`.
