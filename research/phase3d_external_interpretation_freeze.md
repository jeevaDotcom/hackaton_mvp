# Phase 3D — Final External-Interpretation Freeze

## Primary external finding

> External transport failure reflected both target/cohort differences and changed feature–target relationships; therefore the experiment demonstrates transportability risk but cannot isolate pure conditional shift.

## Secondary finding

> Internal feature stability did not guarantee external feature transportability.

## Statistical finding

> Neither the classical SVM nor QSVC demonstrated reliable better-than-random discrimination on BD-KDD, and their external AUC difference was not statistically distinguishable.

## Frozen evidence

| Evidence | Result |
|---|---|
| BD-KDD cohort | 988 total; 507 kidney disease; 481 healthy; 51.32% positive |
| UCI cohort | 400 total; 250 CKD; 150 non-CKD; 62.50% positive |
| Target comparability | PARTIAL |
| RBF SVM external AUC | 0.5106 [95% CI 0.4750-0.5456] |
| QSVC external AUC | 0.5254 [95% CI 0.4891-0.5606] |
| Paired QSVC-SVM difference | +0.0148 [95% CI -0.0292 to +0.0581] |
| Signed feature transport | All eight strong UCI associations flattened; every BD-KDD CI included 0.5 |
| Serum creatinine medians | UCI CKD/non-CKD 2.25/0.90 mg/dL; BD-KDD 7.71/7.10 mg/dL |

## Ruled-out dominant explanations

- Label inversion: not supported.
- Frozen-scaler overflow: not supported.
- Simple clipping repair: not supported.
- Post-hoc bounded encoding repair: not supported.
- Gross quantum-state collision/angle aliasing: not supported.

## Final claim boundary

BD-KDD is described as an independent cross-cohort transport stress test, not clean like-for-like clinical external validation. The 0.525 and 0.511 point estimates are never presented as a quantum benefit. No frozen model, metric, dataset, prediction, or experimental result changed in Phase 3D.

## Future-work boundary

The next scientific step is [transportability-aware study design](phase3d_future_work.md), not post-hoc tuning of the frozen experiment.
