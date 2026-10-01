# IC1.4 B58.4.3

- Bound official-result source probes independently from the general retrying fetcher.
- Probe `showResult` and `result` in parallel, one attempt each, 3 s per URL, 5 s overall deadline.
- Preserve deterministic `showResult` preference when both complete.
- Emit HTTP status, latency, timeout/error type, identity-binding state and parser-reached diagnostics.
- Fail closed with JSON diagnostics instead of allowing result-source latency to stall the endpoint.
