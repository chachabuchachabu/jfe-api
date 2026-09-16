# JFE v1.0 Integrated Candidate IC1.2

Qualification diagnostics hotfix.

Changes:
- fixes JE packet pre_race core readiness: Identity + Entry + RiderStats + Odds are mandatory; Line Order is enrichment
- adds `/v1/failures-suite/{date}/{venue}/{spec}` to report only NOT READY blocks and their reasons
- RiderStats failures report missing car numbers
- Odds failures expose generic-page / identity-binding / value-count evidence
- keeps silent wrong data as UNKNOWN until external ground-truth qualification
- does not guess Line group boundaries or fabricate Odds

Example:
`/v1/failures-suite/2026-09-16/岸和田/1-10`

Not production ready. Secondary Odds adapter still requires source-route qualification.
