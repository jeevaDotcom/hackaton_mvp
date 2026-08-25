# Within-Dataset Signed Univariate AUC

## Method

Numeric variables use their raw increasing value as the score. Binary variables use `dm=yes`, `appet=poor`, and `htn=yes` as score 1. ROC-AUC for a binary score is the Mann–Whitney discriminatory probability and is an appropriate binary-feature equivalent. Missing values are excluded feature-by-feature. Confidence intervals are class-stratified, patient-level percentile bootstrap intervals from 5,000 replicates.

Signed orientation is retained: values below 0.5 are not automatically flipped.

| dataset | feature | method | n_observed | missing_count | auc | ci95_low | ci95_high | direction | ci_includes_0_5 |
|---|---|---|---|---|---|---|---|---|---|
| UCI full source cohort | hemo | raw numeric; increasing value | 348 | 52 | 0.0312 | 0.0161 | 0.0487 | negative (raw numeric; increasing value) | False |
| UCI full source cohort | al | raw numeric; increasing value | 354 | 46 | 0.8708 | 0.8397 | 0.8995 | positive (raw numeric; increasing value) | False |
| UCI full source cohort | dm | binary indicator: yes=1 | 398 | 2 | 0.7740 | 0.7440 | 0.8060 | positive (binary indicator: yes=1) | False |
| UCI full source cohort | sg | raw numeric; increasing value | 353 | 47 | 0.0787 | 0.0538 | 0.1069 | negative (raw numeric; increasing value) | False |
| UCI full source cohort | pcv | raw numeric; increasing value | 329 | 71 | 0.0476 | 0.0266 | 0.0722 | negative (raw numeric; increasing value) | False |
| UCI full source cohort | appet | binary indicator: poor=1 | 399 | 1 | 0.6640 | 0.6340 | 0.6940 | positive (binary indicator: poor=1) | False |
| UCI full source cohort | htn | binary indicator: yes=1 | 398 | 2 | 0.7940 | 0.7620 | 0.8240 | positive (binary indicator: yes=1) | False |
| UCI full source cohort | sc | raw numeric; increasing value | 383 | 17 | 0.9227 | 0.8952 | 0.9467 | positive (raw numeric; increasing value) | False |
| BD-KDD | hemo | raw numeric; increasing value | 988 | 0 | 0.4944 | 0.4589 | 0.5307 | uncertain / includes random orientation | True |
| BD-KDD | al | raw numeric; increasing value | 988 | 0 | 0.4981 | 0.4633 | 0.5333 | uncertain / includes random orientation | True |
| BD-KDD | dm | binary indicator: yes=1 | 988 | 0 | 0.5023 | 0.4707 | 0.5341 | uncertain / includes random orientation | True |
| BD-KDD | sg | raw numeric; increasing value | 988 | 0 | 0.5171 | 0.4809 | 0.5515 | uncertain / includes random orientation | True |
| BD-KDD | pcv | raw numeric; increasing value | 988 | 0 | 0.4708 | 0.4354 | 0.5078 | uncertain / includes random orientation | True |
| BD-KDD | appet | binary indicator: poor=1 | 988 | 0 | 0.5153 | 0.4839 | 0.5461 | uncertain / includes random orientation | True |
| BD-KDD | htn | binary indicator: yes=1 | 988 | 0 | 0.5053 | 0.4744 | 0.5368 | uncertain / includes random orientation | True |
| BD-KDD | sc | raw numeric; increasing value | 988 | 0 | 0.5182 | 0.4828 | 0.5550 | uncertain / includes random orientation | True |

## UCI → BD-KDD direction classification

| feature | uci_auc | uci_ci95 | bd_auc | bd_ci95 | uci_direction | bd_direction | classification | interpretation |
|---|---|---|---|---|---|---|---|---|
| hemo | 0.0312 | [0.016, 0.049] | 0.4944 | [0.459, 0.531] | negative (raw numeric; increasing value) | uncertain / includes random orientation | FLATTENED | Strong UCI association is not distinguishable from random orientation in BD-KDD. |
| al | 0.8708 | [0.840, 0.900] | 0.4981 | [0.463, 0.533] | positive (raw numeric; increasing value) | uncertain / includes random orientation | FLATTENED | Strong UCI association is not distinguishable from random orientation in BD-KDD. |
| dm | 0.7740 | [0.744, 0.806] | 0.5023 | [0.471, 0.534] | positive (binary indicator: yes=1) | uncertain / includes random orientation | FLATTENED | Strong UCI association is not distinguishable from random orientation in BD-KDD. |
| sg | 0.0787 | [0.054, 0.107] | 0.5171 | [0.481, 0.551] | negative (raw numeric; increasing value) | uncertain / includes random orientation | FLATTENED | Strong UCI association is not distinguishable from random orientation in BD-KDD. |
| pcv | 0.0476 | [0.027, 0.072] | 0.4708 | [0.435, 0.508] | negative (raw numeric; increasing value) | uncertain / includes random orientation | FLATTENED | Strong UCI association is not distinguishable from random orientation in BD-KDD. |
| appet | 0.6640 | [0.634, 0.694] | 0.5153 | [0.484, 0.546] | positive (binary indicator: poor=1) | uncertain / includes random orientation | FLATTENED | Strong UCI association is not distinguishable from random orientation in BD-KDD. |
| htn | 0.7940 | [0.762, 0.824] | 0.5053 | [0.474, 0.537] | positive (binary indicator: yes=1) | uncertain / includes random orientation | FLATTENED | Strong UCI association is not distinguishable from random orientation in BD-KDD. |
| sc | 0.9227 | [0.895, 0.947] | 0.5182 | [0.483, 0.555] | positive (raw numeric; increasing value) | uncertain / includes random orientation | FLATTENED | Strong UCI association is not distinguishable from random orientation in BD-KDD. |

## Monotonicity note

ROC-AUC depends only on ranking. A strictly increasing transformation—including positive-factor unit conversion, standardisation, min-max scaling, or another strictly monotonic map—preserves ranking and therefore preserves ROC-AUC. A strictly decreasing transformation reverses orientation, producing `1 − AUC` apart from ties. Non-monotonic transformations can change ranking. Consequently, a near-random within-BD-KDD univariate AUC cannot be rescued by ordinary positive unit conversion or scaling; it indicates absent/flattened ranking signal under that feature orientation, subject to its bootstrap uncertainty.

[Signed-AUC plot](figures/univariate_auc_signed.png)
