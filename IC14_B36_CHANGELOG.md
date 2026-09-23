# IC1.4 DEV-B36
- Fixes production integration bug: server start previously occurred before appended B4+ modules.
- Runtime version now reports `1.0.0-ic1.4-dev-b36`.
- Adds public `/v1/acquisition/test` endpoint to the actual Render HTTP handler.
- Endpoint performs a fresh server-side fetch and returns provenance: HTTP status, content type, byte length, SHA-256, acquired_at, elapsed time.
- Fetch failures are ERROR, never NOT_PUBLISHED.
