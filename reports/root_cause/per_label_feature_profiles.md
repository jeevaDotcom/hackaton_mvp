# Per-Label Frozen-Feature Profiles

These descriptive profiles use the full 400-record UCI source cohort and all 988 BD-KDD records. They do not tune or evaluate a model.

## Numeric profiles

| dataset | label_name | feature | count | missing_count | mean | sd | min | p5 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| UCI full source cohort | non-CKD | hemo | 144 | 6 | 15.1882 | 1.2775 | 13.0000 | 13.3150 | 14.1000 | 15.0000 | 16.2000 | 17.3850 | 17.8000 |
| UCI full source cohort | non-CKD | al | 145 | 5 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| UCI full source cohort | non-CKD | sg | 145 | 5 | 1.0224 | 0.0025 | 1.0200 | 1.0200 | 1.0200 | 1.0200 | 1.0250 | 1.0250 | 1.0250 |
| UCI full source cohort | non-CKD | pcv | 146 | 4 | 46.3356 | 4.1344 | 40.0000 | 40.2500 | 43.0000 | 46.0000 | 50.0000 | 52.7500 | 54.0000 |
| UCI full source cohort | non-CKD | sc | 145 | 5 | 0.8690 | 0.2551 | 0.4000 | 0.5000 | 0.6000 | 0.9000 | 1.1000 | 1.2000 | 1.2000 |
| UCI full source cohort | CKD | hemo | 204 | 46 | 10.6475 | 2.1858 | 3.1000 | 6.6300 | 9.4750 | 10.9000 | 12.0250 | 14.0850 | 16.1000 |
| UCI full source cohort | CKD | al | 209 | 41 | 1.7225 | 1.3726 | 0.0000 | 0.0000 | 0.0000 | 2.0000 | 3.0000 | 4.0000 | 5.0000 |
| UCI full source cohort | CKD | sg | 208 | 42 | 1.0139 | 0.0046 | 1.0050 | 1.0100 | 1.0100 | 1.0150 | 1.0150 | 1.0232 | 1.0250 |
| UCI full source cohort | CKD | pcv | 183 | 67 | 32.9399 | 7.2089 | 9.0000 | 21.1000 | 28.5000 | 33.0000 | 37.0000 | 44.0000 | 52.0000 |
| UCI full source cohort | CKD | sc | 238 | 12 | 4.4149 | 6.9503 | 0.5000 | 0.8000 | 1.4250 | 2.2500 | 4.5500 | 13.5450 | 76.0000 |
| BD-KDD | non-CKD | hemo | 481 | 0 | 12.1046 | 2.9489 | 7.0000 | 7.4000 | 9.7000 | 12.1000 | 14.7000 | 16.6000 | 17.0000 |
| BD-KDD | non-CKD | al | 481 | 0 | 2.0353 | 1.4248 | 0.0000 | 0.0000 | 1.0000 | 2.0000 | 3.0000 | 4.0000 | 4.0000 |
| BD-KDD | non-CKD | sg | 481 | 0 | 1.0150 | 0.0071 | 1.0050 | 1.0050 | 1.0100 | 1.0150 | 1.0200 | 1.0250 | 1.0250 |
| BD-KDD | non-CKD | pcv | 481 | 0 | 37.2245 | 9.7815 | 20.0000 | 21.0000 | 29.0000 | 37.0000 | 46.0000 | 53.0000 | 54.0000 |
| BD-KDD | non-CKD | sc | 481 | 0 | 7.4113 | 4.1744 | 0.5000 | 1.1800 | 3.8100 | 7.1000 | 10.6900 | 14.1600 | 14.9600 |
| BD-KDD | CKD | hemo | 507 | 0 | 12.0533 | 2.7709 | 7.0000 | 7.4000 | 9.8500 | 12.1000 | 14.4000 | 16.3000 | 17.0000 |
| BD-KDD | CKD | al | 507 | 0 | 2.0256 | 1.4147 | 0.0000 | 0.0000 | 1.0000 | 2.0000 | 3.0000 | 4.0000 | 4.0000 |
| BD-KDD | CKD | sg | 507 | 0 | 1.0155 | 0.0072 | 1.0050 | 1.0050 | 1.0100 | 1.0150 | 1.0200 | 1.0250 | 1.0250 |
| BD-KDD | CKD | pcv | 507 | 0 | 36.2446 | 9.9562 | 20.0000 | 21.0000 | 28.0000 | 36.0000 | 45.0000 | 52.0000 | 54.0000 |
| BD-KDD | CKD | sc | 507 | 0 | 7.6533 | 4.1117 | 0.5100 | 1.1730 | 4.1650 | 7.7100 | 10.9600 | 14.1280 | 14.9800 |

## Categorical class-conditional proportions

| dataset | label_name | feature | category | count | missing_count | category_count | proportion |
|---|---|---|---|---|---|---|---|
| UCI full source cohort | non-CKD | dm | no | 148 | 2 | 148.0000 | 1.0000 |
| UCI full source cohort | non-CKD | dm | yes | 148 | 2 | 0.0000 | 0.0000 |
| UCI full source cohort | non-CKD | appet | good | 149 | 1 | 149.0000 | 1.0000 |
| UCI full source cohort | non-CKD | appet | poor | 149 | 1 | 0.0000 | 0.0000 |
| UCI full source cohort | non-CKD | htn | no | 148 | 2 | 148.0000 | 1.0000 |
| UCI full source cohort | non-CKD | htn | yes | 148 | 2 | 0.0000 | 0.0000 |
| UCI full source cohort | CKD | dm | no | 250 | 0 | 113.0000 | 0.4520 |
| UCI full source cohort | CKD | dm | yes | 250 | 0 | 137.0000 | 0.5480 |
| UCI full source cohort | CKD | appet | good | 250 | 0 | 168.0000 | 0.6720 |
| UCI full source cohort | CKD | appet | poor | 250 | 0 | 82.0000 | 0.3280 |
| UCI full source cohort | CKD | htn | no | 250 | 0 | 103.0000 | 0.4120 |
| UCI full source cohort | CKD | htn | yes | 250 | 0 | 147.0000 | 0.5880 |
| BD-KDD | non-CKD | dm | no | 481 | 0 | 246.0000 | 0.5114 |
| BD-KDD | non-CKD | dm | yes | 481 | 0 | 235.0000 | 0.4886 |
| BD-KDD | non-CKD | appet | good | 481 | 0 | 250.0000 | 0.5198 |
| BD-KDD | non-CKD | appet | poor | 481 | 0 | 231.0000 | 0.4802 |
| BD-KDD | non-CKD | htn | no | 481 | 0 | 229.0000 | 0.4761 |
| BD-KDD | non-CKD | htn | yes | 481 | 0 | 252.0000 | 0.5239 |
| BD-KDD | CKD | dm | no | 507 | 0 | 257.0000 | 0.5069 |
| BD-KDD | CKD | dm | yes | 507 | 0 | 250.0000 | 0.4931 |
| BD-KDD | CKD | appet | good | 507 | 0 | 248.0000 | 0.4892 |
| BD-KDD | CKD | appet | poor | 507 | 0 | 259.0000 | 0.5108 |
| BD-KDD | CKD | htn | no | 507 | 0 | 236.0000 | 0.4655 |
| BD-KDD | CKD | htn | yes | 507 | 0 | 271.0000 | 0.5345 |

## Serum-creatinine medians

| dataset | label_name | count | missing_count | median | p25 | p75 | min | max |
|---|---|---|---|---|---|---|---|---|
| UCI full source cohort | non-CKD | 145 | 5 | 0.9000 | 0.6000 | 1.1000 | 0.4000 | 1.2000 |
| UCI full source cohort | CKD | 238 | 12 | 2.2500 | 1.4250 | 4.5500 | 0.5000 | 76.0000 |
| BD-KDD | non-CKD | 481 | 0 | 7.1000 | 3.8100 | 10.6900 | 0.5000 | 14.9600 |
| BD-KDD | CKD | 507 | 0 | 7.7100 | 4.1650 | 10.9600 | 0.5100 | 14.9800 |
