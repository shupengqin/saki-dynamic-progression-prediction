# Dynamic prediction of short-term kidney deterioration and renal replacement therapy in sepsis-associated acute kidney injury: development and multicohort validation using public ICU databases

## Title Page

Pengqin Shu^1; Xiaoye Xu^2*

^1 Hangzhou TCM Hospital Affiliated to Zhejiang Chinese Medical University, Hangzhou, Zhejiang, China.

^2 Hangzhou Seventh People's Hospital Affiliated to Zhejiang University, Hangzhou, Zhejiang, China.

*Corresponding author: Xiaoye Xu, Hangzhou Seventh People's Hospital Affiliated to Zhejiang University, 305 Tianmushan Road, Xihu District, Hangzhou, Zhejiang 310000, China. Email: xuxiaoye2024@163.com.

## Abstract

### Background

Sepsis-associated acute kidney injury (S-AKI) is common in critically ill patients, but risk can change rapidly after AKI onset and static admission-time models may miss clinically important deterioration.

### Methods

We developed and validated a dynamic landmark model for adult ICU patients with S-AKI. In MIMIC-IV v3.1, rows were generated at 24, 48, and 72 hours after S-AKI onset. The outcome was KDIGO stage progression or new renal replacement therapy within 48 hours. The prespecified model was a cross-database XGBoost model using harmonizable demographic, kidney, vital-sign, laboratory, and organ-support predictors. MIMIC-III was the primary temporal/external validation cohort; SICdb was exploratory sensitivity validation; eICU was a supplementary transportability stress test.

### Results

MIMIC-IV included 6,883 landmark rows from 5,129 ICU stays. MIMIC-III included 4,062 rows from 2,930 stays, with a 43.4% event rate. In MIMIC-IV internal testing, the model achieved AUROC 0.766 (95% CI, 0.738-0.792), AUPRC 0.754 (95% CI, 0.719-0.787), and Brier score 0.194 (95% CI, 0.181-0.205). In MIMIC-III external validation, performance was similar: AUROC 0.761 (95% CI, 0.744-0.777), AUPRC 0.703 (95% CI, 0.678-0.727), and Brier score 0.197 (95% CI, 0.190-0.205). In SICdb, discrimination was lower (AUROC, 0.587; 95% CI, 0.524-0.651), with substantial overprediction before recalibration. Decision-curve analysis suggested net benefit over treat-all and treat-none strategies across broad thresholds in MIMIC cohorts. Leading contributors were current KDIGO stage, recent creatinine, urine output, temperature, prior maximum KDIGO stage, systolic blood pressure, and lactate.

### Conclusions

A dynamic landmark model using harmonizable ICU predictors showed preserved performance between MIMIC-IV and MIMIC-III for short-term kidney deterioration after S-AKI onset. SICdb/eICU results indicate that phenotype alignment, local recalibration, and prospective workflow evaluation are needed before clinical deployment.

Keywords: sepsis-associated acute kidney injury; dynamic prediction; landmark model; XGBoost; external validation; MIMIC; SICdb

## Introduction

Sepsis-associated acute kidney injury (S-AKI) is a frequent and clinically important complication of critical illness. In broad ICU populations, acute kidney injury is common and is associated with worse short-term outcomes, while sepsis is one of the leading precipitants of AKI in critically ill patients [1,2,3]. The KDIGO framework provides standardized criteria for AKI diagnosis and staging, but in clinical practice AKI is not a fixed state: patients may remain stable, recover, progress to more severe KDIGO stages, or require renal replacement therapy over short time intervals [4]. This dynamic trajectory is particularly relevant after S-AKI onset, when treatment decisions often depend on repeated reassessment rather than a single admission-time risk estimate.

Several AKI prediction models have used routinely collected ICU or hospital data, including score-based critical-care models, machine-learning inpatient models and continuous EHR-based prediction systems [5,6,7]. However, many prediction efforts remain anchored to fixed time points such as ICU admission, or focus on incident AKI or mortality rather than short-term kidney deterioration after AKI has already developed. For patients with established S-AKI, the more immediate clinical question is often whether kidney injury will worsen over the next 24 to 72 hours and whether escalation of monitoring or renal-support planning is warranted. Dynamic prediction by landmarking offers a principled way to update risk estimates at prespecified time points using only information available up to each landmark [8,9]. A landmark approach is therefore well suited to modeling short-horizon AKI progression after S-AKI onset.

Developing such a model also requires attention to transportability and reporting quality. Prediction-model reporting and appraisal standards emphasize transparent cohort definition, predictor handling, validation design, risk-of-bias assessment and complete reporting of discrimination and calibration [10,11,12]. External validation is essential because apparent performance can degrade when case mix, measurement practice, database structure, or outcome ascertainment changes across health systems [13]. Calibration is especially important for clinical risk prediction because a model can rank patients acceptably while still systematically overestimating or underestimating absolute risk [14]. Decision-curve analysis can further assess whether predicted risks offer potential clinical utility across plausible decision thresholds [15].

Public critical-care databases make it possible to develop and test prediction models across independent ICU datasets. MIMIC-IV and MIMIC-III provide detailed, de-identified electronic health record data for adult ICU patients and have become widely used resources for reproducible critical-care research [16,17]. Additional databases such as SICdb and eICU provide opportunities to probe transportability across more heterogeneous care settings, although phenotype harmonization can be challenging [18]. In this study, we developed a dynamic landmark model in MIMIC-IV to predict KDIGO stage progression or new renal replacement therapy within 48 hours among adult ICU patients with S-AKI, performed primary temporal/external validation in MIMIC-III, and evaluated SICdb and eICU as exploratory transportability analyses. We prioritized a cross-database feature set, assessed discrimination, calibration and decision-curve utility, and examined model-contribution patterns to support clinical interpretability.

## Methods

### Study Design And Data Sources

This retrospective prediction-model study developed and externally validated dynamic models for predicting AKI progression among adult ICU patients with S-AKI. Model development and internal validation were performed in MIMIC-IV v3.1. Primary temporal/external validation was performed in MIMIC-III. SICdb v1.0.8 was evaluated as an exploratory sensitivity external-validation cohort because time-resolved KDIGO trajectories required reconstruction from available serum creatinine measurements and CRRT signals. The eICU Collaborative Research Database v2.0 was evaluated as a supplementary negative transportability stress test because first-pass phenotype harmonization was limited. Cohort roles were fixed before final reporting: MIMIC-IV was the development dataset, MIMIC-III was the primary validation dataset, SICdb was sensitivity validation, and eICU was supplementary only. The study followed TRIPOD-oriented reporting principles for prediction model development and validation.

### Study Population

Adult patients aged 18 years or older were eligible if they had a first ICU stay lasting at least 24 hours, met sepsis criteria, and developed AKI according to KDIGO criteria during the ICU stay. Patients receiving chronic dialysis before ICU admission, patients with identifiable end-stage kidney disease, kidney transplant recipients, and patients with insufficient time-stamped creatinine or urine-output data were excluded where these data were available. For the primary AKI progression model, landmark rows were excluded if the patient had already reached KDIGO stage 3 or had already received renal replacement therapy at or before the landmark.

Sepsis was defined according to a Sepsis-3-oriented suspected infection and organ dysfunction concept where available. In MIMIC-IV, S-AKI onset was defined as the first time point during the ICU stay at which sepsis and KDIGO AKI were both present. In MIMIC-III, where the same local Sepsis-3 concept table was not available, sepsis was approximated using derived explicit sepsis, Angus, and Martin sepsis definitions. MIMIC-III ages above 89 years were capped at 90 years to address de-identification. In SICdb, adult ICU cases with admission-form sepsis marked as present were used for sensitivity validation. These database-specific differences were treated as part of the transportability problem rather than as interchangeable definitions.

### Landmark Design And Outcome

Dynamic prediction rows were generated at 24, 48, and 72 hours after S-AKI onset. At each landmark, only data measured at or before the landmark were used as predictors. The prediction horizon was the subsequent 48 hours. The unit of analysis was a landmark-level row nested within an ICU stay. Patient-level splitting was used during model development to prevent rows from the same ICU stay from contributing to both training and internal test sets.

The primary outcome was AKI progression within 48 hours after each landmark, defined as any progression from KDIGO stage 1 to stage 2 or 3, progression from KDIGO stage 2 to stage 3, or new initiation of renal replacement therapy or continuous renal replacement therapy. Secondary and exploratory outcomes included new RRT/CRRT initiation, kidney non-recovery by discharge, and adverse kidney outcome composites in the broader project files; the present manuscript focuses on 48-hour AKI progression or new RRT/CRRT as the primary outcome.

Outcome ascertainment used laboratory and RRT/CRRT records documented within the 48-hour prediction horizon. Death and discharge within the horizon were not modeled as competing events and were not used as predictors. Landmark rows were therefore interpreted as predictions of documented short-term KDIGO progression or new renal-support initiation among rows eligible at the landmark, with death/discharge handling addressed as a limitation.

### Predictors And Harmonization

Candidate predictors included demographics, current KDIGO stage, previous maximum KDIGO stage, kidney-function measures, vital signs, laboratory measurements and organ support. Dynamic variables were summarized from S-AKI onset to each landmark using clinically meaningful summaries such as most recent value, mean, minimum, maximum, count, and total exposure. The final primary model used a locked cross-database predictor set designed to be more portable across MIMIC-IV, MIMIC-III and SICdb. The predictor set was locked before primary external validation was summarized for manuscript reporting. The complete locked predictor list, measurement windows and harmonization notes are provided in Supplementary Table S4.

Feature units and definitions were harmonized before validation. In MIMIC-III, blood-pressure predictors were harmonized across CareVue and MetaVision arterial and non-invasive systolic, diastolic and mean arterial-pressure labels, excluding alarm thresholds, pulmonary-artery pressures, cuff-pressure fields and other non-systemic pressure labels. MIMIC-III temperature values were harmonized before aggregation by converting plausible Fahrenheit values to Celsius, retaining plausible Celsius values, and excluding implausible temperature values from temperature summaries. In SICdb, S-AKI onset was reconstructed using serum creatinine-based KDIGO staging because the locally available KDIGO fields were processed summary fields rather than direct time-resolved KDIGO trajectories. SICdb urea measurements labelled as Harnstoff were converted to blood urea nitrogen using urea x 0.467 before model application.

### Missing Data

Missingness was summarized by cohort and by predictor. The machine-learning pipeline used median imputation for numeric predictors, most-frequent imputation for categorical predictors, and missingness indicators for selected clinically important laboratory values, including creatinine, BUN and lactate. Imputation parameters and all preprocessing steps were fitted only in the MIMIC-IV training set and then applied unchanged to the MIMIC-IV test set and external validation cohorts. Missingness tables are reported in the supplementary materials. No predictor values measured after the landmark, discharge outcomes, future RRT indicators, future laboratory values, or death/discharge status were used as model inputs.

### Model Development And Validation

Models were trained in MIMIC-IV. Candidate algorithms included L2-regularized logistic regression, random forest, LightGBM and XGBoost. The final selected model was a pooled landmark XGBoost model including landmark hour as a predictor. XGBoost was fitted with 300 trees, maximum tree depth of 3, learning rate of 0.03, subsampling fraction of 0.8 and column-subsampling fraction of 0.8. Model selection considered discrimination, calibration, decision-curve analysis, external-validatable feature availability and interpretability. Internal validation used a grouped train/test split by ICU stay to prevent rows from the same stay appearing in both training and test sets.

The analysis followed a fixed modeling sequence. Candidate algorithms were compared within MIMIC-IV using grouped internal validation. A cross-database predictor set was then selected to maximize availability across MIMIC-IV, MIMIC-III and SICdb while preserving internal performance. The final preprocessing pipeline, predictor schema and XGBoost model were locked before the primary MIMIC-III with-CRRT validation results were summarized for manuscript reporting. The locked pipeline was applied without refitting to external cohorts.

Primary external validation used KDIGO progression and new CRRT initiation recovered from time-stamped `crrt_durations` records in MIMIC-III. Because renal-support ascertainment differed by database, the manuscript uses RRT/CRRT terminology when describing the harmonized outcome and CRRT-specific terminology when referring to MIMIC-III duration records. SICdb validation was treated as exploratory because its sepsis ascertainment, KDIGO reconstruction and case mix differed more substantially from the MIMIC cohorts. eICU was treated as a negative transportability stress test because local S-AKI phenotype harmonization was limited. External validation results are therefore reported hierarchically, with MIMIC-III as the primary validation evidence and SICdb/eICU as analyses of robustness under less aligned definitions.

Several safeguards were used to reduce prediction-model bias. Patient-level splitting prevented rows from the same ICU stay appearing in both training and internal test sets. Imputation, scaling and encoding parameters were learned only in the MIMIC-IV training data. Predictor construction was restricted to data available at or before each landmark, and future outcomes, future measurements, discharge time, mortality status and post-landmark RRT/CRRT indicators were excluded from model inputs. External validation was performed without model refitting; recalibration analyses were reported separately as descriptive apparent recalibration rather than as primary validation performance.

### Performance Analysis

Discrimination was assessed using AUROC and AUPRC. Calibration was evaluated using calibration plots, calibration intercept, calibration slope and Brier score. Confidence intervals for AUROC, AUPRC and Brier score were estimated using clustered bootstrap resampling at the ICU-stay level. Clinical utility was assessed with decision-curve analysis across clinically plausible risk thresholds. Descriptive recalibration analyses included intercept-only recalibration and logistic recalibration of the model logit. These recalibration analyses were estimated within each evaluation cohort and were interpreted as apparent recalibration summaries rather than primary external validation performance.

### Interpretability

Model interpretability was assessed using XGBoost additive feature-contribution outputs for the locked cross-database model in the MIMIC-IV internal test set. Global mean absolute contributions were used to identify leading predictors, and binned dependence summaries were used to describe the direction and approximate shape of model associations. These analyses were interpreted as model-contribution patterns rather than causal effects.

### Software

SQL was used for cohort construction and feature extraction. Python was used for model development, validation, recalibration analysis and table generation. R was used for the final publication figure exports. The reproducibility manifest records the executable scripts, derived output files and environment details.

## Results

### Cohort Construction

In MIMIC-IV, 6,883 landmark rows from 5,129 ICU stays were available for model development and internal validation. The overall event rate for 48-hour AKI progression or new renal replacement therapy was approximately 45%.

For temporal/external validation in MIMIC-III, adult first ICU stays were screened using derived explicit sepsis, Angus and Martin sepsis definitions. After identifying S-AKI onset and applying landmark eligibility criteria, the primary with-CRRT validation cohort included 4,062 landmark rows from 2,930 ICU stays. The event rate was 43.4%, and new CRRT initiation within the subsequent 48 hours occurred in 2.2% of landmark rows. Landmark-specific event rates were 43.0% at 24 hours, 43.0% at 48 hours and 44.6% at 72 hours.

For exploratory sensitivity validation in SICdb, 793 adult ICU cases with admission-form sepsis were eligible. After reconstructing creatinine-based S-AKI onset, applying dynamic landmark criteria and excluding rows with prior CRRT, 685 landmark rows from 347 ICU stays were available. The event rate was 18.7%, with landmark-specific event rates of 23.6% at 24 hours, 13.4% at 48 hours and 16.8% at 72 hours. New CRRT within the subsequent 48 hours occurred in 5.5% of SICdb landmark rows.

### Internal Validation

In the MIMIC-IV internal test set, the full-feature XGBoost model achieved an AUROC of 0.770 (95% CI, 0.743-0.799), an AUPRC of 0.760 (95% CI, 0.726-0.795), and a Brier score of 0.192 (95% CI, 0.180-0.203). Calibration was acceptable, with a calibration slope of 0.970.

A cross-database transportable XGBoost model, restricted to predictors that were easier to harmonize across MIMIC-IV and MIMIC-III, showed similar internal performance: AUROC 0.766 (95% CI, 0.738-0.792), AUPRC 0.754 (95% CI, 0.719-0.787), Brier score 0.194 (95% CI, 0.181-0.205), and calibration slope 0.944.

Candidate-model comparisons using the cross-database predictor set showed that L2-regularized logistic regression and XGBoost had nearly identical internal discrimination in MIMIC-IV (AUROC 0.766 for both; AUPRC 0.756 and 0.754, respectively). Random forest and LightGBM had slightly lower internal discrimination. In the fair MIMIC-III with-CRRT external-validation comparison using the same cross-database predictors, logistic regression achieved an AUROC of 0.728, an AUPRC of 0.626, a Brier score of 0.216 and a calibration slope of 0.483, whereas the locked cross-database XGBoost model achieved an AUROC of 0.761, an AUPRC of 0.703, a Brier score of 0.197 and a calibration slope of 0.866. These candidate-model results are shown in Supplementary Table S5 and support interpreting algorithm choice together with feature portability, calibration and external validation rather than internal discrimination alone.

### Temporal/External Validation In MIMIC-III

The full-feature MIMIC-IV XGBoost model retained discrimination in MIMIC-III, with an AUROC of 0.758 (95% CI, 0.740-0.775), an AUPRC of 0.696 (95% CI, 0.672-0.722), and a Brier score of 0.198 (95% CI, 0.192-0.206). Calibration slope was 0.851, suggesting moderate overfitting or case-mix shift but acceptable transportability for an unrecalibrated model.

The cross-database feature model performed slightly better in MIMIC-III, with an AUROC of 0.761 (95% CI, 0.744-0.777), an AUPRC of 0.703 (95% CI, 0.678-0.727), and a Brier score of 0.197 (95% CI, 0.190-0.205). Calibration slope was 0.866. Landmark-specific discrimination improved over time, with AUROCs of 0.736, 0.781 and 0.784 at 24, 48 and 72 hours, respectively.

### Sensitivity Validation

In an earlier MIMIC-III validation using KDIGO progression alone without explicit time-stamped CRRT initiation, the full-feature XGBoost model achieved an AUROC of 0.749 (95% CI, 0.732-0.765), an AUPRC of 0.683 (95% CI, 0.655-0.713), and a Brier score of 0.203 (95% CI, 0.196-0.211). Adding time-stamped CRRT events, capping de-identified ages above 89 years at 90 years, and improving blood-pressure extraction modestly improved discrimination and Brier score.

In SICdb sensitivity validation, the unrecalibrated cross-database XGBoost model showed attenuated transportability: AUROC 0.587 (95% CI, 0.524-0.651), AUPRC 0.228 (95% CI, 0.179-0.303), and Brier score 0.355 (95% CI, 0.330-0.380). Calibration was poor, with a calibration intercept of -1.651 and calibration slope of 0.284. These findings were interpreted as exploratory because SICdb required creatinine-based KDIGO reconstruction, used a different sepsis ascertainment strategy and had a substantially lower event rate than the MIMIC validation cohorts.

In the eICU supplementary stress test, 4,767 landmark rows from 2,574 ICU stays were evaluated, with an event rate of 24.5%. The cross-database XGBoost model showed weak transportability in this less harmonized phenotype (AUROC 0.560, AUPRC 0.304, Brier score 0.285 and calibration slope 0.261), supporting its interpretation as a negative transportability stress test rather than validation evidence.

Landmark-specific analyses showed that discrimination in MIMIC-III improved from 24 to 72 hours after S-AKI onset, with AUROCs of 0.736, 0.781 and 0.784 at 24, 48 and 72 hours, respectively. In contrast, SICdb performance was unstable across landmarks, with AUROCs of 0.652, 0.575 and 0.446, consistent with weaker transportability in this sensitivity cohort.

### Calibration, Clinical Utility And Interpretability

The cross-database XGBoost model showed acceptable calibration in internal testing and moderate calibration drift in MIMIC-III. In MIMIC-IV internal testing, the calibration intercept was 0.089, the calibration slope was 0.944, and the Brier score was 0.194. In MIMIC-III temporal/external validation, the calibration intercept was -0.230, the calibration slope was 0.866, and the Brier score was 0.197.

Decision-curve analysis suggested potential clinical utility across a broad range of decision thresholds. The model provided greater net benefit than both treat-all and treat-none strategies across threshold probabilities of 0.11-0.75 in MIMIC-IV and 0.12-0.75 in MIMIC-III.

Descriptive recalibration analyses suggested that MIMIC-III required only modest calibration adjustment: intercept-plus-slope recalibration improved the Brier score from 0.197 to 0.195 without changing discrimination. SICdb showed much larger calibration-in-the-large shift, with mean predicted risk of 60.7% compared with an observed event rate of 18.7%. Intercept-only recalibration reduced the SICdb Brier score from 0.355 to 0.162, and intercept-plus-slope recalibration reduced it to 0.150, but AUROC remained 0.587. These analyses indicate that SICdb performance loss reflected both severe miscalibration and reduced risk ranking.

TreeSHAP-style XGBoost contribution analysis was performed for the cross-database feature model in the MIMIC-IV internal test set. The strongest contributor was current KDIGO stage, accounting for 34.6% of the total absolute model contribution. Other leading predictors were recent creatinine, cumulative urine output, mean temperature, current-or-prior maximum KDIGO stage, mean systolic blood pressure, maximum creatinine, maximum lactate, minimum SpO2, minimum chloride, urine-output measurement count, and sex. Directionality analyses supported clinical plausibility: higher recent creatinine, higher maximum creatinine, higher lactate, higher heart rate, and higher current-or-prior KDIGO stage contributed toward higher predicted risk, whereas greater urine output and more favorable vital signs generally contributed toward lower predicted risk.

## Discussion

In this retrospective multicohort prediction-model study, a dynamic landmark model developed in MIMIC-IV predicted short-term kidney deterioration after S-AKI onset with consistent performance in MIMIC-III temporal/external validation. The selected cross-database XGBoost model preserved internal discrimination in MIMIC-IV and achieved an AUROC of 0.761 and AUPRC of 0.703 in MIMIC-III, with moderate calibration drift and a Brier score of 0.197. These results support the central premise of the study: after S-AKI has occurred, repeated risk updating at clinically recognizable time points can provide useful short-horizon information about subsequent KDIGO progression or new renal replacement therapy.

The clinical motivation for this approach differs from admission-time AKI prediction. Prior AKI prediction studies have shown that EHR-derived models can identify patients at risk of future AKI, but the present study focuses on a narrower post-onset problem: whether established S-AKI will progress in the next 48 hours [5,6,7]. For patients with established S-AKI, the immediate question is often not whether AKI will occur, but whether injury will progress over the next one to two days and whether closer monitoring, nephrology consultation, fluid and hemodynamic reassessment, or renal-support planning may be needed. The landmark design addresses this use case by anchoring predictions at 24, 48 and 72 hours after S-AKI onset and restricting predictors to information available before each landmark. This framing is aligned with landmarking as a dynamic prediction strategy and avoids using future information when estimating short-term risk [8,9].

External validation was central to the study design. The MIMIC-III validation results suggest that the model learned risk patterns that were not restricted to one database version or one development sample. Discrimination was preserved despite differences in data era, coding practice, sepsis ascertainment and feature extraction. Internal candidate-model results showed that logistic regression and XGBoost had similar apparent discrimination when trained on the same cross-database predictors, but the fair MIMIC-III external comparison favored the locked cross-database XGBoost pipeline, particularly for AUPRC, Brier score and calibration slope. This pattern supports the decision to prioritize measurement portability, calibration and external validation evidence rather than algorithm complexity alone. It is also consistent with prediction-model guidance emphasizing that external validation and transportability often depend as much on stable measurement definitions as on algorithmic complexity [10,13].

Calibration findings require a more cautious interpretation. In MIMIC-III, calibration drift was moderate and apparent recalibration produced only small Brier-score improvement, suggesting that the unrecalibrated model was reasonably aligned but not perfectly transportable in absolute risk. In SICdb, however, the model substantially overpredicted risk: the mean predicted risk was 60.7% compared with an observed event rate of 18.7%, and the calibration slope was low. Intercept-only recalibration improved the SICdb Brier score but did not improve AUROC, indicating that part of the problem was calibration-in-the-large while part reflected weaker risk ranking. This distinction matters because recalibration can adjust absolute risk but cannot fully repair poor discrimination [14].

The SICdb and eICU analyses therefore serve a different role from the MIMIC-III validation. SICdb provided a useful third-database sensitivity test, but the phenotype required admission-form sepsis ascertainment and creatinine-based reconstruction of time-resolved AKI trajectories. Its lower event rate, distinct case mix and different measurement structure make it inappropriate to treat SICdb as co-primary validation evidence. Similarly, the eICU analysis is best interpreted as a negative transportability stress test because the local phenotype relied on less harmonized infection, urine-output and RRT/CRRT definitions. This hierarchy is important for interpretation: the study provides supportive evidence for transportability across closely harmonized MIMIC cohorts and cautionary evidence that performance may degrade when the clinical phenotype is rebuilt under different documentation structures.

The model-contribution analysis was clinically plausible. Current KDIGO stage, recent creatinine, cumulative urine output and prior maximum KDIGO stage were leading contributors, which is expected for a model predicting subsequent AKI progression. Hemodynamic and sepsis-severity markers, including systolic blood pressure, lactate, temperature and oxygenation, also contributed to risk estimates. These patterns support face validity, but they should not be interpreted as causal effects. The model uses associations among evolving physiologic measurements to rank short-term risk, and clinical interpretation should remain anchored to prediction rather than mechanistic inference.

Decision-curve analysis suggested potential clinical utility across a broad range of thresholds in the MIMIC cohorts, but this does not establish clinical benefit. A prediction model can have favorable discrimination and net benefit in retrospective data yet still fail to improve care if predictions are poorly integrated into workflow, trigger ineffective actions, or contribute to alert fatigue. The most defensible clinical interpretation is that the model may help identify S-AKI patients who warrant closer reassessment or renal-support planning in research or quality-improvement settings, provided that local calibration, clinical thresholds and prospective implementation are evaluated first [15].

This study has several limitations. First, all analyses were retrospective and based on routinely collected ICU data, so measurement frequency, missingness and treatment decisions may reflect clinical behavior as well as patient physiology. Second, sepsis definitions were not identical across databases: MIMIC-IV used a Sepsis-3-oriented concept, whereas MIMIC-III relied on derived explicit sepsis, Angus and Martin definitions. Third, RRT/CRRT ascertainment differed by database, and MIMIC-III validation primarily recovered time-stamped CRRT initiation from duration records. Fourth, death and discharge within the 48-hour prediction horizon were not modeled as competing events, which may affect outcome interpretation when post-landmark laboratory surveillance is shortened by early death or discharge. Fifth, SICdb required creatinine-based KDIGO reconstruction and lacked several severity-score predictors in the extracted sensitivity cohort, making it unsuitable as co-primary validation evidence. Sixth, although the model used harmonized predictors, local laboratory practices, unit conventions and documentation patterns can still affect calibration. Seventh, the analysis did not compare the model against clinician judgement or test whether predictions would change management. Finally, the study did not assess whether real-time predictions improve patient outcomes, and the model should not be considered ready for bedside deployment without prospective validation and workflow evaluation.

In summary, a dynamic landmark XGBoost model using harmonizable cross-database predictors showed preserved discrimination and acceptable calibration in MIMIC-IV and MIMIC-III for predicting short-term AKI progression or new RRT after S-AKI onset. The attenuated SICdb and eICU results emphasize that transportability depends on phenotype alignment, event rate, measurement practice and local calibration. Prospective validation, model updating and workflow evaluation are needed before clinical deployment.

## Availability of data and materials

This study used publicly available, de-identified critical-care databases accessed under their respective data-use requirements. MIMIC-IV v3.1, MIMIC-III v1.4, the eICU Collaborative Research Database v2.0 and SICdb v1.0.8 are available through PhysioNet after completion of the required credentialing and data-use agreements where applicable. Because the underlying patient-level data are governed by third-party data-use agreements, raw data and derived patient-level analytic datasets cannot be redistributed by the authors. Analysis code, cohort-construction scripts, feature definitions, model-training scripts and non-identifying aggregate results will be made available at [FINAL_PUBLIC_CODE_REPOSITORY_URL] before final publication. Trained model objects are not planned for the initial public release because they were fitted using credentialed patient-level datasets; users with authorized database access can reproduce the model using the provided scripts.

## Ethics approval and consent to participate

This retrospective study used only de-identified secondary data. MIMIC-IV, MIMIC-III and eICU are released through PhysioNet under credentialed-access data-use requirements. The present analysis did not involve direct patient contact, intervention, re-identification, or access to identifiable protected health information. SICdb is distributed as an anonymized intensive-care database; the PhysioNet project documentation states that the dataset was anonymized under GDPR and additionally follows HIPAA de-identification requirements, and that SICdb was approved by the local ethical commission of Land Salzburg, Austria (EK Nr: 1115/2021). The authors confirm that this secondary analysis of publicly available de-identified databases was exempt from additional local ethics review. Informed consent was not required for this secondary analysis because all source databases were de-identified and governed by their original data-use approvals.

## Competing interests

The authors declare that they have no competing interests.

## Funding

This study received no external funding.

## Authors' contributions

Pengqin Shu: conceptualization, methodology, data curation, formal analysis, investigation, visualization, writing original draft. Xiaoye Xu: conceptualization, supervision, project administration, methodology, writing review and editing. Both authors reviewed and approved the final manuscript.

## References

1. Hoste EAJ, Bagshaw SM, Bellomo R, Cely CM, Colman R, Cruz DN, et al. Epidemiology of acute kidney injury in critically ill patients: the multinational AKI-EPI study. Intensive Care Med. 2015;41:1411-1423. doi:10.1007/s00134-015-3934-7.
2. Kellum JA, Romagnani P, Ashuntantang G, Ronco C, Zarbock A, Anders HJ. Acute kidney injury. Nat Rev Dis Primers. 2021;7:52. doi:10.1038/s41572-021-00284-z.
3. Bagshaw SM, Uchino S, Bellomo R, Morimatsu H, Morgera S, Schetz M, et al. Septic acute kidney injury in critically ill patients: clinical characteristics and outcomes. Clin J Am Soc Nephrol. 2007;2:431-439. doi:10.2215/CJN.03681106.
4. Kidney Disease: Improving Global Outcomes Acute Kidney Injury Work Group. KDIGO Clinical Practice Guideline for Acute Kidney Injury. Kidney Int Suppl. 2012;2:1-138. doi:10.1038/kisup.2012.1.
5. Flechet M, Guiza F, Schetz M, Wouters PJ, Vanhorebeek I, Derese I, et al. AKIpredictor, an online prognostic calculator for acute kidney injury in adult critically ill patients: development, validation and comparison to serum neutrophil gelatinase-associated lipocalin. Crit Care. 2017;21:39. doi:10.1186/s13054-017-1648-4.
6. Koyner JL, Carey KA, Edelson DP, Churpek MM. The development of a machine learning inpatient acute kidney injury prediction model. Crit Care Med. 2018;46:1070-1077. doi:10.1097/CCM.0000000000003123.
7. Tomasev N, Glorot X, Rae JW, Zielinski M, Askham H, Saraiva A, et al. A clinically applicable approach to continuous prediction of future acute kidney injury. Nature. 2019;572:116-119. doi:10.1038/s41586-019-1390-1.
8. van Houwelingen HC. Dynamic prediction by landmarking in event history analysis. Scand J Stat. 2007;34:70-85. doi:10.1111/j.1467-9469.2006.00529.x.
9. Putter H, van Houwelingen HC. Dynamic prediction by landmarking as an alternative for multi-state modeling: an application to acute lymphoid leukemia data. Biometrics. 2017;73:563-572. doi:10.1111/biom.12438.
10. Collins GS, Reitsma JB, Altman DG, Moons KGM. Transparent Reporting of a multivariable prediction model for Individual Prognosis Or Diagnosis (TRIPOD): the TRIPOD statement. Ann Intern Med. 2015;162:55-63. doi:10.7326/M14-0697.
11. Wolff RF, Moons KGM, Riley RD, Whiting PF, Westwood M, Collins GS, et al. PROBAST: a tool to assess the risk of bias and applicability of prediction model studies. Ann Intern Med. 2019;170:51-58. doi:10.7326/M18-1376.
12. Collins GS, Dhiman P, Andaur Navarro CL, Ma J, Hooft L, Reitsma JB, et al. TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. BMJ. 2024;385:e078378. doi:10.1136/bmj-2023-078378.
13. Steyerberg EW, Vergouwe Y. Towards better clinical prediction models: seven steps for development and an ABCD for validation. Eur Heart J. 2014;35:1925-1931. doi:10.1093/eurheartj/ehu207.
14. Van Calster B, McLernon DJ, van Smeden M, Wynants L, Steyerberg EW. Calibration: the Achilles heel of predictive analytics. BMC Med. 2019;17:230. doi:10.1186/s12916-019-1466-7.
15. Vickers AJ, Elkin EB. Decision curve analysis: a novel method for evaluating prediction models. Med Decis Making. 2006;26:565-574. doi:10.1177/0272989X06295361.
16. Johnson AEW, Bulgarelli L, Shen L, Gayles A, Shammout A, Horng S, et al. MIMIC-IV, a freely accessible electronic health record dataset. Sci Data. 2023;10:1. doi:10.1038/s41597-022-01899-x.
17. Johnson AEW, Pollard TJ, Shen L, Lehman L-WH, Feng M, Ghassemi M, et al. MIMIC-III, a freely accessible critical care database. Sci Data. 2016;3:160035. doi:10.1038/sdata.2016.35.
18. Pollard TJ, Johnson AEW, Raffa JD, Celi LA, Mark RG, Badawi O. The eICU Collaborative Research Database, a freely available multi-center database for critical care research. Sci Data. 2018;5:180178. doi:10.1038/sdata.2018.178.
