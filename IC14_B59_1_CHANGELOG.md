# JFE IC1.4 B59.1

- Hardens KDreams market parsing against the compact bet-type navigation cluster that contaminated B59.0 wide odds.
- Navigation/menu labels are no longer accepted as market section boundaries.
- Adds fail-closed duplicate/conflicting-odds checks and canonicalization for unordered bet types.
- Adds non-promoting HTML table fingerprints under Race Package `market.parser_diagnostics` to identify the real KDreams odds containers on LIVE data.
- Keeps B58.4.8 Target Resolver, racecard, line-formation evidence, and official-result logic unchanged.
- This revision intentionally prefers UNKNOWN/PARTIAL over cross-bet contamination when a source section cannot yet be independently bounded.
