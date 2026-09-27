# IC1.4 B53
- Adds evidence-backed structural/semantic Outlier Safety.
- Validates active car set, leg cardinality, repeated/out-of-field cars, dynamic theoretical combination counts, declared counts, duplicate conflicts, positive numeric odds, and wide min<=max.
- Explicitly preserves and permits source value 9999.9; it is not treated as an outlier.
- No statistical odds threshold or fabricated safety score.
- Adds GET /v1/outlier-safety/YYYY-MM-DD and feeds evidence into B51 strict Data Gate after B52.1 cross-source validation.
