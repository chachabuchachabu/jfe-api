# JFE v1.0 RC5.1 Hotfix

Fixes RC5 activation failure.

The race() execution path now explicitly calls:
- parse_stats(...)
- parse_line(...)

Static release guard rejects the build if the RC4/RC5 placeholder markers remain.

Expected live behavior:
- rider_stats is READY or PENDING/FAIL_CLOSED with real parser output; never the old *_IN_DEVELOPMENT marker.
- line is QUALIFIED_ORDER or PENDING/FAIL_CLOSED with order output; never the old *_IN_DEVELOPMENT marker.
- Identity, Entry, Result and Odds integrity behavior remain unchanged.
