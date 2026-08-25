# Temporary Clipping Experiment — Diagnostic Only

The persisted QSVC and decision boundary were not retrained. Only BD-KDD transformed inputs were temporarily clipped before being passed to the frozen estimator.

| condition | changed_cell_pct | sensitivity | specificity | roc_auc | pr_auc | tn | fp | fn | tp | auc_change_vs_frozen |
|---|---|---|---|---|---|---|---|---|---|---|
| none (frozen external result) | 0.0000 | 0.9921 | 0.0104 | 0.5254 | 0.5446 | 5 | 476 | 4 | 503 | 0.0000 |
| UCI development min/max | 0.0000 | 0.9921 | 0.0104 | 0.5254 | 0.5446 | 5 | 476 | 4 | 503 | 0.0000 |
| UCI development p1/p99 | 0.2910 | 0.9921 | 0.0104 | 0.5255 | 0.5447 | 5 | 476 | 4 | 503 | 0.0002 |
| ±3 transformed SD | 0.0000 | 0.9921 | 0.0104 | 0.5254 | 0.5446 | 5 | 476 | 4 | 503 | 0.0000 |

The best clipping condition was **UCI development p1/p99**, with ROC-AUC **0.526** (change +0.000). The original frozen external result remains authoritative.

[Clipping AUC plot](figures/clipping_auc.png)
