# JFE v1.0 RC4 — Multi-Block Parser

RC4 preserves RC3 Identity/Entry/Odds integrity guards and adds a fail-closed Result parser.

## Result qualification
A completed race becomes Result READY only when:
- every Entry rider appears exactly once in Result,
- ranks are contiguous 1..N,
- result car numbers exactly equal the Entry car-number set,
- each result row binds to exactly one known rider.

It also extracts 2車複, 2車単, 3連複 and 3連単 payouts when present.

RiderStats and Line move to QUALIFYING only; they are deliberately not READY yet.
Odds remains guarded by RC3 and is deliberately not READY until live odds values and freshness are qualified.

Regression race:
2026-09-15 大宮10R / 202609152510
Expected finish: 4-1-7-5-6-2-3
Expected 3連複: 1-4-7 / 1900円
Expected 3連単: 4>1>7 / 16260円
