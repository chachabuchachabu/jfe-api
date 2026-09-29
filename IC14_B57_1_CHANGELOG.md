# IC1.4 B57.1 — Verified Line Formation Binding

- Binds only source-body-identity-verified KDreams race-detail pages.
- Scopes parsing to `racecard_footer-contents` labelled `並び予想` and `div.line_position`.
- Uses source `icon_p space` elements as formation boundaries and `pNNN` classes as car tokens.
- Makes no fixed assumptions about line count, line size, or rider count.
- Promotes lines to AVAILABLE only when every active car appears exactly once, with no duplicates or unknown cars.
- Injects verified formations into targeted strict-contract flow before B51/B55 Strict Data Gate.
- Adds `/v1/line-formation/race/{venue}/{race}[/{date}]` diagnostic/live route.
- No fabricated line/cohesion values.
