# Performance Summary

| Cohort | Model | N rows | N stays | Event rate | AUROC (95% CI) | AUPRC (95% CI) | Brier (95% CI) | Calibration slope (95% CI) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MIMIC-IV internal test | xgboost_full | 1393 | 1026 | 46.8% | 0.770 (0.743-0.799) | 0.760 (0.726-0.795) | 0.192 (0.180-0.203) | 0.970 |
| MIMIC-IV internal test | xgboost_crossdb | 1393 | 1026 | 46.8% | 0.766 (0.738-0.792) | 0.754 (0.719-0.787) | 0.194 (0.181-0.205) | 0.944 |
| MIMIC-III external KDIGO-only | xgboost_full | 4175 | 3020 | 43.6% | 0.749 (0.732-0.765) | 0.683 (0.655-0.713) | 0.203 (0.196-0.211) | 0.791 |
| MIMIC-III external with CRRT | xgboost_full | 4062 | 2930 | 43.4% | 0.758 (0.740-0.775) | 0.696 (0.672-0.722) | 0.198 (0.192-0.206) | 0.851 |
| MIMIC-III external with CRRT | xgboost_crossdb | 4062 | 2930 | 43.4% | 0.761 (0.744-0.777) | 0.703 (0.678-0.727) | 0.197 (0.190-0.205) | 0.866 |
| SICdb sensitivity external | xgboost_crossdb | 685 | 347 | 18.7% | 0.587 (0.524-0.651) | 0.228 (0.179-0.303) | 0.355 (0.330-0.380) | 0.284 |
