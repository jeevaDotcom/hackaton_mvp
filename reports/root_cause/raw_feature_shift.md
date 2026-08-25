# Raw Frozen-Feature Shift

## Decision

All eight inputs shift materially in at least one marginal property. The largest PSI is **sc (1.912)**. PSI is a descriptive bin-based shift indicator, not a hypothesis test or universal severity scale.

## Numeric features

| feature | uci_median | bd_median | uci_mean | bd_mean | uci_missing_pct | bd_missing_pct | ks_statistic | wasserstein | psi |
|---|---|---|---|---|---|---|---|---|---|
| hemo | 12.6000 | 12.1000 | 12.5004 | 12.0782 | 12.1875 | 0.0000 | 0.0792 | 0.5066 | 0.0623 |
| al | 0.0000 | 2.0000 | 1.0596 | 2.0304 | 10.9375 | 0.0000 | 0.3454 | 0.9777 | 0.5535 |
| sg | 1.0200 | 1.0150 | 1.0174 | 1.0153 | 11.5625 | 0.0000 | 0.1701 | 0.0022 | 0.4071 |
| pcv | 40.0000 | 37.0000 | 38.5338 | 36.7217 | 16.8750 | 0.0000 | 0.1215 | 2.2514 | 0.1540 |
| sc | 1.3000 | 7.5200 | 3.0093 | 7.5355 | 4.6875 | 0.0000 | 0.5950 | 5.1388 | 1.9125 |

The CSV contains min, p1, p5, median, p95, p99, max, mean, standard deviation, missingness, KS statistic, Wasserstein distance, and PSI for every numeric frozen feature.

## Categorical prevalence

| feature | risk_category | uci_prevalence | bd_prevalence | difference_pp | uci_missing_pct | bd_missing_pct |
|---|---|---|---|---|---|---|
| dm | yes | 0.3500 | 0.4909 | 14.0891 | 0.6250 | 0.0000 |
| appet | poor | 0.2156 | 0.4960 | 28.0326 | 0.3125 | 0.0000 |
| htn | yes | 0.3688 | 0.5294 | 16.0602 | 0.6250 | 0.0000 |

## Class-conditional relationship transport

Each feature's risk direction is fixed from UCI development, then applied unchanged to BD-KDD. This is descriptive association transport, not feature selection.

| feature | uci_risk_direction | uci_directed_auc | bd_auc_using_uci_direction | uci_non_ckd_mean | uci_ckd_mean | bd_non_ckd_mean | bd_ckd_mean | uci_ckd_minus_non_mean | bd_ckd_minus_non_mean | directed_auc_loss |
|---|---|---|---|---|---|---|---|---|---|---|
| hemo | lower | 0.9746 | 0.5056 | 15.1442 | 10.9335 | 12.1046 | 12.0533 | -4.2107 | -0.0513 | -0.4690 |
| al | higher | 0.8200 | 0.4981 | 0.0000 | 1.5100 | 2.0353 | 2.0256 | 1.5100 | -0.0097 | -0.3219 |
| sg | lower | 0.8898 | 0.4829 | 1.0224 | 1.0149 | 1.0150 | 1.0155 | -0.0075 | 0.0004 | -0.4068 |
| pcv | lower | 0.9583 | 0.5292 | 45.8583 | 34.5350 | 37.2245 | 36.2446 | -11.3233 | -0.9800 | -0.4291 |
| sc | higher | 0.9194 | 0.5182 | 0.9008 | 4.1463 | 7.4113 | 7.6533 | 3.2454 | 0.2420 | -0.4011 |
| dm | yes | 0.7800 | 0.5023 | 0.0000 | 0.5600 | 0.4886 | 0.4931 | 0.5600 | 0.0045 | -0.2777 |
| appet | poor | 0.6725 | 0.5153 | 0.0000 | 0.3450 | 0.4802 | 0.5108 | 0.3450 | 0.0306 | -0.1572 |
| htn | yes | 0.7950 | 0.5053 | 0.0000 | 0.5900 | 0.5239 | 0.5345 | 0.5900 | 0.0106 | -0.2897 |

The UCI-directed single-feature AUCs collapse toward 0.5 in BD-KDD. This loss of class-conditional structure is more mechanistically important than marginal shift alone and is consistent with both frozen models losing discrimination.

## Plots

- [Numeric overlays](figures/raw_numeric_overlays.png)
- [Categorical prevalence](figures/raw_categorical_prevalence.png)
- [Class-conditional AUC transport](figures/class_conditional_auc_transport.png)

P-values are intentionally omitted: with 988 external records they would not measure practical transportability, and marginal tests do not establish a causal mechanism.
