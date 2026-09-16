# IC1.4 DEV-B7
- Added target_date-driven End-to-End orchestrator.
- Verified venue/race gate before race acquisition.
- Connected Entry -> Rider Stats -> Odds.
- Entry failure blocks unbound downstream data.
- One race failure does not abort or contaminate another race.
- Added daily coverage and unified recovery queue.
- Preserves explicit NOT_PUBLISHED semantics for odds.
- Isolation regression corrected: prior failure was an invalid synthetic stats fixture, not a production isolation defect.
