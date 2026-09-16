# IC1.4 DEV-B13
- Added strict Feature Validation Pipeline.
- DISCOVERED_FEATURE -> BACKTEST -> SHADOW_TEST -> OUT_OF_SAMPLE -> ADOPT/REJECT.
- Stage skipping prohibited.
- Threshold failures reject candidates.
- Only ADOPT sets production_enabled=true.
- ADOPT/REJECT are terminal states.
