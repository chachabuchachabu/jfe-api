# IC1.4 B50 — GPT Handoff Contract

Version: `1.0.0-ic1.4-dev-b50`

Adds `GET /v1/gpt/race-input/YYYY-MM-DD`.

The endpoint reuses the canonical B49.5.2 acquisition path and emits normalized `JFE-GPT-RACE-INPUT/0.1` data for GPT/Johnny Engine. Raw HTML is excluded. Entry identity, all five market sections, provenance, source hash, acquisition timestamp, and explicit quality states are preserved.

B50 deliberately does **not** fabricate line formation, cross-source corroboration, scheduled start, outlier safety, or a synthetic coverage score. The handoff can be `READY_FOR_GPT` while the strict Data Gate remains `BLOCKED`; this separation proves transport readiness without weakening B24's no-neutral-default rule.

Focused local contract test and Python compilation pass. Live/production status remains unverified until deployed and queried on Render.
