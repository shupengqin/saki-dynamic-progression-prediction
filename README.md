# S-AKI Dynamic Progression Prediction

This repository contains reproducible code and non-identifying aggregate outputs for a multicohort prediction-model study of short-term AKI progression or new renal replacement therapy after sepsis-associated AKI onset in adult ICU patients.

## Study Overview

The study develops a dynamic landmark prediction model in MIMIC-IV v3.1 and validates it in MIMIC-III v1.4. SICdb is used as exploratory sensitivity validation, and eICU is used as a supplementary negative transportability stress test.

The primary model is a pooled-landmark XGBoost model using harmonizable cross-database predictors measured before 24, 48 and 72 hour landmarks after S-AKI onset. The primary outcome is KDIGO stage progression or new RRT/CRRT initiation within 48 hours after each landmark.

## Repository Contents

- `mimic_iv_sql/`: MIMIC-IV cohort, landmark, outcome and feature extraction SQL.
- `mimiciii_sql/`: MIMIC-III external-validation SQL, including CRRT-aware outcome extraction.
- `sicdb_sql/`: SICdb exploratory validation SQL.
- `eicu_sql_public/`: eICU supplementary stress-test SQL.
- `modeling/`: model training, external validation, calibration, table and figure scripts.
- `results/manuscript_tables/`: manuscript-ready aggregate tables.
- `results/performance_summary/`: aggregate model-performance summaries with confidence intervals.
- `results/clinical_utility/`: aggregate calibration and decision-curve table.
- `results/recalibration_analysis/`: aggregate recalibration and landmark-performance summaries.
- `variable_dictionary.csv`: predictor and variable definitions.
- `unit_harmonization_audit.md`: unit and harmonization notes.

## Data Access

Raw source data are not included. Users must obtain database access through the original distributors:

- MIMIC-IV v3.1: https://physionet.org/content/mimiciv/3.1/
- MIMIC-III v1.4: https://physionet.org/content/mimiciii/1.4/
- eICU Collaborative Research Database v2.0: https://physionet.org/content/eicu-crd/2.0/
- SICdb v1.0.8: https://physionet.org/content/sicdb/1.0.8/

## What Is Not Included

This public release excludes raw patient-level data, derived patient-level modeling datasets, patient-level prediction files, serialized model objects and local database credentials. Users with authorized access to the source databases can reproduce the analytic datasets and model objects using the provided SQL and modeling scripts.

## Reproduction Outline

1. Run the relevant SQL scripts for each database in numeric order.
2. Export the resulting modeling datasets locally.
3. Train the dynamic model with `modeling/train_dynamic_model.py`.
4. Validate locked models with `modeling/external_validate.py`.
5. Generate performance summaries, recalibration analyses, tables and figures with the scripts in `modeling/`.

Exact paths and connection details should be adapted to the user's local database environment.

## Contact

Correspondence: Xiaoye Xu, Hangzhou Seventh People's Hospital Affiliated to Zhejiang University, xuxiaoye2024@163.com.
