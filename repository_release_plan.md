# Repository Release Plan

This plan defines what can be released in a public repository for the S-AKI dynamic prediction manuscript.

## Recommended Repository Name

`saki-dynamic-progression-prediction`

## Release Scope

Public repository should include:

- SQL cohort-construction scripts:
  - `mimic_iv_sql/`
  - `mimiciii_sql/`
  - `sicdb_sql/`
  - `eicu_sql_public/`
- Modeling and validation scripts:
  - `modeling/train_dynamic_model.py`
  - `modeling/external_validate.py`
  - `modeling/summarize_performance_with_ci.py`
  - `modeling/make_recalibration_outputs.py`
  - `modeling/make_manuscript_tables.py`
  - `modeling/make_publication_figures.py`
  - `modeling/export_svg_figures_with_browser.py`
- Predictor schema and data dictionaries:
  - `variable_dictionary.csv`
  - `results/manuscript_tables/table_s4_predictor_definitions.csv`
  - `unit_harmonization_audit.md`
- Aggregate non-identifying results:
  - `results/performance_summary/`
  - `results/manuscript_tables/`
  - `results/recalibration_analysis/recalibration_summary.csv`
  - `results/recalibration_analysis/landmark_performance_summary.csv`
  - `results/clinical_utility/table4_calibration_clinical_utility.csv`
- Manuscript support files:
  - `manuscript_full_draft_v1_vancouver.md`
  - `references/vancouver_references.md`
  - `tripod_ai_submission_checklist.md`
  - `bmc_submission_readiness_checklist.md`

## Do Not Release Publicly

Do not include:

- Raw MIMIC-IV, MIMIC-III, eICU or SICdb patient-level files.
- Derived patient-level modeling datasets in `data/*.csv`.
- Patient-level prediction files, including rows with stay identifiers or landmark-level predictions.
- Serialized model pickle files if releasing them could expose information derived from credentialed patient-level data. If model sharing is desired, release only after confirming source database data-use terms.
- Local database credentials, connection strings, or paths containing private machine-specific locations.

## Suggested Data Availability Wording After Repository Creation

The source datasets are available from PhysioNet or the relevant public database distributors after completion of their required credentialing and data-use agreements. Raw patient-level data and derived patient-level analytic datasets cannot be redistributed by the authors. The analysis code, SQL scripts, predictor definitions and aggregate non-identifying outputs are available at: [ADD REPOSITORY URL].

## Suggested Model Availability Wording

The locked predictor schema and model-training scripts are available in the public repository. Trained model objects are not redistributed in the initial release because they were fitted using credentialed patient-level datasets governed by source data-use agreements. Users with authorized access to the source databases can reproduce the model using the provided scripts.

## Minimum README Structure For Public Repository

1. Study overview.
2. Data access prerequisites and database versions.
3. Cohort construction order.
4. Model training command examples.
5. External validation command examples.
6. Output files and expected aggregate results.
7. Data-use restrictions and citation instructions.
8. Contact information.
