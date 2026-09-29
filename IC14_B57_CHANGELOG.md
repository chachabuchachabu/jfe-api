# IC1.4 DEV-B57 — Verified Line Formation DOM Probe

- Added explicit race route: `/v1/line-formation-dom-probe/race/{venue}/{race_no}[/{YYYY-MM-DD}]`.
- Reuses B56.3 explicit target resolution before source acquisition.
- Independently verifies source-body date / venue / race identity.
- Captures source-local evidence around `並び予想`, `並び`, `ライン`, `周回予想`, `周回`, `展開予想` and likely DOM class/id names.
- Diagnostic-first: **does not infer or synthesize line formations**.
- Fail-closed when target or source-body identity is unresolved.
- Next gate: bind line formations only after LIVE DOM evidence establishes the exact source structure.
