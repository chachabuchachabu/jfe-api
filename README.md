# JFE v0.9.2 — Entry Fail-Safe Hotfix
Live v0.9.1 exposed a false-positive Entry READY: six rows were emitted for a seven-rider race and two labels were misread as names.
v0.9.2 tightens validation: contiguous car numbers, expanded label rejection, and fail-closed behavior.
If extraction is uncertain, Entry stays PENDING and riders are not emitted.
