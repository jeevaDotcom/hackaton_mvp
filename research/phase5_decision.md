# Phase 5 Decision

## 1. Final product name

**Q-CARE — Evidence-First Hybrid Quantum Healthcare Benchmarking**

## 2. One-line pitch

**Q-CARE is an evidence-first hybrid quantum healthcare benchmark that tests quantum ML against a matched classical baseline—and reveals when runtime, robustness, or dataset shift breaks the result.**

## 3. 30-second pitch

“Biomedical models can look excellent on one benchmark and lose discrimination when the cohort changes. Q-CARE compares classical RBF SVM and quantum-kernel QSVC on identical features and folds, then tests robustness, runtime, and transportability. On CKD, QSVC reached 0.985 sensitivity internally, but exact statevector evaluation was about 464 times slower. On the BD-KDD stress test, both model AUC intervals included chance and target comparability was only partial.”

## 4. Main problem

Biomedical ML and QML are often judged on one internal score. That score does not establish robustness, generalisation, computational value, clinical reliability, or quantum utility.

## 5. Main innovation

An integrated, artifact-driven evidence method that applies identical information budgets and evaluation boundaries to classical and quantum models, then keeps performance, compute, robustness, transfer, and negative results visible together.

## 6. Hero dataset

UCI Chronic Kidney Disease: 400 records and 24 predictors, reported from Apollo Hospitals, Karaikudi, Tamil Nadu; reduced through leakage-free stability analysis to an eight-variable primary representation.

## 7. Hero positive result

Eight-variable QSVC reached sensitivity **0.985** and ROC-AUC **0.999** in development-only five-fold CV repeated ten times. Classical RBF SVM reached **1.000 / 1.000**. QSVC remained internally competitive within the predefined 0.05 descriptive tolerance.

## 8. Hero negative result

Exact local statevector QSVC was approximately **464× slower** at eight variables, degraded more under tested missingness and perturbation, and showed no small-sample advantage.

## 9. External-shift result

Frozen BD-KDD testing produced RBF SVM ROC-AUC **0.511 [0.475-0.546]** and QSVC ROC-AUC **0.525 [0.489-0.561]**. Neither reliably exceeded chance; the paired difference included zero, and target comparability was **PARTIAL**.

## 10. Main value proposition

Q-CARE gives biomedical and quantum-ML teams an auditable stop/go evidence layer before a benchmark result becomes an investment, deployment, or clinical claim.

## 11. Exact novelty

Leakage-free stable feature selection; identical classical/quantum information budgets; paired benchmarking; PCA controls; missingness, perturbation, and training-size tests; finite-shot and limited noise evaluation; runtime transparency; independent dataset shift; cross-disease validation; and explicit negative-evidence governance in one reproducible workflow.

## 12. Why quantum is included

Quantum was the hypothesis under test, not the assumed winner. Fidelity-kernel QSVC provides a concrete quantum representation whose predictive behaviour, resource cost, robustness, and transfer can be compared fairly with a structurally similar classical kernel.

## 13. Answer to the quantum-advantage objection

“We did not demonstrate quantum advantage, and we do not claim one. QSVC remained internally competitive at reduced CKD feature budgets, but classical SVM was slightly stronger, far faster, and more robust in the tested stresses. Neither model retained reliable discrimination in the BD-KDD cross-cohort stress test. Q-CARE’s contribution is the controlled evidence that separates a narrow competitive result from an advantageous or deployable one.”

## 14. Five-minute pitch

1. **0:00–0:30:** “99.9% ROC-AUC sounds excellent. But what happens when the hospital changes?”
2. **0:30–1:10:** one-score benchmark problem.
3. **1:10–1:45:** fold-safe data → matched models → stress/shift → verdict.
4. **1:45–2:30:** CKD `24 → 8`; QSVC `0.985/0.999`; classical `1.000/1.000`.
5. **2:30–3:00:** `464×` slower—competitiveness, not acceleration.
6. **3:00–3:50:** BD-KDD paired `0.511/0.525`, uncertainty, and PARTIAL comparability reveal.
7. **3:50–4:15:** Cleveland mixed; Pima not competitive.
8. **4:15–4:45:** integrated evidence novelty.
9. **4:45–5:00:** invest further—or stop.

Exact words and screens: `submission/five_minute_pitch.md`.

## 15. Two-minute demo

**Overview** hero → **CKD Benchmark** `24 → 8` and matched result → `464× slower` on the same section → **Robustness & Shift** external failure → **Quantum Evidence** final verdict. Do not open every chart.

## 16. 60-second fallback

Overview internal `1.000/0.999` → CKD `0.985 vs 1.000` plus `464×` → BD-KDD `0.511/0.525` with both CIs spanning chance → final no-advantage verdict. Offline version: `submission/demo_backup/demo_script_60sec.md`.

## 17. Top 10 judge questions

1. Where is the quantum advantage?
2. If classical ML is faster and slightly better, why use quantum at all?
3. Why only 400 CKD records?
4. Why is internal ROC-AUC almost perfect?
5. Why did cross-cohort transportability fail?
6. Why no entanglement?
7. Why did you reject VQC?
8. Can this run on real quantum hardware?
9. Is this actually an early disease-detection solution?
10. What exactly is novel?

Evidence-backed answers: `submission/judge_questions.md`.

## 18. Problem-statement coverage

Delivered: hybrid classical/quantum architecture; CKD, heart, diabetes, and BD-KDD cross-cohort data; leakage-free stable features plus PCA control; QSVC fidelity kernel; LR/RF/SVM/XGBoost baselines; sensitivity, specificity, F1, ROC-AUC and PR-AUC where applicable; method-level interpretability; measured computational efficiency; internal, stress, transportability, and cross-disease evidence. Near-term quantum compatibility is **PARTIAL** because only exact, finite-shot, and limited noise simulation were tested.

## 19. Repository readiness

Final UI and navigation are frozen; 14 screenshots are validated; the offline backup is complete; documentation matches the five actual page labels; claim and responsible-use controls are active; the demo is deterministic and requires no quantum or dataset network connection after installation.

## 20. Final test count

**63 tests passed in 5.10 seconds** in the final Phase 5 completion audit.

## 21. Remaining blockers

No repository or local-demo blocker. External operational items only: competition-specific team/form metadata, a public hosted URL if the rules require one, and a slide deck—which is explicitly outside this phase.

## 22. GO / MODIFY / ABANDON

**GO.** Freeze the evidence-first positioning and external-shift reveal. Modify only competition metadata, hosting, timing rehearsal, or a later authorised slide phase. Do not modify the UI, scientific results, claim registry, or responsible-use boundary.
