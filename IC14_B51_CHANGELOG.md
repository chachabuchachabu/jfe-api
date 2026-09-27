# IC1.4 B51 Johnny Engine Strict Integration Gate

- Adds `/v1/johnny-engine/integration/YYYY-MM-DD`.
- Consumes the B50 machine-readable RaceInput; no raw HTML is passed to JE.
- Treats an all-L-class field as Girls Keirin and line formation as `NOT_APPLICABLE`, never inferred.
- Standard/male races still require verified line data.
- Cross-source match and outlier safety remain strict blockers until evidence-backed.
- Does not call the legacy neutral-default JE adapter; blocked data never executes JE.
- Preserves provenance, market snapshot and explicit blocker list.
