# Alternative Bounded Encoding — Post-Hoc Exploratory Analysis

## Scientific boundary

These models are experimental copies. Each preprocessing transform was fitted **only on UCI development data**, then a fresh QSVC was fitted there and evaluated once on BD-KDD. Nothing overwrites the frozen model or its external result. The interval `[−π/4, π/4]` was chosen because the installed feature-map phase is `2x`; it prevents more than a half-turn per feature inside the UCI-fitted range and avoids mapping binary endpoints to the same quantum state.

| condition | fit_scope | external_use | train_min | train_max | external_min | external_max | sensitivity | specificity | roc_auc | pr_auc | tn | fp | fn | tp | auc_change_vs_original_frozen |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MinMax clipped to [−π/4, π/4] | UCI development only | one post-hoc BD-KDD evaluation | -0.7854 | 0.7854 | -0.7854 | 0.7854 | 0.9862 | 0.0062 | 0.4992 | 0.5223 | 3 | 478 | 7 | 500 | -0.0262 |
| RobustScaler + tanh to (−π/4, π/4) | UCI development only | one post-hoc BD-KDD evaluation | -0.7815 | 0.7854 | -0.7815 | 0.7854 | 1.0000 | 0.0000 | 0.4989 | 0.5048 | 0 | 481 | 0 | 507 | -0.0264 |
| UCI quantile map to [−π/4, π/4] | UCI development only | one post-hoc BD-KDD evaluation | -0.7854 | 0.7854 | -0.7854 | 0.7854 | 1.0000 | 0.0000 | 0.4996 | 0.5076 | 0 | 481 | 0 | 507 | -0.0258 |

The best exploratory result was **UCI quantile map to [−π/4, π/4]**, ROC-AUC **0.500** (change -0.026 versus the original frozen QSVC).

Even an improvement would support only this wording: **Post-hoc analysis identified a potential transportability improvement.** It would not convert the original experiment into successful external validation.

[Bounded-encoding AUC plot](figures/bounded_encoding_auc.png)
