# Label Mapping Audit

## Decision

**PASS — no positive-class or target inversion bug was found.** CKD/kidney disease is canonical class `1`; non-CKD/healthy is class `0`. Both frozen estimators expose `classes_ = [0, 1]`, and positive decision scores map to `classes_[1] = 1`.

## Raw and cleaned targets

| Cohort | Raw target values | Cleaning rule | Clean counts |
|---|---|---|---|
| UCI CKD | `{"'ckd'": 246, "'ckd\\t'": 2, "''": 2, "'notckd'": 150}` | strip/lower; `ckd → 1`, `notckd → 0` | full dataset `{0: 150, 1: 250}`; development `{0: 120, 1: 200}` |
| BD-KDD | `{0: 481, 1: 507}` | integer identity; dictionary says `0 = healthy`, `1 = kidney disease` | `{0: 481, 1: 507}` |

## Metric and estimator ordering

- `binary_metrics` calls `confusion_matrix(..., labels=[0, 1])`, so the returned order is TN, FP, FN, TP.
- Sensitivity, precision, F1, ROC-AUC, and PR-AUC use class `1` as positive.
- SVM and QSVC both use `classes_ = [0, 1]`; `decision_function >= 0` predicts class `1`.
- Recomputed predictions match the frozen external prediction artifact exactly; maximum floating score differences are reported below.

| model | classes | decision_positive_class | prediction_match_pct | max_score_difference |
|---|---|---|---|---|
| classical_rbf_svm | [0, 1] | 1 | 100.0000 | 0.0000 |
| qsvc | [0, 1] | 1 | 100.0000 | 0.0000 |

## Deliberate inversion test

| model | current_label_auc | inverted_label_auc | one_minus_current |
|---|---|---|---|
| classical_rbf_svm | 0.5106 | 0.4894 | 0.4894 |
| qsvc | 0.5254 | 0.4746 | 0.4746 |

Inverted-label AUC equals `1 − current AUC` to numerical precision, as expected. This is a diagnostic identity, not evidence that the labels should be inverted.

## Manual confusion matrices

Rows below use actual class order `[0, 1]` and predicted class order `[0, 1]`.

| model | tn | fp | fn | tp |
|---|---|---|---|---|
| classical_rbf_svm | 2 | 479 | 7 | 500 |
| qsvc | 5 | 476 | 4 | 503 |

The extreme specificity is therefore real under the documented label convention: both models predict almost every BD-KDD record as CKD.

Two raw UCI lines end with an empty token because they contain a documented spurious delimiter. The strict loader repairs the 26-column structure before reading the target; both repaired targets are `ckd`. They are not missing or guessed labels.
