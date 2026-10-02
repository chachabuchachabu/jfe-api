# JFE B59.5-access1

- Preserves B59.5 resolver, market, result, and race-package behavior unchanged.
- Adds `GET /v1/access-probe` returning a tiny fixed JSON response with no upstream fetches.
- Purpose: distinguish ChatGPT/Render reachability restrictions from large-response or JFE pipeline issues.
- Existing `/health` remains unchanged.
