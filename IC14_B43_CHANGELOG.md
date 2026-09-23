# IC1.4 DEV-B43
Adds `/v1/entry-acquisition/YYYY-MM-DD`.

This is deliberately a live Entry Acquisition probe. It consumes B42 verified races,
selects canonical source-published racedetail URLs, fetches each race independently,
preserves SHA-256 provenance, and exposes rider/profile/car-number structure for the
next binding gate. No rider count is assumed and entries are not promoted to AVAILABLE.
