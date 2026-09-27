# IC1.4 B55 Change Log

- Added evidence-native Johnny Engine strict contract endpoint.
- Removed the requirement to fabricate rating/form/tactical/fit/context fields: the new contract carries source-backed `race_score` explicitly.
- Girls Keirin uses `INDIVIDUAL_RACE` with lines `NOT_APPLICABLE`; no singleton lines or cohesion are synthesized.
- Maps only exacta/quinella/trio/trifecta to the current JE market vocabulary.
- Wide is explicitly audited as excluded because current JE probability contract does not support range odds.
- Preserves source `9999.9` values and flags them; does not classify them as outliers.
- Does not invent numeric quality scores for the legacy JE 1.0 proto.
- Predictive execution remains NOT_EXECUTED pending chronological calibration/OOS validation of an evidence-native model.
