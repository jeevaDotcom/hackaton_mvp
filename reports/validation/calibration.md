# Calibration review

Platt and isotonic calibration were evaluated with a leakage-safe nested structure: each outer-training partition was split into proper-training and calibration subsets, all preprocessing/model fitting used proper-training only, calibration used its held-out subset, and metrics used the untouched outer validation fold.

| model | method | brier / mean | brier / std | log_loss / mean | log_loss / std | ece_10_bin / mean | ece_10_bin / std |
|---|---|---|---|---|---|---|---|
| classical_rbf_svm | isotonic | 0.002 | 0.002 | 0.005 | 0.004 | 0.004 | 0.003 |
| classical_rbf_svm | platt | 0.007 | 0.003 | 0.057 | 0.011 | 0.053 | 0.009 |
| qsvc | isotonic | 0.016 | 0.011 | 0.172 | 0.136 | 0.018 | 0.011 |
| qsvc | platt | 0.015 | 0.008 | 0.084 | 0.025 | 0.063 | 0.009 |

The internally calibrated probabilities are not externally validated clinical risks. BD-KDD exposes substantial transport shift, and the sample size is inadequate for population-specific absolute-risk validation. The product contract therefore freezes **class label plus signed decision score**, not probability or a “risk percentage.” Calibration remains a research diagnostic only.
