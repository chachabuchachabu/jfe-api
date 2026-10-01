# JFE IC1.4 B58.4.6

- Parse KDreams official-result rows by semantic table headers (`着順`, `車番`, `選手名`) instead of guessed numeric cell order.
- Preserve rider names directly from the bound result table; B50 rider data remains optional enrichment only.
- Add fail-closed integrity gates for all-empty rider names, invalid finish-position ordering, and missing winner row.
- Preserve B58.4.5 target resolution, canonical candidate deduplication, bounded result probes, and top-level diagnostics.
