# IC1.4 B56.1.2

- Added source-body race identity binding before accepting scheduled start.
- Binds page date, venue and race number from the KDreams HTML title.
- Binds scheduled start only from `racecard_header` contract: `dt.start` (`発走予定`) paired `dd`.
- Rejects URL/body date or race identity drift instead of assigning a time to the requested date.
- Generic odds timestamps, AM guidance times, and sidebar deadline times are never accepted as race start.
- NOW filtering remains fail-closed for unresolved or mismatched source evidence.
