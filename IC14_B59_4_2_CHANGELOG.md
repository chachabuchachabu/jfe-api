# JFE IC1.4 B59.4.2

- Fix Wide odds lower-bound validation.
- Accept official KDreams Wide ranges whose minimum is exactly 1.0 (for example `1.0～1.2`).
- Continue rejecting Wide values below 1.0 and reversed ranges.
- Keep non-Wide single-odds validation unchanged (`odds > 1.0`).
- Preserve B59.4.1 explicit DOM binding, trifecta BT5 coordinate reconstruction, cardinality gates, and fail-closed behavior.
