# IC1.4 DEV-B58 — Chronological Calibration Specimen Gate

- Adds `/v1/calibration-specimen/race/{venue}/{race_no}[/{YYYY-MM-DD}]`.
- Reuses the B57.1 targeted strict contract and preserves exact target identity.
- Emits an eligible pre-race calibration specimen only when `acquired_at_jst < scheduled_start_jst` and the strict contract is `READY_FOR_MODEL_VALIDATION`.
- Creates a canonical evidence SHA-256 for later result binding/audit.
- Reports formed-vs-9999.9 market counts without reinterpreting 9999.9.
- Does not attach results, train a model, rank riders, or execute a bet model.
- Explicitly marks storage as volatile until durable snapshot persistence is implemented.
