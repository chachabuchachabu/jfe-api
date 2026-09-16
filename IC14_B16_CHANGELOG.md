# IC1.4 DEV-B16
- Added Live Integration Gate for externally acquired source documents.
- Added provenance: source/source_url/published_at/acquired_at/parser_version/evidence.
- Missing transport document is ERROR/PARTIAL, never NOT_PUBLISHED.
- Added explicit Release Candidate Gate.
- RC requires regression PASS, compile PASS, complete live manifest, and empty recovery queue.
- Direct JFE runtime HTTP success is NOT claimed.
