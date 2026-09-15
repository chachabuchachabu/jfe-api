# JFE v0.9.1 — Entry Qualification
Adds conservative live Entry parsing on top of v0.9.0 Identity validation.
Entry is READY only when 5–9 unique car numbers are extracted; otherwise it remains PENDING and no rider list is emitted.
No fabricated rider data. Other blocks remain PENDING.
Live test: `/v1/race/2026-09-15/大宮/10`
