# SICdb SQL Skeleton

This directory contains SQL skeletons for external validation using SICdb v1.0.8.

## Assumptions

Expected source schema:

- `sicdb`

Common source tables referenced by the skeleton:

- `cases`
- `laboratory`
- `medication`
- `observations`
- `d_references`

Important SICdb design notes:

- The main ICU case identifier is usually `CaseID`.
- Many event tables use an `Offset` column in seconds.
- `laboratory` and `medication` use `DrugID`, which should be joined to `d_references`.
- SICdb v1.0.6+ includes `KDIGO_AKI_168`; use it if available.
- SICdb v1.0.8 includes LOINC mapping, which can improve laboratory harmonization.

## Local Adaptation Points

Before running final analyses, confirm local table and column names. If your import lowercases identifiers, replace names such as `CaseID` with `caseid`.

Key items to verify:

- `KDIGO_AKI_168` table or field location.
- Sepsis definition using antibiotic plus microbiology/culture information.
- RRT/CRRT medication or procedure names.
- Vasopressor medication names and dose fields.
- Laboratory unit mapping through `d_references`.
- Observation names for vital signs and urine output.

## Run Order

1. `00_create_schema.sql`
2. `01_base_cohort.sql`
3. `02_sepsis_aki_onset.sql`
4. `03_landmarks_outcomes.sql`
5. `04_predictor_features.sql`
6. `05_modeling_dataset.sql`
7. `06_validation_checks.sql`

## Output

The target output is `saki_sicdb.modeling_dataset`, with column names aligned as closely as possible to MIMIC-IV and eICU.

