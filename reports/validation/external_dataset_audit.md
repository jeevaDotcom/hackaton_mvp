# External dataset audit

| Dataset | Country/population | Rows | Target definition | Feature overlap | Provenance/license | Permitted use |
|---|---|---|---|---|---|---|
| BD-KDD | Bangladesh | 988 | Physician/laboratory-assigned: 507 kidney disease / 481 healthy | 8/8 | CC0 1.0; DOI 10.7910/DVN/MB1LES | External transfer stress test |
| Cleveland | United States | 303 | UCI `num` 0 vs >0: 139 disease / 164 no disease | Disease-specific | UCI repository | Methodology validation |
| Pima diabetes | United States (Phoenix, Arizona) | 768 | Tested positive/negative: 268 / 500 | Disease-specific | OpenML mirror of UCI dataset | Methodology validation |

## BD-KDD compatibility decision

The public dataset has all eight frozen CKD variables under corresponding names and the dictionary specifies compatible units/codings. It was used without feature selection or external retraining: models trained on the 320-case UCI development partition were transferred to all 988 BD-KDD records. File hashes are frozen in the model manifest.

Compatibility is syntactic, not proof of cohort equivalence. BD-KDD contains no missing cells or duplicate rows, but class-conditional laboratory patterns are materially unlike UCI. For example, mean serum creatinine is {0: 7.411, 1: 7.653} by BD-KDD class, values that do not reproduce the source association. Its results are therefore reported as a stress test, not external confirmation or clinical validation.

Exact mapping: `Hemo→hemo`, `Al→al`, `Dm→dm`, `Sg→sg`, `Pcv→pcv`, `Appet→appet`, `Htn→htn`, `Sc→sc`, and `Class→target`. No unit conversion was applied because the BD-KDD dictionary reports the same units as UCI; binary codes were mapped using the dictionary. The source reports retrospective records from Popular Diagnostic Centre, Savar Branch, Dhaka, with physician/laboratory label assignment. These provenance statements are source-reported and were not independently audited.

| model | accuracy | sensitivity | specificity | precision | f1 | roc_auc | pr_auc | tn | fp | fn | tp | prediction_seconds |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| classical_rbf_svm | 0.508 | 0.986 | 0.004 | 0.511 | 0.673 | 0.511 | 0.518 | 2 | 479 | 7 | 500 | 0.002 |
| qsvc | 0.514 | 0.992 | 0.010 | 0.514 | 0.677 | 0.525 | 0.545 | 5 | 476 | 4 | 503 | 4.416 |

## Population wording

The diabetes dataset contains women of Pima heritage living near Phoenix, Arizona. It is explicitly **not an Indian-population dataset**. Zero values in plasma glucose, blood pressure, skinfold thickness, insulin and BMI were treated as missing-code sentinels inside folds.
