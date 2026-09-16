# JFE v1.0 Integrated Candidate IC1.1

Qualification hotfix. Not production-ready. Free Render compatible.

Changes:
- Correct pre-race readiness: mandatory core = Identity + Entry + RiderStats + Odds. `enriched_ready` additionally requires Line Order.
- `silent_wrong_data` is no longer hard-coded false. It is `UNKNOWN` until external ground-truth qualification proves otherwise.
- Generic/unbound Odds templates are classified `ODDS_GENERIC_PAGE`, not `JFE-05 SOURCE_CONFLICT`.
- RiderStats parser broadened for 5-9 rider layouts while preserving exact Entry binding and fail-closed behavior.
- Added compact qualification suite endpoint: `/v1/qualify-suite/YYYY-MM-DD/VENUE/1-10`.
- Existing Identity/Entry/Line/Result/Odds integrity behavior retained.

Still pending qualification:
- Actual parsed/fresh Odds READY.
- Explicit Line group boundaries.
- True independent secondary-source Odds adapter/failover.
- 50/100-race external ground-truth qualification.
