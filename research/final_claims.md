# Final claims

## Supported claims

- A classical RBF SVM and frozen QSVC were reproducibly compared at identical 8- and 6-feature budgets on UCI CKD (`artifacts/phase3/reference_cv_summary.csv`, 5×10 CV).
- The eight-variable QSVC remained within the predeclared 0.05 descriptive tolerance internally, but paired mean deltas favoured SVM (`artifacts/phase3/reference_cv_paired.csv`).
- Missingness, perturbation, prevalence, threshold, and calibration sensitivity were quantified without accessing the locked test (`reports/validation/robustness_results.md`).
- The leakage-controlled comparison method ran on Cleveland and Pima with disease-specific preprocessing (`reports/validation/cross_disease_validation.md`).
- The BD-KDD cross-cohort stress test showed that nominal 8/8 feature compatibility did not yield reliable discrimination for either model; target comparability was PARTIAL (`reports/root_cause/external_auc_bootstrap.md`; `reports/root_cause/target_definition_audit.md`).
- Internal feature stability did not guarantee external feature transportability in this tested UCI-to-BD-KDD setting (`reports/root_cause/univariate_auc.md`).

## Conditionally supported claims

- “Feature-efficient” is permitted only as a dimensionality/benchmark description; six or eight tests are not sufficient to diagnose disease.
- “QSVC competitive on internal UCI CKD resampling” is permitted only with the matched classical metrics, uncertainty, runtime disadvantage, and no non-inferiority wording.
- “Methodology generalises” means the experimental pipeline executes across disease-specific datasets; it does not mean one model or QSVC performance generalises.

## Unsupported claims

- Quantum advantage, speed advantage, clinical superiority, demonstrated cross-cohort transportability, or calibrated clinical risk.
- Any statement that internal or locked-test metrics generalise to a hospital, geography, demographic group, instrument, protocol, or future period.
- Any statement that Pima represents an Indian population.

## Prohibited claims

- “Quantum outperforms classical ML,” “quantum is faster,” or “clinical non-inferiority.”
- “Six/eight tests are enough to diagnose CKD,” “75% cost reduction,” or equivalent cost claims.
- “Hardware-ready,” “clinically validated,” “production-ready medical device,” “confirmed disease,” treatment advice, or clinical recommendation.
- Any fabricated percentage such as “83% CKD risk.”

## Required public wording

“Research benchmark only. Outputs are model class labels and relative decision scores, not diagnoses or clinical risk probabilities. Neither frozen model demonstrated reliable better-than-random discrimination on the BD-KDD cross-cohort stress test; target comparability was partial, and no classical-versus-quantum difference was established.”
