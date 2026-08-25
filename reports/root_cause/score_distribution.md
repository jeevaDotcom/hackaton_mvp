# Frozen Score-Distribution Diagnostic

## Class score separation

| model | cohort | ckd_score_median | non_ckd_score_median | overlap_coefficient | hedges_g_ckd_minus_non | ckd_above_boundary_pct | non_ckd_above_boundary_pct | all_above_boundary_pct | roc_auc |
|---|---|---|---|---|---|---|---|---|---|
| classical_rbf_svm | UCI development (training diagnostic) | 1.5478 | -1.1593 | 0.0000 | 8.2535 | 100.0000 | 0.0000 | 62.5000 | 1.0000 |
| classical_rbf_svm | BD-KDD external | 1.3467 | 1.3417 | 0.9044 | -0.0042 | 98.6193 | 99.5842 | 99.0891 | 0.5106 |
| qsvc | UCI development (training diagnostic) | 1.0003 | -1.2142 | 0.0100 | 9.3433 | 99.0000 | 0.0000 | 61.8750 | 1.0000 |
| qsvc | BD-KDD external | 0.9219 | 0.9191 | 0.9149 | 0.0968 | 99.2110 | 98.9605 | 99.0891 | 0.5254 |

The overlap coefficient is histogram overlap on `[0,1]`; lower is better separation. Hedges’ g is positive when CKD scores exceed non-CKD scores. The UCI values are training-set diagnostics for the frozen development-fitted model, not independent performance estimates.

## Classical RBF geometry

The frozen classical model uses `gamma=0.171667` and 40 support vectors.

| matrix | n | offdiag_mean | offdiag_std | near_one_pct | near_zero_pct | kernel_variance | within_class_mean | between_class_mean | within_minus_between | effective_rank | numerical_rank | top_eigenvalue_fraction |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RBF_within_UCI | 120 | 0.3843 | 0.2978 | 0.6863 | 6.4986 | 0.0887 | 0.5575 | 0.2140 | 0.3435 | 4.1189 | 104 | 0.4583 |
| RBF_within_BD-KDD | 160 | 0.1547 | 0.1469 | 0.0000 | 4.3396 | 0.0216 | 0.1537 | 0.1557 | -0.0020 | 19.4237 | 160 | 0.1702 |

### BD-KDD distance from frozen classical support vectors

| actual_class | n | min_distance_median | min_distance_p95 | median_distance_to_all_support_vectors |
|---|---|---|---|---|
| 0 | 481 | 2.4909 | 3.6959 | 3.4919 |
| 1 | 507 | 2.5592 | 3.7393 | 3.5058 |

## Mechanistic explanation

On BD-KDD, the non-CKD fraction above the decision boundary is the false-positive rate. Values near 99% directly explain specificity near 1%. Both frozen models shift nearly all external scores to the CKD side.

[Decision-score distributions](figures/decision_score_distributions.png)
