# External ROC-AUC Bootstrap Audit

## Method

The audit uses 10,000 class-stratified patient-level bootstrap replicates. Identical sampled patient indices are used for every configuration, so QSVC–SVM differences are paired. Percentile 95% confidence intervals are descriptive uncertainty intervals for this fixed BD-KDD cohort.

| configuration | auc | ci95_low | ci95_high | bootstrap_probability_auc_above_0_5 | random_discrimination_assessment |
|---|---|---|---|---|---|
| Frozen classical RBF SVM | 0.5106 | 0.4750 | 0.5456 | 0.7163 | INDISTINGUISHABLE FROM RANDOM |
| Frozen QSVC | 0.5254 | 0.4891 | 0.5606 | 0.9156 | INDISTINGUISHABLE FROM RANDOM |
| Frozen QSVC + diagnostic UCI p1/p99 clipping | 0.5255 | 0.4891 | 0.5606 | 0.9175 | INDISTINGUISHABLE FROM RANDOM |
| Post-hoc bounded MinMax QSVC | 0.4992 | 0.4638 | 0.5353 | 0.4820 | INDISTINGUISHABLE FROM RANDOM |
| Post-hoc bounded robust-tanh QSVC | 0.4989 | 0.4626 | 0.5351 | 0.4776 | INDISTINGUISHABLE FROM RANDOM |
| Post-hoc bounded quantile QSVC | 0.4996 | 0.4637 | 0.5353 | 0.4930 | INDISTINGUISHABLE FROM RANDOM |

## Paired frozen-model difference

- Point estimate, QSVC − SVM: **+0.0148**.
- 95% bootstrap CI: **[-0.0292, +0.0581]**.
- Bootstrap portion above zero: **75.2%**.
- The interval includes zero.

**Conclusion:** 0.525 and 0.511 are not presented as a quantum benefit. All tested configurations have intervals containing 0.5; no tested configuration demonstrated reliable better-than-random external discrimination.

[Bootstrap interval plot](figures/external_auc_bootstrap.png)
