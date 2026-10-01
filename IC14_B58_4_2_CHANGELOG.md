# JFE IC1.4 B58.4.2

- Deduplicate source-validated race candidates after multiday identity normalization.
- Canonical key: `(kaisai_date_id, venue_code, race_no)`.
- Prevent multiple discovery candidates converging on the same real race from causing `TARGET_NOT_UNIQUELY_BOUND`.
- Keeps B58.4.1 bounded identity-probe latency unchanged.
