# IC1.4 B49.2 — Bounded Market Binding

- Version: 1.0.0-ic1.4-dev-b49.2
- Schema: JFE-LIVE-MARKET-BINDING/0.2
- Keeps B49.1 source-binding hotfix.
- Fixes B49 entry parser call to use the B44 dictionary contract.
- Wraps the complete Market DOM scan + odds parse + dedup/binding in a 5 second wall-clock guard.
- Removes the unbounded pre-binding odds probe from the B49 path, avoiding a second full odds parse.
- Adds market_binding_diagnostics with raw candidate counts and a diagnostic candidate ceiling of 2000.
- On timeout/error/limit breach, returns ERROR/PARTIAL JSON; it never promotes incomplete data to a complete market snapshot.
