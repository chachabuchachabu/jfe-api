# IC1.4 B48.3.1 — Route Hotfix

- Version: 1.0.0-ic1.4-dev-b48.3.1
- Root cause of B48.3 blank response: `/v1/upstream-stage-probe/...` called nonexistent `self.send_json`.
- Replaced with the server's actual JSON sender `self.j`.
- AVAILABLE/PARTIAL -> HTTP 200; ERROR -> HTTP 503 with JSON body.
- No acquisition/parser/lock semantics changed.
