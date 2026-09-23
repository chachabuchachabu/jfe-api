# IC1.4 DEV-B41

Adds `/v1/race-verification/YYYY-MM-DD`.

The verifier:
- discovers source-published racecard URLs for target-date meeting IDs;
- fetches each candidate independently;
- enumerates race numbers from page evidence without assuming 12 races;
- promotes a candidate to `VERIFIED_VENUE` only after HTTP 200 plus race evidence;
- sends incomplete candidates to recovery, never `NOT_PUBLISHED`;
- preserves per-page SHA-256 provenance.
