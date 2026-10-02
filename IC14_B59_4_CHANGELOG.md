# JFE IC1.4 DEV-B59.4

- Restores five KDreams market bet types using explicit DOM container IDs discovered in B59.3.
- Binds 3連単/2車単/3連複/2車複/ワイド to `JS_ODDSCONTENTS_*`; no cross-bet text boundaries.
- Parses only explicit combination strings inside the bound container, preventing rider/profile numeric contamination.
- Preserves ordered selections for 3連単/2車単 and canonicalizes unordered selections for 3連複/2車複/ワイド.
- Stores ワイド as `odds_min` / `odds_max` range.
- Adds expected-vs-parsed combination cardinality integrity gate and conflicting-duplicate rejection.
- Market becomes AVAILABLE only when all five sections are complete and clean; otherwise remains fail-closed.
- B58 resolver, racecard, line-formation and official-result logic unchanged.
