# JFE v1.0 RC2 — Multi-Block Qualification Probe

RC2 keeps the proven Identity/Entry parser and adds controlled live probes for Odds and Result.
It records acquisition time, source binding, latency, transport mode and an in-memory odds snapshot digest.
Unqualified parsers remain QUALIFYING/PENDING — never READY.

RiderStats and Line remain fail-closed pending their authoritative/structural adapters.
Next live test can use the completed 2026-09-15 Omiya 10R to qualify Result transport,
then an unstarted current race is required to qualify Odds freshness and Pre-Race Lock semantics.
