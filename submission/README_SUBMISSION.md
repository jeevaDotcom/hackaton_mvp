# Q-CARE — Submission Summary

**Evidence-First Hybrid Quantum Healthcare Benchmarking Platform**

> **Q-CARE is an evidence-first hybrid quantum healthcare benchmark that tests quantum ML against a matched classical baseline—and reveals when runtime, robustness, or cross-cohort transportability breaks the result.**

Final spoken copy is in `final_pitch.md`; the post-redesign visual route is in `screenshot_pitch_mapping.md`.

## 1. Problem

Excellent biomedical benchmark scores do not guarantee robustness, generalisation, clinical reliability, or useful quantum computation. Quantum-ML demonstrations can also hide unfair feature budgets and simulator cost. A decision needs the complete evidence, not only the highest internal metric.

## 2. Q-CARE

Q-CARE is a reproducible platform that tests where quantum machine learning remains competitive with classical ML on biomedical datasets—and exposes where performance breaks under feature reduction, missingness, measurement perturbation, computational cost, and cross-cohort transport.

It is a research benchmark, not a clinical screening product.

## 3. What we built

- Provenance-aware biomedical ingestion and deterministic cleaning.
- Fold-safe stable feature selection.
- Matched RBF SVM and fidelity-kernel QSVC experiments.
- Full, eight-, six-, and four-variable budget evaluation plus PCA controls.
- Missingness, perturbation, training-size, finite-shot, and simulated-noise tests.
- BD-KDD cross-cohort transportability audit and cross-disease methodology validation.
- Single-page Streamlit clinical research workstation integrating the five frozen evidence areas, live VQC assessment, CSV data-health checks, and report download.
- Frozen artifact manifest, claim registry, responsible-use controls, and automated tests.

## 4. Architecture

```text
Biomedical datasets
        ↓
Data quality + fold-safe preprocessing
        ↓
Stable feature selection
        ↓
Clinical representation ↔ PCA control
        ↓
RBF SVM             ↔ Fidelity-kernel QSVC
        ↓
Paired performance + runtime evaluation
        ↓
Robustness → transportability → cross-disease tests
        ↓
Evidence verdict → Q-CARE dashboard
```

Phase 1 establishes data and classical references, Phase 2 freezes the fair quantum comparison, and Phase 3 tests robustness and transfer. The dashboard consumes artifacts; it does not retrain models.

## 5. Datasets

- **UCI Chronic Kidney Disease:** 400 records, 24 predictors, reported from Apollo Hospitals, Karaikudi, Tamil Nadu.
- **BD-KDD:** 988 records from Popular Diagnostic Centre, Savar Branch, Dhaka; frozen cross-cohort stress test with PARTIAL target comparability.
- **UCI Cleveland Heart Disease:** 303 records and 13 predictors; methodology-transfer test.
- **Pima Indians Diabetes / OpenML 37:** 768 records and eight predictors; women of Pima heritage near Phoenix, Arizona—not an Indian-population dataset.

## 6. Classical benchmark

RBF SVM is the matched primary reference. On development-only 5-fold CKD cross-validation repeated 10 times, the eight-variable model reached sensitivity, specificity, F1, and ROC-AUC of 1.000.

## 7. Quantum benchmark

QSVC uses a fidelity quantum kernel with `ZFeatureMap`, `reps=1`, no entanglement, eight qubits primary, six secondary, logical depth two, and `C=0.5`. At eight variables, repeated internal sensitivity was **0.985** and ROC-AUC approximately **0.999**. It met the predefined 0.05 descriptive competitiveness tolerance at eight and six variables.

## 8. Robustness

Classical SVM degraded less under added missingness and numeric perturbation. QSVC showed no small-sample advantage. Finite-shot stability is supported only in the tested local simulation; the small simulated-noise experiment is inconclusive for broad hardware robustness.

## 9. External transportability

On the BD-KDD cross-cohort stress test, RBF SVM ROC-AUC was **0.511 [0.475-0.546]** and QSVC ROC-AUC was **0.525 [0.489-0.561]**. Neither reliably exceeded chance and their paired difference included zero. Target comparability was **PARTIAL**, while all eight strong UCI feature-label relationships flattened toward chance in BD-KDD.

External transport failure reflected both target/cohort differences and changed feature–target relationships; therefore the experiment demonstrates transportability risk but cannot isolate pure conditional shift.

## 10. Cross-disease validation

Cleveland heart-disease methodology transfer was mixed: sensitivity and ROC-AUC were close, but specificity missed tolerance. Pima diabetes was poor for QSVC, including sensitivity of 0.043. Results are kept separate and are never averaged across diseases.

## 11. Key findings

1. QSVC can remain internally competitive at reduced feature budgets on this controlled CKD benchmark.
2. Competitive prediction did not establish advantage: QSVC was about 464× slower at eight variables and 477× slower at six.
3. Classical SVM was more robust in the tested missingness and perturbation settings.
4. Internal feature stability did not guarantee external feature transportability; both model AUC intervals included chance on BD-KDD.
5. Methodological generalisation was inconsistent across diseases.

## 12. Novelty

Q-CARE’s contribution is an integrated evaluation method: identical feature budgets, stable fold-safe selection, paired classical/QSVC benchmarking, PCA controls, robustness testing, runtime transparency, cross-cohort transportability, cross-disease validation, and explicit negative evidence. It does not claim a novel quantum algorithm or quantum advantage.

## 13. Limitations

- Small, single-site primary dataset with missing values and unusually high internal separability.
- Descriptive tolerance, not powered clinical non-inferiority.
- Partial target comparability in the BD-KDD cross-cohort stress test.
- No prospective or clinical validation.
- Exact local statevector evaluation; no real quantum hardware.
- Limited noise experiment and no large-cohort scalability demonstration.
- Not intended for diagnosis, treatment, clinical decision-making, or patient triage.

## 14. Run instructions

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
streamlit run app.py
```

Expected URL: `http://localhost:8501` when the default port is free. The temporary Phase 3D validation instance used `http://localhost:8520`. Demo mode uses precomputed artifacts and requires no IBM Quantum connection.

For the live segment, choose the borderline/mixed profile and click **ANALYSE PROFILE**. Present the `0.509` uncalibrated research-model score, the strong haemoglobin perturbation, five similar benchmark records, and the `2 OF 3 AGREE` VQC/QSVC/RBF comparison. State the visible **WEAK — DISPLAY WITH CAUTION** verdict.

## 15. Demo sequence

1. **Overview** — open on paired internal `1.000/0.999` → BD-KDD `0.511/0.525`, with both external intervals spanning chance.
2. **CKD Benchmark** — show `24 → 8`, then **Feature reduction** and **Classical vs quantum**.
3. **Quantum Evidence** — show **Runtime transparency** and the frozen circuit.
4. **Robustness & Shift** — open on the transportability comparison, then show **Feature transportability**.
5. **Quantum Evidence** — finish at **Final evidence summary**.

Use `demo_script_2min.md`; if time is cut, switch to `demo_script_60sec.md`.

## 16. Expected deliverables

All 16 required implementation categories are mapped in `expected_deliverables.md`. Fifteen are fully delivered; scalability is implemented as measured resource transparency but remains a research limitation at larger cohort sizes.

## 17. Team-ready handover

- **Presenter:** `five_minute_pitch.md`, `pitch_story.md`
- **Demo operator:** `demo_script_2min.md`, `demo_script_60sec.md`
- **Q&A lead:** `judge_questions.md`, `quantum_advantage_answer.md`, `quantum_explainer.md`
- **Submission editor:** this file, `final_pitch.md`, `novelty_statement.md`, `expected_deliverables.md`
- **Technical verifier:** `reproducibility_check.md`, `final_claim_review.md`, `../artifacts/final_model_manifest.json`
- **Visual verifier:** `screenshots/README.md`, `screenshot_pitch_mapping.md`, `screenshot_validation.md`, `accessibility_check.md`
- **Offline presenter:** `demo_backup/README.md`

Do not alter frozen metrics or add patient-screening claims for presentation.

## 18. Final visual evidence

Thirty-six screenshots are indexed in `screenshots/README.md`: the original 16 responsive evidence captures, seven live-VQC workflow captures, and 13 final single-page workstation captures. Every displayed scientific value remains traceable to frozen artifacts.

## 19. References

- [UCI Chronic Kidney Disease](https://archive.ics.uci.edu/dataset/336/chronic)
- [UCI Heart Disease](https://archive.ics.uci.edu/dataset/45/heart%2Bdisease)
- [Pima Indians Diabetes / OpenML 37](https://www.openml.org/d/37)
- [BD-KDD / Harvard Dataverse DOI](https://doi.org/10.7910/DVN/MB1LES)
- Repository bibliography: `../research/references.md`
- Provenance audit: `../reports/data_provenance.md`
- External audit: `../reports/validation/external_dataset_audit.md`

## Final position

**We did not demonstrate quantum advantage. We demonstrated why healthcare QML needs an evidence layer before anyone can responsibly claim one.**
