# JFE IC1.4 B59.0
- Freezes the B58.4.8 historical/multiday Target Resolver behavior as the upstream identity layer.
- Adds `/v1/race-package/race/{venue}/{race_no}/{date}`.
- Unifies explicit-race target identity, racecard/riders, KDreams source-published line/prediction evidence, all five odds sections, and chronology-aware official result into one fail-closed package.
- Reuses existing source-bound parsers; does not infer missing riders, formations, odds, or results.
- Component failures remain explicit and do not become `未発表` unless the source/chronology contract supports that state.
