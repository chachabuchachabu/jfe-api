# IC1.4 B56.3 — Explicit Target Path Routes

- Version: `1.0.0-ic1.4-dev-b56.3`
- Adds query-separator-free explicit routes for mobile/browser reliability.
- `GET /v1/target-resolver/venue/{venue}`
- `GET /v1/target-resolver/venue/{venue}/{YYYY-MM-DD}`
- `GET /v1/target-resolver/race/{venue}/{race}`
- `GET /v1/target-resolver/race/{venue}/{race}/{YYYY-MM-DD}`
- `GET /v1/targeted-strict-contract/race/{venue}/{race}`
- `GET /v1/targeted-strict-contract/race/{venue}/{race}/{YYYY-MM-DD}`
- Existing query-string endpoints remain unchanged for backward compatibility.
- Explicit path values are URL-decoded by the existing request path normalization.
- No fabricated race data or fallback target selection is introduced.
