# Five-Minute Winning Narrative — Final UI

Target: **4:45 spoken + 0:15 contingency**. Do not begin with qubits.

## 0:00–0:30 — Hook

**Screen:** `screenshots/11_demo_hero.png` or **Overview**.

“99.9% ROC-AUC sounds excellent. But what happens when the hospital changes? In our experiment, internal RBF SVM and QSVC AUCs near 1.0 became 0.511 and 0.525 in a second kidney-disease cohort, with both external intervals including chance. That transportability test is why we built Q-CARE: the best benchmark score is often the beginning of the evidence, not the end.”

**Point at:** internal `1.000 / 0.999` → BD-KDD `0.511 / 0.525` and **PARTIAL** target comparability.

## 0:30–1:10 — Problem

**Screen:** Overview hero and four-measure strip.

“Healthcare ML and quantum-ML prototypes are often judged on one familiar benchmark. But accuracy alone cannot answer whether a model survives missing values, measurement variation, less training data, a new population, or the cost of running the quantum method. It also cannot tell us whether quantum added anything over a strong classical baseline. In healthcare, those missing questions are exactly where overconfident claims become dangerous. Q-CARE makes robustness, generalisation, computational cost, and quantum utility part of the result.”

## 1:10–1:45 — Q-CARE

**Screen:** `demo_backup/architecture_diagram.svg`.

“Q-CARE starts with provenance-checked biomedical data. Preprocessing and stable feature selection are learned only inside training partitions. Classical RBF SVM and quantum-kernel QSVC then receive identical feature budgets, folds, and regularisation. Their results pass through missingness, perturbation, training-size, finite-shot and noise tests, followed by a cross-cohort transport stress test and cross-disease validation. Only then does the platform show an evidence verdict. The dashboard does not retrain or invent numbers; it reads frozen artifacts through one validated results layer.”

## 1:45–2:30 — CKD hero experiment

**Screen:** **CKD Benchmark**, then `screenshots/04_classical_vs_quantum.png`.

“The hero dataset is UCI Chronic Kidney Disease: 400 records and 24 predictors. Leakage-free stability analysis produced an eight-variable primary representation. The classical branch used RBF SVM. The quantum branch used QSVC with a fidelity kernel and a deliberately simple `ZFeatureMap`: eight qubits, one repetition, logical depth two.

In development-only five-fold cross-validation repeated ten times, QSVC reached 0.985 sensitivity and 0.999 ROC-AUC. Classical SVM reached 1.000 sensitivity and 1.000 ROC-AUC. Under our predefined 0.05 experimental tolerance, QSVC remained internally competitive. That is a narrow benchmark conclusion—not clinical non-inferiority, superiority, or generalisation.”

## 2:30–3:00 — Quantum cost

**Screen:** `screenshots/04_classical_vs_quantum.png` or **Quantum Evidence → Runtime transparency**.

“Then we measured the cost. Exact local statevector QSVC was about 464 times slower at eight variables, and about 477 times slower at six. So our finding is competitiveness, not acceleration. This is simulator timing, not hardware timing, but it is the computation we actually paid—and Q-CARE keeps it beside the predictive result.”

## 3:00–3:50 — The reveal

**Screen:** `screenshots/06_external_shift.png` or **Robustness & Shift**.

“We then froze both models and moved to a second kidney-disease cohort. The result was not a quantum-specific collapse. Classical SVM fell to ROC-AUC 0.511 and QSVC to 0.525, and both confidence intervals included chance performance.

We investigated why. Labels were not inverted, scaling did not overflow, and the quantum kernel did not collapse through state collisions. Instead, all eight clinical features that were strongly discriminative in UCI flattened toward AUC 0.5 in BD-KDD.

Target comparability was also only partial. So the correct conclusion is not that quantum failed; it is that neither representation transported reliably across these cohorts.”

## 3:50–4:15 — Cross-disease methodology

**Screen:** `screenshots/07_cross_disease.png` or **Cross-Disease**.

“We repeated the methodology on Cleveland heart disease and Pima diabetes. Cleveland evidence was mixed: sensitivity and ROC-AUC were close, but specificity missed tolerance. On Pima diabetes, QSVC sensitivity fell to 0.043 and was not competitive. We keep the datasets separate rather than averaging them into a reassuring score. Quantum-model behaviour was dataset-dependent.”

## 4:15–4:45 — Novelty and value

**Screen:** `screenshots/08_quantum_evidence.png`.

“The novelty is not a new quantum algorithm. It is the integrated evidence method: leakage-free stable feature selection, identical classical and quantum information budgets, paired benchmarking, PCA controls, runtime transparency, missingness, perturbation, training size, finite shots, simulated noise, cross-cohort transportability, cross-disease validation, and explicit negative evidence. Q-CARE distinguishes internal feature stability from external feature transportability. Every claim remains attached to a frozen artifact instead of being compressed into a promotional score.”

## 4:45–5:00 — Close

**Screen:** `screenshots/10_responsible_ai.png` or **Quantum Evidence → Final evidence summary**.

“Q-CARE does not assume quantum is better. It produces the evidence needed to decide when quantum healthcare models deserve further investment—and when they do not.”

## Non-negotiable wording

- Say **internally competitive within a predefined descriptive tolerance**.
- Say **exact local statevector runtime**, never hardware runtime.
- Do not claim diagnosis, early detection, clinical validation, cost savings, hardware readiness, or quantum advantage.
- Do not describe BD-KDD as like-for-like clinical validation or isolate pure conditional shift.
