# Public Release Manifest

Prepared from local project `saki_dynamic_prediction`.

## Included

- SQL scripts for MIMIC-IV, MIMIC-III, SICdb and eICU cohort construction.
- Python and R modeling, validation, recalibration, table and figure scripts.
- Variable dictionary and unit-harmonization notes.
- Aggregate manuscript tables and performance summaries.
- Aggregate recalibration and landmark-performance summaries.
- Manuscript support checklist and Vancouver manuscript draft.

## Excluded

- `data/*.csv`
- raw source database exports
- derived patient-level modeling datasets
- patient-level predictions
- `*.pkl` serialized model objects
- local credentials, connection strings and machine-specific database exports

## Validation Notes

The fair cross-database logistic baseline was externally validated in MIMIC-III with CRRT using the same predictor schema as the locked cross-database XGBoost model. Aggregate metrics are reported in `results/manuscript_tables/table_s5_candidate_model_comparison.csv`.
