# TRIPOD/TRIPOD+AI Submission Checklist Mapping

This working checklist maps the current manuscript to prediction-model reporting items commonly inspected under TRIPOD and TRIPOD+AI. It is intended as a submission-ready mapping draft; if the journal provides a mandatory checklist form, copy the corresponding locations and notes from this file into that form.

## Title And Abstract

| Reporting item | Manuscript location | Status | Notes |
| --- | --- | --- | --- |
| Identify the study as development and validation of a prediction model | Title; Abstract Methods | Complete | Title specifies development and multicohort validation. |
| State target population, prediction horizon and outcome | Abstract Methods; Methods: Landmark Design And Outcome | Complete | Adult ICU S-AKI; 24/48/72 h landmarks; 48 h KDIGO progression or new RRT. |
| State model type and validation cohorts | Abstract Methods; Methods: Study Design And Data Sources | Complete | XGBoost; MIMIC-IV development; MIMIC-III primary validation; SICdb/eICU exploratory. |
| Report key performance measures | Abstract Results; Results | Complete | AUROC, AUPRC, Brier score, calibration and DCA summarized. |

## Introduction

| Reporting item | Manuscript location | Status | Notes |
| --- | --- | --- | --- |
| Explain clinical context and intended use | Introduction paragraphs 1-2; Discussion | Complete | Intended use is short-term risk stratification after S-AKI onset, not automated treatment. |
| Summarize prior prediction work and gap | Introduction paragraph 2 | Complete | Prior AKI prediction models cited; current gap is post-S-AKI progression dynamic prediction. |
| State study objective | Introduction final paragraph | Complete | Objective includes dynamic landmark model, external validation and transportability analyses. |

## Source Data

| Reporting item | Manuscript location | Status | Notes |
| --- | --- | --- | --- |
| Describe data sources and versions | Methods: Study Design And Data Sources | Complete | MIMIC-IV v3.1, MIMIC-III, SICdb v1.0.8 and eICU v2.0. |
| Clarify dataset roles | Abstract Methods; Methods: Study Design And Data Sources | Complete | Roles fixed and hierarchically interpreted. |
| Ethics and consent | Ethics Statement | Complete | Secondary de-identified public databases; local exemption stated. |
| Data availability | Data Availability | Partial | Needs final code repository URL before submission. |

## Participants

| Reporting item | Manuscript location | Status | Notes |
| --- | --- | --- | --- |
| Eligibility criteria | Methods: Study Population | Complete | Adult first ICU stays, sepsis, AKI, stay duration and exclusion criteria stated. |
| Cohort flow | Results: Cohort Construction; Figure 1 | Complete | Figure exported as PDF/PNG. |
| Handling repeated records | Methods: Landmark Design And Outcome; Model Development | Complete | Landmark rows nested within ICU stays; grouped splitting and clustered bootstrap. |

## Outcome

| Reporting item | Manuscript location | Status | Notes |
| --- | --- | --- | --- |
| Define primary outcome | Methods: Landmark Design And Outcome | Complete | KDIGO progression or new RRT/CRRT within 48 h. |
| Define prediction time and horizon | Methods: Landmark Design And Outcome | Complete | 24, 48, 72 h landmarks; subsequent 48 h horizon. |
| Avoid outcome leakage | Methods: Missing Data; Landmark Design | Complete | No post-landmark predictors, future RRT indicators or discharge/death status used. |
| Database-specific outcome harmonization | Methods: Predictors And Harmonization; Model Development | Complete | MIMIC-III CRRT duration records, SICdb reconstruction caveats stated. |

## Predictors

| Reporting item | Manuscript location | Status | Notes |
| --- | --- | --- | --- |
| Predictor domains | Methods: Predictors And Harmonization | Complete | Demographics, KDIGO, kidney, vitals, labs and organ support. |
| Predictor definitions and units | Supplementary Table S4 | Complete | Source file: `results/manuscript_tables/table_s4_predictor_definitions.csv`. |
| Timing of predictor measurement | Methods: Landmark Design; Predictors And Harmonization | Complete | Values summarized from S-AKI onset to landmark. |
| Unit harmonization | Methods: Predictors And Harmonization; unit audit | Complete | MIMIC-III temperature and SICdb urea/BUN conversion documented. |

## Missing Data And Preprocessing

| Reporting item | Manuscript location | Status | Notes |
| --- | --- | --- | --- |
| Report missingness | Supplementary Table S1 | Complete | Missingness by predictor and cohort. |
| Describe imputation | Methods: Missing Data | Complete | Median numeric, most-frequent categorical, selected missingness indicators. |
| Prevent validation leakage | Methods: Missing Data | Complete | Preprocessing fitted only in MIMIC-IV training set and applied unchanged externally. |

## Model Development

| Reporting item | Manuscript location | Status | Notes |
| --- | --- | --- | --- |
| Candidate algorithms | Methods: Model Development And Validation | Complete | Logistic regression, random forest, LightGBM, XGBoost. |
| Final model and hyperparameters | Methods: Model Development And Validation | Complete | XGBoost hyperparameters reported. |
| Internal validation strategy | Methods: Model Development And Validation | Complete | Grouped train/test split by ICU stay. |
| Feature-locking and model selection | Methods: Predictors; Model Development | Complete | Cross-database predictor set and locked preprocessing/model schema stated. |

## Model Performance

| Reporting item | Manuscript location | Status | Notes |
| --- | --- | --- | --- |
| Discrimination | Results; Table 3 | Complete | AUROC and AUPRC with CIs. |
| Calibration | Results; Table 3; Table 4; calibration figure | Complete | Brier score, calibration intercept/slope and calibration plots. |
| Uncertainty intervals | Methods: Performance Analysis | Complete | Clustered bootstrap at ICU-stay level. |
| Clinical utility | Methods/Results; DCA figure | Complete | Decision-curve analysis reported for MIMIC cohorts. |
| Recalibration | Results; Supplementary Table S2 | Complete | Descriptive apparent recalibration only. |

## External Validation And Transportability

| Reporting item | Manuscript location | Status | Notes |
| --- | --- | --- | --- |
| Primary external validation | Results: Temporal/External Validation In MIMIC-III | Complete | MIMIC-III with CRRT. |
| Sensitivity validation | Results: Sensitivity Validation | Complete | SICdb labelled exploratory. |
| Negative transportability stress test | Methods; Discussion | Complete | eICU supplementary only. |
| Interpret validation hierarchy | Discussion | Complete | MIMIC-III primary; SICdb/eICU cautionary transportability analyses. |

## Explainability And AI-Specific Reporting

| Reporting item | Manuscript location | Status | Notes |
| --- | --- | --- | --- |
| Explainability method | Methods: Interpretability | Complete | XGBoost additive feature-contribution outputs. |
| Global importance and directionality | Results; Figures | Complete | Contribution importance and binned dependence outputs. |
| Avoid causal interpretation | Methods: Interpretability; Discussion | Complete | Model contributions treated as associations, not causal effects. |
| Model availability | Data Availability | Partial | Need final decision on sharing model weights. |

## Discussion And Limitations

| Reporting item | Manuscript location | Status | Notes |
| --- | --- | --- | --- |
| Main findings | Discussion paragraph 1 | Complete | Preserved MIMIC-IV/MIMIC-III performance. |
| Strengths and clinical interpretation | Discussion | Complete | Dynamic post-S-AKI risk stratification emphasized. |
| Limitations | Discussion limitations paragraph | Complete | Retrospective data, non-identical sepsis definitions, RRT ascertainment, SICdb reconstruction and no prospective workflow evaluation. |
| Avoid overclaiming | Abstract Conclusions; Discussion | Complete | No claim of bedside readiness or clinical benefit. |

## Final Submission Gaps

- Add public repository URL for code and non-identifying outputs.
- Decide whether trained model objects can be released or whether only predictor schema and reproducible scripts will be shared.
- Convert this mapping into the exact checklist template if the BMC submission system requests one.
