# Manuscript Tables

## Table 1. Baseline Characteristics by Cohort

| Variable | MIMIC-IV | MIMIC-III | SMD: MIMIC-III vs MIMIC-IV | SICdb | SMD: SICdb vs MIMIC-IV |
| --- | --- | --- | --- | --- | --- |
| Number of ICU stays | 5,129 | 2,930 |  | 347 |  |
| Landmark rows | 6,883 | 4,062 |  | 685 |  |
| Age, median (IQR), years | 69.4 (58.9-79.5) | 69.7 (58.3-79.9) | 0.010 | 70.0 (55.0-75.0) | 0.145 |
| Male sex, n (%) | 2905 (56.6%) | 1612 (55.0%) | 0.033 | 210 (60.5%) | -0.079 |
| Initial KDIGO stage 1, n (%) | 1546 (30.1%) | 900 (30.7%) | -0.012 | 197 (56.8%) | -0.558 |
| Initial KDIGO stage 2, n (%) | 3583 (69.9%) | 2030 (69.3%) | 0.012 | 150 (43.2%) | 0.558 |
| SOFA score, median (IQR) | 7.0 (5.0-9.0) | 6.0 (4.0-8.0) | 0.332 | NA |  |
| OASIS score, median (IQR) | 37.0 (32.0-42.0) | 38.0 (32.0-44.0) | -0.085 | NA |  |
| SAPS II score, median (IQR) | 42.0 (34.0-52.0) | 43.0 (35.0-52.0) | -0.023 | NA |  |
| Creatinine, median (IQR), mg/dL | 1.2 (0.8-1.9) | 1.2 (0.8-2.1) | -0.160 | 1.5 (1.0-2.1) | -0.093 |
| BUN, median (IQR), mg/dL | 27.0 (18.0-43.0) | 28.0 (18.0-45.8) | -0.072 | 33.6 (22.9-46.2) | -0.092 |
| Lactate, median (IQR), mmol/L | 1.9 (1.3-3.0) | 1.9 (1.3-3.1) | -0.024 | 2.6 (1.7-4.1) | -0.349 |
| Platelet count, median (IQR) | 159.0 (104.0-229.0) | 171.0 (109.0-244.0) | -0.090 | 176.0 (117.5-256.5) | -0.173 |
| MAP, median (IQR), mmHg | 74.8 (69.6-81.4) | 74.7 (68.7-82.4) | 0.010 | 69.8 (65.9-75.1) | 0.563 |
| Urine output, median (IQR), mL | 1227 (826-2413) | 1170 (792-2249) | 0.069 | 1205 (640-2145) | 0.094 |
| Vasopressor use, n (%) | 2519 (49.1%) | 1303 (44.5%) | 0.093 | 257 (74.1%) | -0.531 |
| Mechanical ventilation, n (%) | 4722 (92.1%) | 2241 (76.5%) | 0.438 | 246 (70.9%) | 0.566 |
| Hospital mortality, n (%) | 1382 (26.9%) | 825 (28.2%) | -0.027 | 76 (21.9%) | 0.118 |

## Table 2. Landmark Rows and Outcome Event Rates

| Cohort | Landmark | Rows | Unique ICU stays | AKI progression events | Event rate | Future CRRT/RRT rate |
| --- | --- | --- | --- | --- | --- | --- |
| MIMIC-IV | 24 h | 3395 | 3395 | 1551 | 45.7% | Included in outcome |
| MIMIC-IV | 48 h | 2061 | 2061 | 925 | 44.9% | Included in outcome |
| MIMIC-IV | 72 h | 1427 | 1427 | 652 | 45.7% | Included in outcome |
| MIMIC-III with CRRT | 24 h | 1875 | 1875 | 807 | 43.0% | 2.0% |
| MIMIC-III with CRRT | 48 h | 1274 | 1274 | 548 | 43.0% | 2.2% |
| MIMIC-III with CRRT | 72 h | 913 | 913 | 407 | 44.6% | 2.6% |
| SICdb sensitivity | 24 h | 301 | 301 | 71 | 23.6% | 8.0% |
| SICdb sensitivity | 48 h | 217 | 217 | 29 | 13.4% | 2.8% |
| SICdb sensitivity | 72 h | 167 | 167 | 28 | 16.8% | 4.8% |

## Table 3. Model Performance

| Cohort | Model | N rows | N stays | Event rate | AUROC (95% CI) | AUPRC (95% CI) | Brier (95% CI) | Calibration intercept | Calibration slope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MIMIC-IV internal test | xgboost_full | 1393 | 1026 | 46.8% | 0.770 (0.743-0.799) | 0.760 (0.726-0.795) | 0.192 (0.180-0.203) | 0.108 | 0.970 |
| MIMIC-IV internal test | xgboost_crossdb | 1393 | 1026 | 46.8% | 0.766 (0.738-0.792) | 0.754 (0.719-0.787) | 0.194 (0.181-0.205) | 0.089 | 0.944 |
| MIMIC-III external KDIGO-only | xgboost_full | 4175 | 3020 | 43.6% | 0.749 (0.732-0.765) | 0.683 (0.655-0.713) | 0.203 (0.196-0.211) | -0.206 | 0.791 |
| MIMIC-III external with CRRT | xgboost_full | 4062 | 2930 | 43.4% | 0.758 (0.740-0.775) | 0.696 (0.672-0.722) | 0.198 (0.192-0.206) | -0.169 | 0.851 |
| MIMIC-III external with CRRT | xgboost_crossdb | 4062 | 2930 | 43.4% | 0.761 (0.744-0.777) | 0.703 (0.678-0.727) | 0.197 (0.190-0.205) | -0.230 | 0.866 |
| SICdb sensitivity external | xgboost_crossdb | 685 | 347 | 18.7% | 0.587 (0.524-0.651) | 0.228 (0.179-0.303) | 0.355 (0.330-0.380) | -1.651 | 0.284 |

## Table S1. Predictor Missingness

| Feature | MIMIC-IV missing % | MIMIC-III missing % | SICdb missing % |
| --- | --- | --- | --- |
| Creatinine recent | 0.7% | 0.7% | 0.0% |
| BUN recent | 0.7% | 0.7% | 0.0% |
| Lactate maximum | 33.6% | 38.6% | 9.5% |
| Platelet minimum | 1.0% | 1.0% | 1.5% |
| MAP mean | 0.1% | 1.2% | 9.2% |
| Urine output total | 1.3% | 7.5% | 12.0% |
| SOFA score | 0.0% | 0.0% | 100.0% |
| Systolic BP mean | 0.1% | 1.2% | 9.2% |
| SpO2 minimum | 0.1% | 1.1% | 9.2% |
| pH minimum | 19.8% | 11.8% | 9.8% |

## Table 4. Calibration and Clinical Utility

| Model | Cohort | Calibration intercept | Calibration slope | Brier score | DCA useful threshold range |
| --- | --- | --- | --- | --- | --- |
| XGBoost cross-database | MIMIC-IV internal test | 0.089 | 0.944 | 0.194 | 0.11-0.75 |
| XGBoost cross-database | MIMIC-III temporal/external validation | -0.23 | 0.866 | 0.197 | 0.12-0.75 |

## Table S2. Descriptive Recalibration Analysis

| Cohort | Recalibration variant | N rows | Observed event rate | Mean predicted risk | AUROC | AUPRC | Brier score | Calibration intercept | Calibration slope | Applied intercept | Applied slope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MIMIC-IV internal test | unrecalibrated | 1393 | 46.8% | 44.8% | 0.766 | 0.754 | 0.194 | 0.089 | 0.944 | 0.000 | 1.000 |
| MIMIC-IV internal test | intercept_only | 1393 | 46.8% | 46.8% | 0.766 | 0.754 | 0.193 | -0.010 | 0.944 | 0.105 | 1.000 |
| MIMIC-IV internal test | intercept_plus_slope | 1393 | 46.8% | 46.8% | 0.766 | 0.754 | 0.193 | 0.000 | 1.000 | 0.089 | 0.944 |
| MIMIC-III external with CRRT | unrecalibrated | 4062 | 43.4% | 47.5% | 0.761 | 0.703 | 0.197 | -0.230 | 0.866 | 0.000 | 1.000 |
| MIMIC-III external with CRRT | intercept_only | 4062 | 43.4% | 43.4% | 0.761 | 0.703 | 0.196 | -0.037 | 0.866 | -0.224 | 1.000 |
| MIMIC-III external with CRRT | intercept_plus_slope | 4062 | 43.4% | 43.4% | 0.761 | 0.703 | 0.195 | -0.000 | 1.000 | -0.230 | 0.866 |
| SICdb sensitivity external | unrecalibrated | 685 | 18.7% | 60.7% | 0.587 | 0.228 | 0.355 | -1.651 | 0.284 | 0.000 | 1.000 |
| SICdb sensitivity external | intercept_only | 685 | 18.7% | 18.7% | 0.587 | 0.228 | 0.162 | -0.993 | 0.284 | -2.321 | 1.000 |
| SICdb sensitivity external | intercept_plus_slope | 685 | 18.7% | 18.7% | 0.587 | 0.228 | 0.150 | 0.002 | 1.001 | -1.651 | 0.284 |

## Table S3. Landmark-Specific Unrecalibrated Performance

| Cohort | Landmark | N rows | Events | Event rate | Mean predicted risk | AUROC | AUPRC | Brier score | Calibration intercept | Calibration slope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MIMIC-III external with CRRT | 24 h | 1875 | 807 | 43.0% | 46.6% | 0.736 | 0.685 | 0.206 | -0.210 | 0.799 |
| MIMIC-III external with CRRT | 48 h | 1274 | 548 | 43.0% | 47.3% | 0.781 | 0.712 | 0.189 | -0.232 | 0.944 |
| MIMIC-III external with CRRT | 72 h | 913 | 407 | 44.6% | 49.7% | 0.784 | 0.726 | 0.191 | -0.277 | 0.902 |
| MIMIC-IV internal test | 24 h | 675 | 321 | 47.6% | 46.4% | 0.783 | 0.789 | 0.185 | 0.068 | 1.028 |
| MIMIC-IV internal test | 48 h | 427 | 196 | 45.9% | 43.4% | 0.741 | 0.694 | 0.208 | 0.063 | 0.797 |
| MIMIC-IV internal test | 72 h | 291 | 135 | 46.4% | 43.3% | 0.769 | 0.767 | 0.192 | 0.161 | 0.986 |
| SICdb sensitivity external | 24 h | 301 | 71 | 23.6% | 61.0% | 0.652 | 0.340 | 0.325 | -1.544 | 0.542 |
| SICdb sensitivity external | 48 h | 217 | 29 | 13.4% | 58.4% | 0.575 | 0.188 | 0.352 | -2.009 | 0.263 |
| SICdb sensitivity external | 72 h | 167 | 28 | 16.8% | 63.3% | 0.446 | 0.155 | 0.412 | -1.512 | -0.143 |

## Table S4. Locked Primary-Model Predictor Definitions

| Predictor | Domain | Definition | Unit | Observation window | Model aggregation | Cross-database harmonization notes |
| --- | --- | --- | --- | --- | --- | --- |
| gender | demographic | Biological sex encoded for modeling | binary/category | baseline | direct | Encoded consistently before modeling. |
| age | demographic | Age at ICU admission | years | baseline | value | May need de-identification handling in MIMIC-IV |
| landmark_hour | time | Prediction landmark after S-AKI onset | hours | landmark | direct |  |
| current_kdigo | kidney | KDIGO stage at landmark | stage | before landmark | latest | Key dynamic predictor |
| current_or_prior_max_kdigo | kidney | Maximum KDIGO stage observed up to and including the landmark | stage | S-AKI onset to landmark | direct |  |
| heart_rate_mean | vital | Heart rate | bpm | S-AKI onset to landmark | mean | Dynamic marker |
| heart_rate_max | vital | Heart rate | bpm | S-AKI onset to landmark | maximum | Dynamic marker |
| sbp_mean | vital | Systolic blood pressure | mmHg | S-AKI onset to landmark | mean | Use invasive/non-invasive hierarchy |
| sbp_min | vital | Systolic blood pressure | mmHg | S-AKI onset to landmark | minimum | Use invasive/non-invasive hierarchy |
| dbp_mean | vital | Diastolic blood pressure | mmHg | S-AKI onset to landmark | mean | Use invasive/non-invasive hierarchy |
| dbp_min | vital | Diastolic blood pressure | mmHg | S-AKI onset to landmark | minimum | Use invasive/non-invasive hierarchy |
| map_mean | vital | Mean arterial pressure | mmHg | S-AKI onset to landmark | mean | Include recent mean and minimum |
| map_min | vital | Mean arterial pressure | mmHg | S-AKI onset to landmark | minimum | Include recent mean and minimum |
| resp_rate_mean | vital | Respiratory rate | breaths/min | S-AKI onset to landmark | mean | Dynamic marker |
| resp_rate_max | vital | Respiratory rate | breaths/min | S-AKI onset to landmark | maximum | Dynamic marker |
| temp_mean | vital | Body temperature | degC | S-AKI onset to landmark | mean | Convert Fahrenheit to Celsius if needed Temperature harmonized to degrees Celsius. |
| temp_min | vital | Body temperature | degC | S-AKI onset to landmark | minimum | Convert Fahrenheit to Celsius if needed Temperature harmonized to degrees Celsius. |
| temp_max | vital | Body temperature | degC | S-AKI onset to landmark | maximum | Convert Fahrenheit to Celsius if needed Temperature harmonized to degrees Celsius. |
| spo2_mean | vital | Oxygen saturation | percent | S-AKI onset to landmark | mean | Dynamic oxygenation marker |
| spo2_min | vital | Oxygen saturation | percent | S-AKI onset to landmark | minimum | Dynamic oxygenation marker |
| creatinine_recent | kidney | Most recent serum creatinine before landmark | mg/dL | S-AKI onset to landmark | most recent | Convert umol/L to mg/dL when needed |
| creatinine_max | kidney | Maximum serum creatinine before landmark | mg/dL | S-AKI onset to landmark | maximum | Dynamic kidney injury severity |
| bun_recent | kidney | Most recent blood urea nitrogen before landmark | mg/dL | S-AKI onset to landmark | most recent | Convert units if needed SICdb urea (Harnstoff) converted to BUN using urea x 0.467. |
| bun_max | kidney | Most recent blood urea nitrogen before landmark | mg/dL | S-AKI onset to landmark | maximum | Convert units if needed SICdb urea (Harnstoff) converted to BUN using urea x 0.467. |
| bicarbonate_min | lab | Bicarbonate | mmol/L | S-AKI onset to landmark | minimum | Acid-base status |
| sodium_min | lab | Sodium | mmol/L | S-AKI onset to landmark | minimum | Electrolyte |
| sodium_max | lab | Sodium | mmol/L | S-AKI onset to landmark | maximum | Electrolyte |
| potassium_min | lab | Potassium | mmol/L | S-AKI onset to landmark | minimum | Electrolyte |
| potassium_max | lab | Potassium | mmol/L | S-AKI onset to landmark | maximum | Electrolyte |
| chloride_min | lab | Chloride | mmol/L | S-AKI onset to landmark | minimum | Electrolyte |
| chloride_max | lab | Chloride | mmol/L | S-AKI onset to landmark | maximum | Electrolyte |
| wbc_max | lab | White blood cell count | 10^9/L | S-AKI onset to landmark | maximum | Inflammation marker |
| hemoglobin_min | lab | Hemoglobin | g/dL | S-AKI onset to landmark | minimum | Anemia/illness marker |
| platelet_min | lab | Platelet count | 10^9/L | S-AKI onset to landmark | minimum | Coagulation/sepsis marker |
| hematocrit_min | lab | Hematocrit | percent | S-AKI onset to landmark | direct | Complete blood count marker. |
| lactate_max | lab | Lactate | mmol/L | S-AKI onset to landmark | maximum | Sepsis severity |
| ph_min | lab | Arterial or venous pH | pH | S-AKI onset to landmark | minimum | Prefer arterial if both available |
| urine_output_total | kidney | Total urine output before landmark | mL | S-AKI onset to landmark | sum | First-pass SQL feature; not weight-normalized |
| urine_output_count | kidney | Number of urine output records before landmark | count | S-AKI onset to landmark | count | Helps distinguish no output from no documentation |
| mechanical_ventilation | treatment | Mechanical ventilation before landmark | binary | S-AKI onset to landmark | any | Harmonize invasive ventilation if possible |
| vasopressor | treatment | Any vasopressor before landmark | binary | S-AKI onset to landmark | any | Shock marker |
| creatinine_missing | missingness | No creatinine before landmark | binary | S-AKI onset to landmark | missingness indicator | Missingness indicator |
| bun_missing | missingness | No BUN measurement before landmark | binary | S-AKI onset to landmark | direct |  |
| lactate_missing | missingness | No lactate before landmark | binary | S-AKI onset to landmark | missingness indicator | Missingness indicator |

## Table S5. Candidate Model Comparison

| Evaluation setting | Model | N rows | Event rate | AUROC | AUPRC | Brier score | Calibration intercept | Calibration slope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MIMIC-IV internal test, cross-database predictors | logistic_l2 | 1393 | 46.8% | 0.766 | 0.756 | 0.195 | -0.096 | 0.859 |
| MIMIC-IV internal test, cross-database predictors | xgboost | 1393 | 46.8% | 0.766 | 0.754 | 0.194 | 0.089 | 0.944 |
| MIMIC-IV internal test, cross-database predictors | random_forest | 1393 | 46.8% | 0.762 | 0.746 | 0.196 | -0.039 | 1.239 |
| MIMIC-IV internal test, cross-database predictors | lightgbm | 1393 | 46.8% | 0.759 | 0.739 | 0.2 | 0.039 | 0.665 |
| MIMIC-III external with CRRT, cross-database logistic | logistic_l2 | 4062 | 43.4% | 0.728 | 0.626 | 0.216 | -0.204 | 0.483 |
| MIMIC-III external with CRRT, cross-database XGBoost | xgboost_crossdb | 4062 | 43.4% | 0.761 | 0.703 | 0.197 | -0.23 | 0.866 |
