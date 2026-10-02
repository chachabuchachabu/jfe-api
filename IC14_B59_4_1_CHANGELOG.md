# JFE IC1.4 B59.4.1

- Fix trifecta completeness: KDreams full 3連単 market is encoded as seven `odds_table bt5` coordinate tables, while explicit `A-B-C` ranking views are bounded to 100 rows.
- Reuse the previously source-verified B49.5 `nN` CSS class coordinate binder, scoped strictly inside `JS_ODDSCONTENTS_3rentan`.
- Keep B59.4 explicit DOM-id bet-type binding for all five bet types unchanged.
- Require class-bound first/second/third axes, complete active-car coverage, no conflicting cells, and theoretical combination cardinality before AVAILABLE.
- Fail closed on coordinate binding errors; no inferred or fabricated odds.
