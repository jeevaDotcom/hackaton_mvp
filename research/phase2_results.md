# Phase 2 fair quantum benchmark results

All architecture choice, robustness analysis and PCA fitting used development data only. The fixed 0.05 margin is an experimental tolerance, not a formal clinical non-inferiority threshold. No quantum-advantage claim is made.

## Frozen model

QSVC used `FidelityQuantumKernel`, `z_reps1`, C=0.5, exact cached statevector fidelity for ideal development runs, and the Phase 1 preprocessing fitted within each training fold.

## Predefined feature-map screen on eight clinical variables

| Map | Qubits | Depth | Gates | Sensitivity | Specificity | ROC-AUC | F1 | Train s |
|---|---|---|---|---|---|---|---|---|
| zz_reps1 | 8 | 41 | 100 | 1.000 | 0.829 | 1.000 | 0.952 | 0.6484 |
| zz_reps2 | 8 | 67 | 200 | 1.000 | 0.079 | 0.959 | 0.784 | 1.0001 |
| z_reps1 | 8 | 2 | 16 | 0.983 | 0.979 | 0.999 | 0.985 | 0.3464 |

## Identical-fold classical versus frozen QSVC comparison

| Representation | Budget | Classical sens | QSVC sens | Δ sens | Classical spec | QSVC spec | Classical AUC | QSVC AUC | Δ AUC | Classical F1 | QSVC F1 | All primary deltas ≥−0.05 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| clinical | 8 | 1.000 | 0.983 | -0.017 | 1.000 | 0.979 | 1.000 | 0.999 | -0.001 | 1.000 | 0.985 | True |
| clinical | 6 | 1.000 | 0.975 | -0.025 | 0.983 | 0.975 | 1.000 | 0.994 | -0.006 | 0.995 | 0.980 | True |
| clinical | 4 | 0.960 | 0.895 | -0.065 | 0.950 | 0.887 | 0.978 | 0.950 | -0.027 | 0.965 | 0.912 | False |
| pca | 8 | 0.983 | 0.973 | -0.010 | 1.000 | 0.767 | 1.000 | 0.980 | -0.020 | 0.991 | 0.921 | False |
| pca | 6 | 0.988 | 0.938 | -0.050 | 0.996 | 0.821 | 1.000 | 0.963 | -0.037 | 0.992 | 0.917 | False |
| pca | 4 | 0.993 | 0.910 | -0.083 | 0.988 | 0.854 | 1.000 | 0.948 | -0.052 | 0.992 | 0.911 | False |

Paired fold-level bootstrap intervals and Wilcoxon tests are in `artifacts/quantum_paired_comparison_summary.csv`. P-values are descriptive because ten repeated-CV assessments are neither a large sample nor independent patient cohorts.

## Development-only training-size robustness

| Train fraction | Model | Train n | Sensitivity mean | Sensitivity SD | ROC-AUC mean | ROC-AUC SD | Train s |
|---|---|---|---|---|---|---|---|
| 25% | classical_rbf_svm | 64 | 1.000 | 0.000 | 1.000 | 0.000 | 0.0009 |
| 25% | qsvc | 64 | 0.933 | 0.014 | 0.994 | 0.005 | 0.0343 |
| 50% | classical_rbf_svm | 128 | 0.992 | 0.014 | 1.000 | 0.000 | 0.0006 |
| 50% | qsvc | 128 | 0.950 | 0.025 | 1.000 | 0.001 | 0.1337 |
| 75% | classical_rbf_svm | 192 | 1.000 | 0.000 | 1.000 | 0.000 | 0.0006 |
| 75% | qsvc | 192 | 0.942 | 0.029 | 0.999 | 0.001 | 0.2088 |
| 100% | classical_rbf_svm | 256 | 1.000 | 0.000 | 1.000 | 0.000 | 0.0007 |
| 100% | qsvc | 256 | 0.975 | 0.000 | 0.999 | 0.000 | 0.3696 |

## Finite-shot experiment (six clinical variables)

| Mode | Shots | Runs | Sensitivity | Sensitivity SD | Specificity | F1 | ROC-AUC | Train s |
|---|---|---|---|---|---|---|---|---|
| classical_reference | ideal | 1 | 1.000 | NR | 1.000 | 1.000 | 1.000 | 0.0015 |
| finite_shot_qsvc | 256 | 3 | 0.980 | 0.000 | 1.000 | 0.990 | 0.995 | 0.3737 |
| finite_shot_qsvc | 1024 | 3 | 0.980 | 0.000 | 1.000 | 0.990 | 0.994 | 0.3326 |
| finite_shot_qsvc | 4096 | 3 | 0.980 | 0.000 | 1.000 | 0.990 | 0.995 | 0.3221 |
| ideal_qsvc | ideal | 1 | 0.980 | NR | 1.000 | 0.990 | 0.995 | 0.2824 |

Finite-shot values use seeded binomial sampling of the exact compute-uncompute all-zero probability; a stock Qiskit path is checked in tests. This isolates shot noise without conflating it with gate noise.

## Aer noise experiment (six clinical variables)

| Condition | Shots | Sensitivity | Specificity | Accuracy | F1 | ROC-AUC | Δ sensitivity | Train s |
|---|---|---|---|---|---|---|---|---|
| ideal | 1024 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 2.217 |
| low | 1024 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 4.468 |
| moderate | 1024 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 4.627 |

Low and moderate conditions are synthetic device-inspired Aer models, not calibration snapshots from a named IBM device. They apply 1q/2q depolarizing and symmetric readout errors recorded in `artifacts/quantum_config.json`.

## Shared locked-test evaluation

The 80-patient holdout was already used for Phase 1 confirmation; it is not a pristine external validation cohort.

| Configuration | Model | Representation | Budget | Accuracy | Sensitivity | Specificity | F1 | ROC-AUC | Confusion |
|---|---|---|---|---|---|---|---|---|---|
| classical_6_clinical | classical_rbf_svm | clinical | 6 | 0.975 | 0.960 | 1.000 | 0.980 | 1.000 | TN=30, FP=0, FN=2, TP=48 |
| classical_6_pca | logistic_regression | pca | 6 | 0.938 | 0.920 | 0.967 | 0.948 | 0.997 | TN=29, FP=1, FN=4, TP=46 |
| classical_8_clinical | classical_rbf_svm | clinical | 8 | 0.988 | 0.980 | 1.000 | 0.990 | 1.000 | TN=30, FP=0, FN=1, TP=49 |
| qsvc_6_clinical | qsvc | clinical | 6 | 0.950 | 0.920 | 1.000 | 0.958 | 0.998 | TN=30, FP=0, FN=4, TP=46 |
| qsvc_6_pca | qsvc | pca | 6 | 0.863 | 0.880 | 0.833 | 0.889 | 0.939 | TN=25, FP=5, FN=6, TP=44 |
| qsvc_8_clinical | qsvc | clinical | 8 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | TN=30, FP=0, FN=0, TP=50 |

Bootstrap intervals (2,000 class-stratified resamples) are stored in the machine-readable evaluation artifact. No quantum configuration was changed after these results were observed.

## Interpretation

The comparison asks whether QSVC is competitive at equal dimension and what it costs. Near-ceiling classical performance leaves almost no room for a defensible predictive advantage claim. Kernel structure, runtime, finite-shot behavior and noise sensitivity therefore carry equal interpretive weight. This remains a small, single-site engineering benchmark rather than clinical validation.
