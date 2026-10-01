# IC1.4 B58.4.1

- Prevent blank/hanging official-result responses during multiday identity resolution.
- Added a dedicated single-attempt bounded identity probe (3.0 s per source request).
- Added a 5.0 s aggregate deadline for parallel candidate identity binding.
- Timed-out candidates now return `IDENTITY_PROBE_DEADLINE_EXCEEDED` diagnostics instead of blocking the HTTP response.
- Preserves fail-closed identity validation and does not weaken normal JFE source fetching policy.
