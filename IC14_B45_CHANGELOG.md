# IC1.4 DEV-B45 — Entry Integrity Gate

- Added `/v1/entry-integrity/YYYY-MM-DD`.
- Separates successful entry acquisition/binding from integrity acceptance.
- Validates car-number uniqueness, rider-name uniqueness, field types, grade format, race score presence, and source/retrieved/bound car-set consistency.
- Does not assume seven riders or contiguous car numbers.
- Does not infer withdrawals from absence; withdrawal state remains UNKNOWN without explicit source evidence.
- Integrity failures are isolated per race and added to Recovery Queue.
- B44.1 entry binding remains unchanged except version promotion.
