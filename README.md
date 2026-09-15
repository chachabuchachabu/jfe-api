# JFE v1.0 Integrated Candidate IC1

Integrated development line.

Preserved qualified blocks:
- Identity READY
- Entry READY
- RiderStats READY
- Line Order QUALIFIED_ORDER
- Result READY
- RC3 Odds Integrity Guard

New integration:
- `/v1/je-packet/{date}/{venue}/{race}`: normalized JE Race Packet.
- `/v1/qualify/{date}/{venue}/{race}`: machine-readable per-block qualification.
- Independent readiness flags: unqualified Line Groups and Odds cannot masquerade as READY.
- Pre-race and post-race data are separated for leakage-safe JE learning.

Still intentionally NOT READY:
- Line group boundaries
- Parsed/fresh live Odds
- true multi-source production failover

This candidate is for live qualification, not production.
