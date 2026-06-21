# Unit Harmonization Audit

This audit summarizes value ranges for the locked cross-database predictors most vulnerable to unit mismatch. Ranges are descriptive and should be reviewed alongside extraction code and database dictionaries before submission.

| Feature | Clinical label | Cohort | Expected unit | N observed | P1 | Median | P99 | Max | Audit note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| creatinine_recent | Serum creatinine | MIMIC-IV | mg/dL | 6833 | 0.30 | 1.10 | 6.20 | 15.90 | All extracted values are interpreted as mg/dL. SICdb KDIGO timing is reconstructed from serum creatinine values. |
| creatinine_recent | Serum creatinine | MIMIC-III | mg/dL | 4033 | 0.30 | 1.20 | 8.50 | 13.00 | All extracted values are interpreted as mg/dL. SICdb KDIGO timing is reconstructed from serum creatinine values. |
| creatinine_recent | Serum creatinine | SICdb | mg/dL | 685 | 0.44 | 1.40 | 3.90 | 3.97 | All extracted values are interpreted as mg/dL. SICdb KDIGO timing is reconstructed from serum creatinine values. |
| bun_recent | Blood urea nitrogen | MIMIC-IV | mg/dL | 6834 | 6.00 | 28.00 | 116.00 | 268.00 | MIMIC values are BUN in mg/dL. SICdb Harnstoff is urea and was converted to BUN using urea x 0.467. |
| bun_recent | Blood urea nitrogen | MIMIC-III | mg/dL | 4032 | 7.00 | 29.00 | 121.00 | 216.00 | MIMIC values are BUN in mg/dL. SICdb Harnstoff is urea and was converted to BUN using urea x 0.467. |
| bun_recent | Blood urea nitrogen | SICdb | mg/dL | 685 | 6.46 | 34.09 | 91.48 | 104.14 | MIMIC values are BUN in mg/dL. SICdb Harnstoff is urea and was converted to BUN using urea x 0.467. |
| lactate_max | Lactate | MIMIC-IV | mmol/L | 4567 | 0.60 | 1.80 | 11.40 | 22.00 | Values are treated as mmol/L across cohorts. |
| lactate_max | Lactate | MIMIC-III | mmol/L | 2496 | 0.60 | 1.80 | 12.11 | 27.70 | Values are treated as mmol/L across cohorts. |
| lactate_max | Lactate | SICdb | mmol/L | 620 | 0.91 | 2.68 | 16.15 | 18.85 | Values are treated as mmol/L across cohorts. |
| temp_mean | Temperature | MIMIC-IV | degC | 6571 | 35.80 | 37.00 | 38.39 | 40.10 | MIMIC temperatures were harmonized to Celsius in the source extraction. SICdb temperatures are interpreted as Celsius. |
| temp_mean | Temperature | MIMIC-III | degC | 3994 | 35.55 | 36.99 | 38.55 | 40.10 | MIMIC temperatures were harmonized to Celsius in the source extraction. SICdb temperatures are interpreted as Celsius. |
| temp_mean | Temperature | SICdb | degC | 615 | 32.39 | 36.77 | 38.92 | 39.37 | MIMIC temperatures were harmonized to Celsius in the source extraction. SICdb temperatures are interpreted as Celsius. |
| temp_min | Minimum temperature | MIMIC-IV | degC | 6571 | 34.29 | 36.50 | 37.67 | 40.10 | MIMIC temperatures were harmonized to Celsius in the source extraction. SICdb temperatures are interpreted as Celsius. |
| temp_min | Minimum temperature | MIMIC-III | degC | 3994 | 33.83 | 36.17 | 37.83 | 39.00 | MIMIC temperatures were harmonized to Celsius in the source extraction. SICdb temperatures are interpreted as Celsius. |
| temp_min | Minimum temperature | SICdb | degC | 615 | 25.09 | 34.47 | 37.99 | 38.63 | MIMIC temperatures were harmonized to Celsius in the source extraction. SICdb temperatures are interpreted as Celsius. |
| temp_max | Maximum temperature | MIMIC-IV | degC | 6571 | 36.33 | 37.61 | 39.66 | 42.70 | MIMIC temperatures were harmonized to Celsius in the source extraction. SICdb temperatures are interpreted as Celsius. |
| temp_max | Maximum temperature | MIMIC-III | degC | 3994 | 36.11 | 37.78 | 40.00 | 40.80 | MIMIC temperatures were harmonized to Celsius in the source extraction. SICdb temperatures are interpreted as Celsius. |
| temp_max | Maximum temperature | SICdb | degC | 615 | 34.95 | 37.82 | 40.26 | 40.43 | MIMIC temperatures were harmonized to Celsius in the source extraction. SICdb temperatures are interpreted as Celsius. |
| platelet_min | Platelet count | MIMIC-IV | 10^9/L | 6812 | 18.00 | 156.00 | 542.00 | 1048.00 | 10^9/L and K/uL are numerically equivalent for platelet count. |
| platelet_min | Platelet count | MIMIC-III | 10^9/L | 4023 | 15.00 | 166.00 | 536.56 | 938.00 | 10^9/L and K/uL are numerically equivalent for platelet count. |
| platelet_min | Platelet count | SICdb | 10^9/L | 675 | 11.00 | 165.00 | 570.00 | 832.00 | 10^9/L and K/uL are numerically equivalent for platelet count. |
| hemoglobin_min | Hemoglobin | MIMIC-IV | g/dL | 6813 | 6.01 | 9.20 | 14.50 | 18.10 | Values are treated as g/dL. |
| hemoglobin_min | Hemoglobin | MIMIC-III | g/dL | 4025 | 6.40 | 9.50 | 14.30 | 17.70 | Values are treated as g/dL. |
| hemoglobin_min | Hemoglobin | SICdb | g/dL | 675 | 6.00 | 8.50 | 14.00 | 16.10 | Values are treated as g/dL. |
| map_mean | Mean arterial pressure | MIMIC-IV | mmHg | 6878 | 59.04 | 74.81 | 104.58 | 124.96 | Blood pressure values are treated as mmHg; MIMIC-III labels were filtered to avoid pulmonary-artery/cuff metadata fields. |
| map_mean | Mean arterial pressure | MIMIC-III | mmHg | 4013 | 55.50 | 74.80 | 106.35 | 217.65 | Blood pressure values are treated as mmHg; MIMIC-III labels were filtered to avoid pulmonary-artery/cuff metadata fields. |
| map_mean | Mean arterial pressure | SICdb | mmHg | 622 | 57.67 | 70.88 | 95.72 | 111.80 | Blood pressure values are treated as mmHg; MIMIC-III labels were filtered to avoid pulmonary-artery/cuff metadata fields. |
| sbp_mean | Systolic blood pressure | MIMIC-IV | mmHg | 6878 | 89.37 | 112.34 | 155.35 | 183.81 | Blood pressure values are treated as mmHg; MIMIC-III labels were filtered to avoid alarm and non-systemic fields. |
| sbp_mean | Systolic blood pressure | MIMIC-III | mmHg | 4014 | 85.31 | 113.55 | 158.55 | 179.15 | Blood pressure values are treated as mmHg; MIMIC-III labels were filtered to avoid alarm and non-systemic fields. |
| sbp_mean | Systolic blood pressure | SICdb | mmHg | 622 | 80.56 | 104.80 | 150.10 | 203.56 | Blood pressure values are treated as mmHg; MIMIC-III labels were filtered to avoid alarm and non-systemic fields. |
| urine_output_total | Cumulative urine output | MIMIC-IV | mL | 6792 | 124.55 | 1585.00 | 8976.42 | 16490.00 | Values are cumulative mL from S-AKI onset to landmark, not weight-normalized mL/kg/h. |
| urine_output_total | Cumulative urine output | MIMIC-III | mL | 3756 | 20.55 | 1520.50 | 7918.60 | 17420.00 | Values are cumulative mL from S-AKI onset to landmark, not weight-normalized mL/kg/h. |
| urine_output_total | Cumulative urine output | SICdb | mL | 603 | 30.00 | 1895.00 | 12269.20 | 18505.00 | Values are cumulative mL from S-AKI onset to landmark, not weight-normalized mL/kg/h. |

## Interpretation

- No locked predictor was missing from the MIMIC-IV, MIMIC-III, or SICdb modeling datasets.
- MIMIC-III temperature values were corrected at extraction: plausible Fahrenheit values were converted to Celsius before aggregation, plausible Celsius values were retained, and implausible temperature values were excluded from temperature summaries.
- SICdb BUN harmonization was corrected by converting Harnstoff (urea) to BUN using urea x 0.467 before validation.
- Platelet units were treated as numerically compatible across 10^9/L and K/uL conventions.
- Urine output is cumulative mL from S-AKI onset to landmark and is not weight-normalized; this should be stated in Methods and Table S4.
- SICdb remains exploratory because the sepsis definition and time-resolved KDIGO phenotype are less harmonized than the MIMIC cohorts.
