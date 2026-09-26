# IC1.4 B48.4 — Single-Acquisition Entry-Lock to Odds DOM

- Version: 1.0.0-ic1.4-dev-b48.4
- Adds `/v1/single-acquisition-odds-probe/YYYY-MM-DD`.
- Performs race verification once, fetches one source-bound entry page once, validates it, creates Entry-only lock material, then derives the official odds view from the same source-bound racedetail URL.
- Does not execute the all-race B47 pipeline and does not re-run entry binding before Odds fetch.
- Bounded stages: race verification 8s, entry fetch 6s, odds fetch 6s.
- Odds remain diagnostic-only; bet types require explicit source context and invalid combinations are guarded against the active car set.
- No odds-lock or GPT handoff promotion yet.
