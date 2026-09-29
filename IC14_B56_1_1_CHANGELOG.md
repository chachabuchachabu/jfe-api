# IC1.4 B56.1.1 — Scheduled Start DOM Probe

- Adds `/v1/scheduled-start-dom-probe/YYYY-MM-DD`.
- Optional query: `venue`, `race`.
- Uses only a source-bound racedetail URL from Race Verification.
- Reports bounded plain-text contexts around HH:MM tokens and start/close labels.
- Reports bounded raw HTML fragments around HH:MM tokens to expose tag/class structure.
- Does not promote or infer a scheduled start time. Diagnostic only.
- Preserves source URL, transport, latency, byte length, and SHA-256 provenance.
