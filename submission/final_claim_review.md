# Final Claim Review

Wording is allowed only in the scope shown. “Pitch” means spoken or slide copy when slides are authorised later.

| Claim | Evidence | Allowed? | Use in pitch? | Use in README? | Use in dashboard? |
|---|---|---:|---:|---:|---:|
| “QSVC was internally competitive at eight and six clinical variables within the predefined 0.05 descriptive tolerance.” | `artifacts/phase3/reference_cv_summary.csv`; tolerance implementation | YES, with all qualifiers | YES | YES | YES |
| “Quantum competitive.” | Same evidence, but scope is missing | ONLY if rewritten with dataset, internal-validation, budget, and tolerance qualifiers | NO as written | NO as written | NO as written |
| “QSVC achieved 0.985 sensitivity in repeated internal CKD cross-validation.” | `artifacts/phase3/reference_cv_summary.csv` | YES | YES | YES | YES |
| “Classical SVM achieved 1.000 sensitivity in the matched repeated CKD reference.” | `artifacts/phase3/reference_cv_summary.csv` | YES | YES | YES | YES |
| “Q-CARE is feature efficient.” | Feature count alone does not establish operational efficiency or clinical sufficiency | NO | NO | NO | NO |
| “QSVC remained competitive at reduced feature budgets.” | Matched eight- and six-variable comparisons | YES, internal/tested scope only | YES | YES | YES |
| “Eight variables mean eight clinical tests.” | Not measured; variables do not map one-to-one to tests | NO | NO | NO | NO |
| “Classical SVM was more robust to tested missingness and perturbation.” | `artifacts/phase3/missingness.csv`; `artifacts/phase3/perturbation.csv` | YES | YES | YES | YES |
| “QSVC is robust.” | Robustness dimensions were mixed/negative; no external advantage | NO | NO | NO | NO |
| “Finite-shot stability was supported in the tested local simulation.” | `artifacts/quantum_finite_shot_results.csv` | YES, exact scope only | Optional | YES | YES |
| “QSVC generalises.” | BD-KDD QSVC AUC 0.525 [0.489-0.561]; target comparability PARTIAL | NO | NO | NO | NO |
| “External transport failure reflected both target/cohort differences and changed feature–target relationships.” | Phase 3C target, univariate, and bootstrap audits | YES | YES | YES | YES |
| “Neither frozen model demonstrated reliable better-than-random discrimination on BD-KDD.” | RBF 0.511 [0.475-0.546]; QSVC 0.525 [0.489-0.561] | YES | YES | YES | YES |
| “QSVC outperformed SVM externally.” | Paired delta +0.0148 [-0.0292, +0.0581] | NO | NO | NO | NO |
| “Q-CARE enables early detection.” | No prospective early-detection study | NO | NO | NO | NO |
| “Q-CARE is an Indian healthcare solution.” | Primary UCI source is reported from Tamil Nadu; other datasets have different provenance; no health-system evaluation | NO | NO | NO | NO |
| “The primary CKD dataset was reported from Apollo Hospitals, Karaikudi, Tamil Nadu.” | UCI provenance metadata | YES | Optional | YES | YES |
| “Q-CARE is a quantum healthcare benchmarking platform.” | Accurate research-domain positioning | YES, keep “benchmarking” | YES | YES | YES |
| “Q-CARE is a quantum-powered healthcare product.” | Implies clinical capability and promotional superiority | NO | NO | NO | NO |
| “QSVC was approximately 464× and 477× slower at eight and six variables in exact local statevector evaluation.” | `artifacts/quantum_paired_comparison_summary.csv` | YES | YES | YES | YES |
| “Quantum acceleration” or “quantum speed-up.” | Opposite of measured simulator runtime; no hardware test | NO | NO | NO | NO |
| “Near-term hardware ready” or “hardware-ready.” | No real hardware evaluation | NO | NO | NO | NO |
| “The circuit is Qiskit-compatible.” | Qiskit-built frozen `ZFeatureMap` | YES | Optional | YES | YES |
| “No entanglement was needed.” | Overgeneralises one limited architecture search | NO | NO | NO | NO |
| “The selected low-depth map had no entanglement and gave the best evidence among tested configurations.” | `artifacts/quantum_config.json`; Phase 2 selection | YES | YES if asked | YES | YES |
| “Q-CARE is clinically validated / clinically non-inferior.” | No clinical or prospective validation | NO | NO | NO | NO |
| “Q-CARE can diagnose CKD or estimate patient risk.” | Not evaluated or exposed | NO | NO | NO | NO |
| “Q-CARE saves costs or reduces tests by 75%.” | No workflow or economic evaluation | NO | NO | NO | NO |
| “Q-CARE demonstrates quantum advantage/superiority.” | Predictive, runtime, robustness, and transfer evidence do not support it | NO | NO | NO | NO |

## Frozen pitch rule

Use “competitive” only with **internal**, **tested feature budget**, and **predefined descriptive tolerance**. Always place runtime and the shared cross-cohort transportability finding in the same narrative.
