# Robustness results

## Repeated development reference experiment

The frozen clinical representations were compared on identical 5-fold × 10-repeat partitions. Preprocessing was refit within every training partition; the locked test was never accessed.

| Budget | Model | Sensitivity | 95% CI | Specificity | ROC-AUC | Mean fit s |
|---|---|---|---|---|---|---|
| 6 | classical_rbf_svm | 0.998 | 0.995–1.000 | 0.987 | 1.000 | 0.00 |
| 6 | qsvc | 0.977 | 0.970–0.983 | 0.978 | 0.995 | 0.32 |
| 8 | classical_rbf_svm | 1.000 | 1.000–1.000 | 1.000 | 1.000 | 0.00 |
| 8 | qsvc | 0.985 | 0.978–0.992 | 0.980 | 0.999 | 0.51 |

Paired QSVC-minus-classical results are in `artifacts/phase3/reference_cv_paired.csv`; intervals are bootstrap intervals over matched fold deltas and Wilcoxon values are descriptive, not multiplicity-adjusted confirmatory tests.

## Missingness stress

Additional missing cells were injected only after folds were fixed, independently into training and validation predictors, at 0%, 5%, 10%, and 20% with three seeds. Imputation was always learned from the corrupted training partition.

| model | missingness_fraction | sensitivity / mean | sensitivity / std | specificity / mean | specificity / std | roc_auc / mean | roc_auc / std |
|---|---|---|---|---|---|---|---|
| classical_rbf_svm | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 |
| classical_rbf_svm | 0.050 | 0.997 | 0.009 | 1.000 | 0.000 | 1.000 | 0.000 |
| classical_rbf_svm | 0.100 | 0.978 | 0.021 | 1.000 | 0.000 | 1.000 | 0.001 |
| classical_rbf_svm | 0.200 | 0.962 | 0.030 | 1.000 | 0.000 | 0.998 | 0.006 |
| qsvc | 0.000 | 0.985 | 0.021 | 0.975 | 0.035 | 1.000 | 0.001 |
| qsvc | 0.050 | 0.978 | 0.016 | 0.997 | 0.011 | 0.999 | 0.002 |
| qsvc | 0.100 | 0.962 | 0.030 | 0.975 | 0.031 | 0.993 | 0.008 |
| qsvc | 0.200 | 0.930 | 0.039 | 0.981 | 0.035 | 0.986 | 0.010 |

## Numeric perturbation

Gaussian perturbations used 1%, 5%, or 10% of each outer-training feature standard deviation for observed numeric values only. Categorical features were untouched. Models were fitted on clean training folds; this isolates inference-time measurement sensitivity.

| model | noise_sd_fraction | flip_rate / mean | flip_rate / std | sensitivity_delta / mean | sensitivity_delta / std | roc_auc_delta / mean | roc_auc_delta / std |
|---|---|---|---|---|---|---|---|
| classical_rbf_svm | 0.010 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| classical_rbf_svm | 0.050 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| classical_rbf_svm | 0.100 | 0.002 | 0.005 | -0.002 | 0.006 | 0.000 | 0.000 |
| qsvc | 0.010 | 0.001 | 0.004 | 0.002 | 0.006 | 0.000 | 0.000 |
| qsvc | 0.050 | 0.002 | 0.005 | 0.002 | 0.006 | -0.000 | 0.001 |
| qsvc | 0.100 | 0.009 | 0.010 | -0.002 | 0.011 | -0.000 | 0.001 |

## Prevalence shift

Development OOF predictions were resampled to 30%, 50%, and 70% prevalence (400 cases, 100 repetitions per setting). Sensitivity and specificity are comparatively stable under class-mixture resampling, while accuracy, precision and PR-AUC move with prevalence and therefore cannot be treated as transportable constants.

| model | prevalence | sensitivity | specificity | accuracy | precision | pr_auc |
|---|---|---|---|---|---|---|
| classical_rbf_svm | 0.300 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| classical_rbf_svm | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| classical_rbf_svm | 0.700 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| qsvc | 0.300 | 0.986 | 0.978 | 0.981 | 0.952 | 0.998 |
| qsvc | 0.500 | 0.984 | 0.980 | 0.982 | 0.980 | 0.999 |
| qsvc | 0.700 | 0.986 | 0.978 | 0.983 | 0.991 | 1.000 |

## Threshold trade-offs

Threshold curves were generated solely from repeated development OOF scores. They are exploratory operating-point evidence, not a deployed or clinically chosen threshold. The final frozen threshold remains the SVM decision boundary at 0.0.
