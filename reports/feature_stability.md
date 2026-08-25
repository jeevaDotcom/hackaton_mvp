# Feature-selection stability

Based on 10 outer-training partitions. 7 method-budget combinations meet the predeclared descriptive stability rule. This is predictive stability, not clinical causality.

## Overall method/budget stability

| Method | Budget | Mean Jaccard | Jaccard SD | Features freq≥0.80 | Stable |
|---|---|---|---|---|---|
| mutual_information | 8 | 0.796 | 0.129 | 7 | True |
| mutual_information | 6 | 0.848 | 0.144 | 5 | True |
| mutual_information | 4 | 0.920 | 0.162 | 4 | True |
| permutation_importance | 8 | 0.507 | 0.189 | 3 | False |
| permutation_importance | 6 | 0.504 | 0.202 | 3 | False |
| permutation_importance | 4 | 0.640 | 0.237 | 3 | True |
| wrapper_rfe | 8 | 0.912 | 0.117 | 8 | True |
| wrapper_rfe | 6 | 0.848 | 0.144 | 5 | True |
| wrapper_rfe | 4 | 0.692 | 0.212 | 3 | True |

## Per-feature ranks and frequencies

| Method | Feature | Freq@8 | Freq@6 | Freq@4 | Mean rank | Rank SD |
|---|---|---|---|---|---|---|
| mutual_information | hemo | 1.000 | 1.000 | 1.000 | 1.00 | 0.00 |
| mutual_information | pcv | 1.000 | 1.000 | 1.000 | 2.10 | 0.32 |
| mutual_information | rc | 1.000 | 1.000 | 1.000 | 3.30 | 0.67 |
| mutual_information | sc | 1.000 | 1.000 | 0.900 | 3.70 | 0.67 |
| mutual_information | sg | 1.000 | 1.000 | 0.100 | 5.00 | 0.47 |
| mutual_information | al | 0.900 | 0.700 | 0.000 | 6.60 | 1.26 |
| mutual_information | htn | 0.700 | 0.100 | 0.000 | 7.90 | 1.73 |
| mutual_information | sod | 0.800 | 0.100 | 0.000 | 8.00 | 1.49 |
| mutual_information | dm | 0.400 | 0.100 | 0.000 | 8.30 | 1.25 |
| mutual_information | pot | 0.200 | 0.000 | 0.000 | 10.00 | 1.56 |
| mutual_information | bu | 0.000 | 0.000 | 0.000 | 10.60 | 0.70 |
| mutual_information | bgr | 0.000 | 0.000 | 0.000 | 12.50 | 0.85 |
| mutual_information | bp | 0.000 | 0.000 | 0.000 | 13.30 | 2.75 |
| mutual_information | appet | 0.000 | 0.000 | 0.000 | 15.70 | 2.54 |
| mutual_information | pe | 0.000 | 0.000 | 0.000 | 15.80 | 1.93 |
| mutual_information | wc | 0.000 | 0.000 | 0.000 | 15.90 | 2.13 |
| mutual_information | pc | 0.000 | 0.000 | 0.000 | 16.10 | 1.66 |
| mutual_information | age | 0.000 | 0.000 | 0.000 | 19.70 | 2.21 |
| mutual_information | ane | 0.000 | 0.000 | 0.000 | 19.70 | 2.83 |
| mutual_information | su | 0.000 | 0.000 | 0.000 | 19.80 | 3.22 |
| mutual_information | rbc | 0.000 | 0.000 | 0.000 | 20.20 | 2.39 |
| mutual_information | pcc | 0.000 | 0.000 | 0.000 | 21.30 | 2.50 |
| mutual_information | ba | 0.000 | 0.000 | 0.000 | 21.60 | 2.59 |
| mutual_information | cad | 0.000 | 0.000 | 0.000 | 21.90 | 2.13 |
| permutation_importance | sg | 1.000 | 1.000 | 1.000 | 1.30 | 0.48 |
| permutation_importance | hemo | 0.900 | 0.900 | 0.900 | 4.50 | 6.55 |
| permutation_importance | al | 0.900 | 0.900 | 0.900 | 5.20 | 5.94 |
| permutation_importance | age | 0.700 | 0.500 | 0.300 | 7.50 | 4.09 |
| permutation_importance | dm | 0.600 | 0.500 | 0.200 | 7.80 | 3.97 |
| permutation_importance | sc | 0.700 | 0.700 | 0.600 | 8.30 | 8.90 |
| permutation_importance | appet | 0.600 | 0.300 | 0.000 | 8.30 | 2.26 |
| permutation_importance | ane | 0.500 | 0.400 | 0.000 | 8.70 | 3.86 |
| permutation_importance | bgr | 0.500 | 0.200 | 0.000 | 9.50 | 4.03 |
| permutation_importance | ba | 0.400 | 0.000 | 0.000 | 10.50 | 3.54 |
| permutation_importance | htn | 0.500 | 0.400 | 0.100 | 10.50 | 5.34 |
| permutation_importance | bp | 0.100 | 0.000 | 0.000 | 11.20 | 2.49 |
| permutation_importance | bu | 0.000 | 0.000 | 0.000 | 12.40 | 3.50 |
| permutation_importance | pcv | 0.500 | 0.200 | 0.000 | 12.80 | 7.27 |
| permutation_importance | cad | 0.000 | 0.000 | 0.000 | 13.60 | 2.91 |
| permutation_importance | pc | 0.000 | 0.000 | 0.000 | 15.30 | 2.50 |
| permutation_importance | pcc | 0.000 | 0.000 | 0.000 | 16.30 | 2.50 |
| permutation_importance | rc | 0.100 | 0.000 | 0.000 | 17.20 | 5.47 |
| permutation_importance | pe | 0.000 | 0.000 | 0.000 | 17.60 | 2.41 |
| permutation_importance | pot | 0.000 | 0.000 | 0.000 | 17.70 | 2.67 |
| permutation_importance | sod | 0.000 | 0.000 | 0.000 | 18.90 | 4.82 |
| permutation_importance | rbc | 0.000 | 0.000 | 0.000 | 19.50 | 2.27 |
| permutation_importance | su | 0.000 | 0.000 | 0.000 | 22.20 | 1.93 |
| permutation_importance | wc | 0.000 | 0.000 | 0.000 | 23.20 | 1.93 |
| wrapper_rfe | hemo | 1.000 | 1.000 | 1.000 | 1.00 | 0.00 |
| wrapper_rfe | al | 1.000 | 1.000 | 0.900 | 2.90 | 1.20 |
| wrapper_rfe | dm | 1.000 | 1.000 | 0.900 | 3.40 | 1.17 |
| wrapper_rfe | sg | 1.000 | 1.000 | 0.700 | 3.80 | 1.03 |
| wrapper_rfe | pcv | 1.000 | 1.000 | 0.400 | 4.40 | 1.07 |
| wrapper_rfe | htn | 1.000 | 0.600 | 0.100 | 6.00 | 1.49 |
| wrapper_rfe | appet | 0.900 | 0.400 | 0.000 | 6.90 | 1.37 |
| wrapper_rfe | sc | 0.900 | 0.000 | 0.000 | 7.90 | 0.57 |
| wrapper_rfe | rc | 0.100 | 0.000 | 0.000 | 9.20 | 0.63 |
| wrapper_rfe | sod | 0.100 | 0.000 | 0.000 | 10.70 | 1.77 |
| wrapper_rfe | su | 0.000 | 0.000 | 0.000 | 11.10 | 1.52 |
| wrapper_rfe | bp | 0.000 | 0.000 | 0.000 | 12.40 | 1.78 |
| wrapper_rfe | pe | 0.000 | 0.000 | 0.000 | 12.40 | 0.97 |
| wrapper_rfe | bu | 0.000 | 0.000 | 0.000 | 14.20 | 1.40 |
| wrapper_rfe | pc | 0.000 | 0.000 | 0.000 | 14.70 | 2.41 |
| wrapper_rfe | bgr | 0.000 | 0.000 | 0.000 | 16.50 | 0.97 |
| wrapper_rfe | ane | 0.000 | 0.000 | 0.000 | 16.50 | 1.27 |
| wrapper_rfe | rbc | 0.000 | 0.000 | 0.000 | 17.70 | 1.06 |
| wrapper_rfe | wc | 0.000 | 0.000 | 0.000 | 18.60 | 1.51 |
| wrapper_rfe | pot | 0.000 | 0.000 | 0.000 | 20.40 | 1.35 |
| wrapper_rfe | age | 0.000 | 0.000 | 0.000 | 21.00 | 1.33 |
| wrapper_rfe | cad | 0.000 | 0.000 | 0.000 | 22.30 | 1.06 |
| wrapper_rfe | pcc | 0.000 | 0.000 | 0.000 | 22.70 | 0.95 |
| wrapper_rfe | ba | 0.000 | 0.000 | 0.000 | 23.30 | 0.67 |
