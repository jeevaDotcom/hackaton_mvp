# Feature-by-Feature Quantum-Kernel Ablation — Diagnostic Only

## Boundary

These are disposable precomputed-kernel SVC fits using the exact analytical fidelity of the frozen `ZFeatureMap`. They do **not** alter or replace the frozen QSVC. The eight-feature diagnostic replay reproduces the frozen kernel definition before leave-one-feature-out geometry is inspected.

| removed_feature | dimensions | external_auc | sensitivity | specificity | kernel_target_alignment_uci | external_geometry_auc | same_minus_different_similarity | auc_change_vs_8_feature_diagnostic |
|---|---|---|---|---|---|---|---|---|
| none (8-feature diagnostic replay) | 8 | 0.5254 | 0.9921 | 0.0104 | 0.4889 | 0.5118 | 0.0004 | 0.0000 |
| hemo | 7 | 0.5123 | 0.9901 | 0.0166 | 0.5377 | 0.5062 | 0.0006 | -0.0131 |
| al | 7 | 0.5212 | 0.9763 | 0.0291 | 0.4562 | 0.5111 | 0.0001 | -0.0042 |
| dm | 7 | 0.5191 | 0.9744 | 0.0270 | 0.4676 | 0.5107 | -0.0003 | -0.0063 |
| sg | 7 | 0.5283 | 0.9882 | 0.0083 | 0.5345 | 0.5070 | 0.0005 | 0.0030 |
| pcv | 7 | 0.5199 | 0.9921 | 0.0166 | 0.5743 | 0.5003 | 0.0006 | -0.0055 |
| appet | 7 | 0.5232 | 0.9783 | 0.0270 | 0.4736 | 0.5099 | 0.0006 | -0.0022 |
| htn | 7 | 0.5228 | 0.9783 | 0.0249 | 0.4724 | 0.5060 | 0.0007 | -0.0026 |
| sc | 7 | 0.5191 | 0.9744 | 0.0395 | 0.4779 | 0.5126 | 0.0000 | -0.0063 |

The largest external AUC after removal was **0.528** when removing **sg** (change +0.003). This is a mechanism probe, not feature selection or a new final model.

[Ablation AUC plot](figures/ablation_auc.png)
