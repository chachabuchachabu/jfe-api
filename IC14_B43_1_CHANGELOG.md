# IC1.4 DEV-B43.1

Adds `/v1/entry-summary/YYYY-MM-DD`.

It runs the existing B43 acquisition path but returns only compact parser-design evidence:
race identity, HTTP state, racer-link count, car tokens, at most three sample profile links,
and one 350-character context sample per race. The full B43 endpoint remains available.
