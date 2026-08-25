# Classical RBF Geometry Comparison

The frozen RBF kernel uses `gamma=0.17166666` on the same frozen scaled representation.

## Kernel geometry

| matrix | n | offdiag_mean | offdiag_median | offdiag_sd | offdiag_variance | offdiag_p5 | offdiag_p25 | offdiag_p75 | offdiag_p95 | within_class_mean | between_class_mean | within_minus_between | effective_rank | numerical_rank | condition_number_positive_spectrum | top_eigenvalue_fraction | centered_kernel_target_alignment |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RBF UCI development | 320 | 0.3195 | 0.2422 | 0.2712 | 0.0736 | 0.0077 | 0.0909 | 0.5003 | 0.8489 | 0.4347 | 0.1898 | 0.2449 | 5.6100 | 274 | 8468079132.9028 | 0.3745 | 0.7544 |
| RBF BD-KDD | 988 | 0.1639 | 0.1157 | 0.1506 | 0.0227 | 0.0119 | 0.0485 | 0.2369 | 0.4779 | 0.1639 | 0.1640 | -0.0001 | 19.7928 | 988 | 1042355.4756 | 0.1767 | 0.0053 |

## Decision-score geometry compared with QSVC

| model | cohort | ckd_median_score | non_ckd_median_score | score_overlap_coefficient | fraction_non_ckd_above_boundary | fraction_ckd_above_boundary | auc |
|---|---|---|---|---|---|---|---|
| Frozen RBF SVM | UCI development (training diagnostic) | 1.5478 | -1.1593 | 0.0000 | 0.0000 | 1.0000 | 1.0000 |
| Frozen RBF SVM | BD-KDD | 1.3467 | 1.3417 | 0.8780 | 0.9958 | 0.9862 | 0.5106 |
| Frozen QSVC | UCI development (training diagnostic) | 1.0003 | -1.2142 | 0.0100 | 0.0000 | 0.9900 | 1.0000 |
| Frozen QSVC | BD-KDD | 0.9219 | 0.9191 | 0.9278 | 0.9896 | 0.9921 | 0.5254 |

Both model families lose within-versus-between-class similarity separation and develop heavy class-score overlap on BD-KDD. This supports loss of usable feature-label geometry shared across kernels rather than a quantum-only mechanism.

The full RBF and QSVC eigenvalue spectra are in `kernel_eigenvalue_spectra.csv`.
