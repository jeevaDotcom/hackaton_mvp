# Shift profile for the frozen CKD signature

This is descriptive characterization, not evidence of causality. UCI full-data summaries describe the source cohort; all model-selection and robustness estimates remain development-only. Missing values are handled by training-partition-fitted imputers.

| Feature | Source missing | Descriptive target relationship | Observed extent | Acquisition | External shift signal |
|---|---|---|---|---|---|
| hemo | 13.0% | median no-CKD 15.000; CKD 10.900 | range 3.100–17.800 | blood test | UCI mean 12.526; BD-KDD mean 12.078 |
| al | 11.5% | median no-CKD 0.000; CKD 2.000 | range 0.000–5.000 | urine test | UCI mean 1.017; BD-KDD mean 2.030 |
| dm | 0.5% | no: CKD rate 0.433; yes: CKD rate 1.000; nan: CKD rate 0.000 | categorical | history/diagnosis | UCI mode no; BD-KDD mode no |
| sg | 11.8% | median no-CKD 1.020; CKD 1.015 | range 1.005–1.025 | urine test | UCI mean 1.017; BD-KDD mean 1.015 |
| pcv | 17.8% | median no-CKD 46.000; CKD 33.000 | range 9.000–54.000 | blood test | UCI mean 38.884; BD-KDD mean 36.722 |
| appet | 0.2% | good: CKD rate 0.530; poor: CKD rate 1.000; nan: CKD rate 0.000 | categorical | subjective history | UCI mode good; BD-KDD mode good |
| htn | 0.5% | no: CKD rate 0.410; yes: CKD rate 1.000; nan: CKD rate 0.000 | categorical | history/diagnosis | UCI mode no; BD-KDD mode yes |
| sc | 4.2% | median no-CKD 0.900; CKD 2.250 | range 0.400–76.000 | blood test | UCI mean 3.072; BD-KDD mean 7.536 |

## Numeric Spearman correlation

| index | hemo | al | sg | pcv | sc |
|---|---|---|---|---|---|
| hemo | 1.000 | -0.680 | 0.630 | 0.870 | -0.730 |
| al | -0.680 | 1.000 | -0.520 | -0.660 | 0.640 |
| sg | 0.630 | -0.520 | 1.000 | 0.630 | -0.560 |
| pcv | 0.870 | -0.660 | 0.630 | 1.000 | -0.720 |
| sc | -0.730 | 0.640 | -0.560 | -0.720 | 1.000 |

## Interpretation

The signature mixes laboratory measurements, recorded diagnoses, and one subjective symptom. The most operationally brittle inputs are specific gravity/albumin (urine collection and assay), hematology/creatinine (laboratory method and units), and appetite (subjective coding). Hospital coding practices can shift `dm`, `htn`, and `appet`; instruments, specimen handling, units, and reference ranges can shift the five measured variables. Demographic transport cannot be established because the source is small and the frozen signature contains no demographic covariate or adequately powered subgroup analysis. BD-KDD has compatible names and nominal units, but its class-conditional values—especially serum creatinine—differ sharply from the UCI relationships. That makes it a valuable transfer stress test and prevents calling it clean external confirmation.
