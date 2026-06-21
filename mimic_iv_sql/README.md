# MIMIC-IV SQL Skeleton

This directory contains SQL skeletons for the S-AKI dynamic prediction study.

## Assumptions

These scripts assume that MIMIC-IV v3.1 and the common MIMIC derived concepts are available.

Expected schemas:

- `mimiciv_hosp`
- `mimiciv_icu`
- `mimiciv_derived`

Expected derived tables or concepts include:

- `icustay_detail`
- `sepsis3`
- `kdigo_stages`
- `rrt` or equivalent RRT concept
- `vitalsign`
- `chemistry`
- `complete_blood_count`
- `coagulation`
- `bg`
- `sofa`
- `oasis`
- `sapsii`
- `ventilation`

If your environment uses BigQuery, replace temporary-table syntax and interval syntax as needed.

## Run Order

1. `00_create_schema.sql`
2. `01_base_cohort.sql`
3. `02_saki_onset.sql`
4. `03_landmarks_outcomes.sql`
5. `04_predictor_features.sql`
6. `05_modeling_dataset.sql`
7. `06_validation_checks.sql`

## Key Design Choices

- Unit of analysis: one row per ICU stay per landmark.
- Landmarks: 24, 48, and 72 hours after S-AKI onset.
- Predictors: only measurements at or before the landmark.
- Primary outcome: future 48-hour AKI progression or new RRT.
- Main exclusion at landmark: current KDIGO stage 3 or current/prior RRT.

## Validation

After creating the modeling dataset, run `06_validation_checks.sql` and review
`../mimic_iv_sql_validation.md` before starting model training.
