# IC1.4 B58.1 — Official Result Binding

- Adds exact-target official-result route.
- Before source-bound scheduled start: returns `NOT_PUBLISHED` without fetching a result page.
- After start: fetches KDreams `?pageType=result`, requires source-body date/venue/race identity, then binds only an explicit table containing `着順 / 車番 / 選手名`.
- Missing post-start result structure is `UNKNOWN`, not silently `NOT_PUBLISHED`.
- Network failure is `ERROR`; identity mismatch is `RACE_BINDING_ERROR`.
- Emits finish order, winner, integrity issues and hashes only when evidence is bound.
- Does not train or execute a predictive model.
