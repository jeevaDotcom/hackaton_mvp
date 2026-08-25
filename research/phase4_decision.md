# Phase 4 Decision

## 1. Final application name

**Q-CARE**

## 2. Final one-line positioning

**Evidence-First Hybrid Quantum Healthcare Benchmarking Platform.**

## 3. Final pages

1. Overview
2. CKD Benchmark Lab
3. Robustness & Shift Lab
4. Cross-Disease Validation
5. Quantum Evidence Explorer

## 4. Primary headline metric

QSVC achieved **0.985 sensitivity** in development-only stratified 5-fold cross-validation repeated 10 times on the eight-variable UCI CKD representation; matched RBF SVM sensitivity was **1.000**.

## 5. Most important negative result

On the BD-KDD cross-cohort stress test, RBF SVM ROC-AUC was **0.511 [0.475-0.546]** and QSVC ROC-AUC was **0.525 [0.489-0.561]**. Neither reliably exceeded chance, their difference was not distinguishable, and target comparability was **PARTIAL**.

## 6. Main quantum-positive result

QSVC remained internally competitive with the classical RBF SVM within the predefined **0.05 descriptive tolerance** at eight- and six-variable clinical budgets. This is a result about tested internal competitiveness, not superiority or clinical non-inferiority.

## 7. Main quantum-negative result

QSVC demonstrated no performance, runtime, robustness, small-sample, or generalisation advantage. It was approximately **464× slower at eight variables** and **477× slower at six**, and it was less robust than classical SVM under added missingness and measurement perturbation.

## 8. External transportability message

**Internal feature stability did not guarantee external feature transportability.** External transport failure reflected both target/cohort differences and changed feature–target relationships; therefore the experiment demonstrates transportability risk but cannot isolate pure conditional shift.

## 9. Final demo sequence

1. Overview
2. CKD comparison
3. Feature reduction
4. Runtime reveal
5. Robustness
6. External transportability failure
7. Final evidence verdict

## 10. Removed prototype claims

Removed: patient-specific screening, CKD risk percentages, “83% risk” outputs, diagnosis-like classifications, clinical recommendations, treatment/referral language, tests-saved and cost-saving claims, the 75% test-reduction claim, multi-disease patient risk cascades, illustrative metrics, a fabricated weighted quantum evidence score, implied entanglement, and incorrect dataset provenance.

## 11. Final supported claims

- Stable reduced CKD representations were identified.
- QSVC was internally competitive within the predefined tolerance at eight and six clinical variables.
- Classical SVM was slightly stronger on repeated resampling.
- Selected clinical variables were stronger than PCA for the tested QSVC.
- Classical SVM was more robust to missingness and input perturbation.
- QSVC showed no small-sample advantage.
- Both frozen models approached random discrimination on BD-KDD, where target comparability was only PARTIAL.
- Heart-disease method transfer was mixed; diabetes transfer was poor.
- Finite-shot stability was supported only in the tested local simulation.

## 12. Final prohibited claims

Quantum advantage, quantum acceleration, quantum superiority, clinical non-inferiority, CKD diagnosis, patient risk percentages, clinical sufficiency of six or eight tests, cost savings, clinical validation, medical-device readiness, and hardware readiness.

## 13. Total tests

**57 passing tests.**

## 14. App startup command

```bash
.venv/bin/streamlit run app.py
```

The final QA instance is available locally at `http://localhost:8502`.

## 15. GO / MODIFY / ABANDON for pitch preparation

**GO**, with the evidence-first research-platform framing frozen. The pitch must lead with transparent evaluation, the internal-to-external reversal, and the value of identifying negative quantum evidence. It must not resurrect screening, diagnosis, clinical, hardware-readiness, cost-saving, or quantum-advantage claims.
