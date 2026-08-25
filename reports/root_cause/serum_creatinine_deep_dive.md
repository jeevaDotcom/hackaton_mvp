# Serum Creatinine Deep Dive

## Per-label distribution

| dataset | label_name | count | missing_count | mean | sd | min | p5 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| UCI full source cohort | non-CKD | 145 | 5 | 0.8690 | 0.2551 | 0.4000 | 0.5000 | 0.6000 | 0.9000 | 1.1000 | 1.2000 | 1.2000 |
| UCI full source cohort | CKD | 238 | 12 | 4.4149 | 6.9503 | 0.5000 | 0.8000 | 1.4250 | 2.2500 | 4.5500 | 13.5450 | 76.0000 |
| BD-KDD | non-CKD | 481 | 0 | 7.4113 | 4.1744 | 0.5000 | 1.1800 | 3.8100 | 7.1000 | 10.6900 | 14.1600 | 14.9600 |
| BD-KDD | CKD | 507 | 0 | 7.6533 | 4.1117 | 0.5100 | 1.1730 | 4.1650 | 7.7100 | 10.9600 | 14.1280 | 14.9800 |

## Signed within-dataset AUC

Higher raw serum creatinine is the score orientation.

| dataset | n_observed | missing_count | auc | ci95_low | ci95_high | direction |
|---|---|---|---|---|---|---|
| UCI full source cohort | 383 | 17 | 0.9227 | 0.8952 | 0.9467 | positive (raw numeric; increasing value) |
| BD-KDD | 988 | 0 | 0.5182 | 0.4828 | 0.5550 | uncertain / includes random orientation |

## Distribution overlap and missingness

| dataset | histogram_overlap_coefficient | non_ckd_missing_pct | ckd_missing_pct |
|---|---|---|---|
| UCI full source cohort | 0.4160 | 3.3333 | 4.8000 |
| BD-KDD | 0.8097 | 0.0000 | 0.0000 |

UCI documents serum creatinine as `mgs/dl`; BD-KDD documents `mg/dL`, so unit confidence is high. No CKD stage is assigned: staging requires renal-function and chronicity evidence that cannot be derived from one creatinine value. The BD-KDD medians show that both labelled groups occupy a substantially higher and far more overlapping creatinine distribution than the UCI non-CKD/CKD contrast, consistent with a materially different renal-function cohort or label/cohort construction.

[Serum-creatinine distributions](figures/serum_creatinine_by_label.png)
