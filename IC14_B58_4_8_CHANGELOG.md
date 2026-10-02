# JFE IC1.4 B58.4.8

- Adds explicit historical fallback resolution when KDreams current root discovery returns zero candidates.
- Builds day 1-3 meeting candidates from venue code + target date + race number.
- Never trusts constructed IDs directly: existing bounded source-body identity validation must uniquely prove date, venue and race.
- Exposes fallback seed, resolution evidence and failure reason under `resolver_diagnostics.historical_fallback`.
- Leaves B58.4.6 official-result semantic parser unchanged.
