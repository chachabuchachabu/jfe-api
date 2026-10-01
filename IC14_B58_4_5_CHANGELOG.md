# JFE IC1.4 B58.4.5

- Fix official-result TypeError caused by calling `_b5612_page_identity_and_start` with three arguments although its contract accepts raw HTML only.
- Add `_b5845_result_identity` adapter to reuse the existing HTML parser and separately validate target date, venue, and race number.
- Fix B58.4.4 stage-probe result URL construction to pass `source_racedetail_url` instead of the selected-target object.
- Preserve B58.4.4 resolver decoupling, bounded result probes, fail-closed behavior, and top-level JSON exception diagnostics.
