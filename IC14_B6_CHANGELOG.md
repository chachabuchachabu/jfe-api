# IC1.4 DEV-B6
- Added ACTIVE_MEETING / VERIFIED_VENUE / SALE_REFERENCE_ONLY / UNKNOWN classification.
- Added evidence reconciliation without majority-vote conflict suppression.
- Added sale-only filtering.
- Successful Race Discovery promotes venue to VERIFIED_VENUE.
- Dual sale+active evidence is retained as an auditable conflict, not discarded.
- Preserves B1-B5 regressions.
