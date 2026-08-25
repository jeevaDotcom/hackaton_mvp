# Delivery Table (Expected Deliverables)

| # | Expected Deliverable | Q-CARE Implementation | Evidence | Status |
|---:|---|---|---|---|
| 1 | Biomedical data ingestion | Schema-aware CKD loader plus audited external and cross-disease loaders | `src/phase1/data.py`; `artifacts/data_provenance.json` | FULLY DELIVERED |
| 2 | Data quality pipeline | Token repair, missingness handling, encoding, scaling, and fold-local fitting | `reports/data_quality.md`; `artifacts/quantum_preprocessing_audit.json` | FULLY DELIVERED |
| 3 | Classical models | Logistic regression, random forest, SVM, and XGBoost comparison; RBF SVM retained as matched reference | `reports/classical_cv_summary.csv`; `artifacts/development_decision.json` | FULLY DELIVERED |
| 4 | Feature-selection engine | Repeated leakage-free selection with frequency, rank, Jaccard, and PCA control | `reports/feature_stability.csv`; `reports/feature_stability_overall.csv`; `artifacts/quantum_cv_summary.csv` | FULLY DELIVERED |
| 5 | QSVC quantum model | `FidelityQuantumKernel` with frozen low-depth `ZFeatureMap` | `artifacts/quantum_config.json`; `artifacts/final_model_manifest.json` | FULLY DELIVERED |
| 6 | Hybrid evaluation workflow | Paired classical/QSVC folds, preprocessing, regularisation, and identical feature budgets | `src/phase2/benchmark.py`; `artifacts/quantum_paired_fold_deltas.csv` | FULLY DELIVERED |
| 7 | Performance benchmark | Sensitivity, specificity, F1, ROC-AUC, PR-AUC where applicable, feature budgets, and runtime | `artifacts/phase3/reference_cv_summary.csv`; `artifacts/phase3/external_ckd_metrics.csv` | FULLY DELIVERED |
| 8 | Robustness testing | Added missingness, numeric perturbation, and training-size experiments | `artifacts/phase3/missingness.csv`; `artifacts/phase3/perturbation.csv`; `artifacts/quantum_training_size_results.csv` | FULLY DELIVERED |
| 9 | Quantum resource/noise analysis | Qubit/depth/runtime reporting, finite shots, and limited simulated noise; no real-hardware execution | `reports/quantum/resource_comparison.csv`; `artifacts/quantum_finite_shot_results.csv`; `artifacts/quantum_noise_results.csv` | PARTIALLY DELIVERED — SIMULATOR ONLY |
| 10 | External dataset-shift evaluation | Frozen eight-variable CKD transfer to BD-KDD with mapping audit | `artifacts/phase3/external_ckd_metrics.csv`; `reports/validation/external_dataset_audit.md` | FULLY DELIVERED |
| 11 | Cross-disease validation | Separate Cleveland heart disease and Pima diabetes methodology tests | `artifacts/phase3/cross_disease_cv.csv`; `reports/validation/cross_disease_validation.md` | FULLY DELIVERED |
| 12 | Evidence-first dashboard | Five-page Streamlit platform with offline replay and evidence download | `app.py`; `src/results_repository.py`; `submission/screenshots/` | FULLY DELIVERED |
| 13 | Quantum circuit visualisation | Real decomposed Qiskit circuit plus plain-language interpretation | `scripts/render_frozen_circuit.py`; `artifacts/qsvc_z_reps1_8_circuit.txt` | FULLY DELIVERED |
| 14 | Documentation | README, protocols, provenance, phase reports, submission summary, scripts, and judge bank | `README.md`; `research/`; `submission/` | FULLY DELIVERED |
| 15 | Reproducibility/test suite | Phase runners, manifests, 63 passing tests, source-value checks, and prohibited-claim checks | `scripts/`; `artifacts/final_model_manifest.json`; `tests/`; `submission/reproducibility_check.md` | FULLY DELIVERED |
| 16 | Responsible-AI framework | Claim registry, persistent non-clinical footer, provenance language, and explicit negative evidence | `artifacts/claim_registry.json`; `app.py`; `submission/final_claim_review.md` | FULLY DELIVERED |
