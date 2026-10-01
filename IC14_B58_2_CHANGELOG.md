# IC1.4 B58.2 — Official Result Route Correction

- Corrects the primary KDreams result view from `?pageType=result` to `?pageType=showResult`.
- Retains `?pageType=result` as a fail-closed diagnostic fallback.
- Records per-route `source_attempts` for provenance and diagnosis.
- Accepts a result only after exact date/venue/race identity and explicit `着順 / 車番 / 選手名` table binding.
- Preserves `UNKNOWN` when neither route yields a bound result table; does not fabricate publication state.
