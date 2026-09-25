# IC1.4 DEV-B48

Adds a source-bound Market/Odds DOM diagnostic stage after the verified Entry-only lock.

- Version: `1.0.0-ic1.4-dev-b48`
- Endpoint: `/v1/odds-dom-probe/YYYY-MM-DD`
- Uses the B42 source-published racedetail identity and switches only the official `pageType=odds` view.
- Samples the first LOCKED, source-bound race per venue for bounded diagnostics.
- Records HTTP/provenance/hash, explicit bet-type label evidence, source timestamp evidence, candidate odds table structure and per-bet-type parse counts.
- Never infers a bet type when no explicit source label is present.
- Rejects combinations containing cars outside the Entry LOCK active-car set.
- Does not promote the market parser to READY; `parser_promotion=NONE_DIAGNOSTIC_ONLY`.
- No fixed rider count and no fabricated odds.
