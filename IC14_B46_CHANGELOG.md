# IC1.4 B46 — Entry Snapshot / Change Detection

- Added `/v1/entry-snapshot/YYYY-MM-DD`.
- Added deterministic content hashes and immutable content-version snapshot IDs.
- Added BASELINE / UNCHANGED / CHANGED comparison states.
- Added ADDED / REMOVED / RIDER_CHANGED / FIELD_CHANGED events.
- REMOVED never implies withdrawal. Withdrawal changes require explicit upstream source evidence.
- Preserved per-race failure isolation and Recovery Queue.
- No fixed rider count or contiguous car-number assumption.
