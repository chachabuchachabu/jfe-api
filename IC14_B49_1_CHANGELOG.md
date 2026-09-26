# IC1.4 B49.1 — Source-Binding Hotfix

- Version: 1.0.0-ic1.4-dev-b49.1
- Reuses the B48.4 live-pass source binding shape: venue.state == VERIFIED_VENUE, evidence[] -> race_identity_evidence.
- Removes the incorrect B49 dependency on meeting_state and the nonexistent evidence.race_identity_urls shape.
- Adds source_binding_diagnostics and fail-closed NO_SOURCE_BOUND_RACE_AFTER_VERIFICATION reporting.
- Market binding logic itself is unchanged.
