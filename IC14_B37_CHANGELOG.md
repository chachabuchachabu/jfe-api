# IC1.4 DEV-B37
First live-discovery integration on the verified Render transport.
Adds `/v1/discovery/YYYY-MM-DD`. It fetches KDreams server-side, preserves SHA-256/provenance, reuses the dynamic venue parser, and fails closed to UNKNOWN/ERROR rather than inventing venues or NOT_PUBLISHED.
