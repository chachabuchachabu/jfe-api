# JFE API v0.8.1
Single-file Render deployment shell for KFX/JE qualification.

- `/health` => `200 UP`
- `/v1/race/{date}/{venue}/{race_no}` => `503 SOURCE_ADAPTERS_PENDING`
  until v0.9 live adapters are connected.
- No database, disk, secrets, or paid Render resources are declared.
