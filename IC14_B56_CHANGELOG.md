# IC1.4 B56 Target Resolver
- Adds request-time JST target binding (`NOW`).
- Adds explicit venue and venue+race selection (`VENUE`, `RACE`).
- Adds source-bound Target Identity Guard; unique race selection required.
- Adds targeted strict-contract path that reuses B49-B55 pipeline for the selected race.
- NOW mode fails closed for unstarted filtering until scheduled-start evidence is bound; it never guesses race status.
- No hard-coded race count; venue codes are labels only, race identity remains source-bound.
