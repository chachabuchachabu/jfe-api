# IC1.4 DEV-B42

Introduces Race Identity Gate.

B41 live evidence exposed a false-positive race `24`. B42 does not hard-code its removal.
Instead, a race number is accepted only when source-link evidence binds it to the same
`kaisaiDateId`. Generic page text such as `24R` is no longer sufficient.

The B41 live verifier is upgraded to use this gate and preserves per-race identity URLs.
