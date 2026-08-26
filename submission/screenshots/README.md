# Final Q-CARE Screenshot Index

Phase 3D evidence files were regenerated on 25 August 2026 from the final redesigned UI. Desktop captures use a consistent 956 × 1000 viewport; responsive captures use 480 × 900 mobile-width and 834 × 1083 tablet canvases.

| Filename | Page | What it demonstrates | Recommended use |
|---|---|---|---|
| `01_overview.png` | Overview | Paired RBF SVM/QSVC internal `1.000/0.999` → BD-KDD `0.511/0.525`, with both external intervals spanning chance | README, pitch, poster |
| `02_ckd_benchmark.png` | CKD Benchmark | Controlled experiment framing and `24 → 8` feature reduction | Pitch, README |
| `03_feature_stability.png` | CKD Benchmark | Named eight-variable signature and Jaccard stability table | Poster, technical judging |
| `04_classical_vs_quantum.png` | CKD Benchmark | Identical-budget RBF SVM/QSVC metrics and runtime verdict | Pitch, poster, demo backup |
| `05_robustness_missingness.png` | Robustness & Shift | Sensitivity degradation under 0–20% additional missingness | Poster, technical judging |
| `06_external_shift.png` | Robustness & Shift | Paired internal-to-external transport story with partial target comparability | Pitch, README, demo backup |
| `07_cross_disease.png` | Cross-Disease | Separate CKD, Cleveland, and Pima evidence verdicts | Poster, technical judging |
| `08_quantum_evidence.png` | Quantum Evidence | Evidence matrix showing the shared classical/quantum transportability failure | Pitch, submission portal |
| `09_quantum_circuit.png` | Quantum Evidence | Frozen eight-qubit, depth-two ZFeatureMap and interpretation | Poster, technical judging |
| `10_responsible_ai.png` | Quantum Evidence | Frozen verdict, claim-registry status, and responsible-use boundary | Pitch close, demo backup |
| `11_demo_hero.png` | Overview | Strongest single visual: paired internal `1.000/0.999` → external `0.511/0.525` evidence | Pitch hero, README, demo backup |
| `12_feature_transportability.png` | Robustness & Shift | Signed univariate AUCs and 95% intervals for all eight frozen features in both cohorts | Technical judging, poster |
| `13_creatinine_comparison.png` | Robustness & Shift | Label-specific serum-creatinine medians in UCI and BD-KDD | Technical judging, root-cause explanation |
| `mobile_overview.png` | Overview | Narrow-screen hero layout with collapsed navigation | Submission portal, responsive QA |
| `mobile_external_shift.png` | Robustness & Shift | Narrow-screen external-shift narrative and comparison | Responsive QA, demo backup |
| `tablet_ckd_benchmark.png` | CKD Benchmark | Tablet layout, persistent navigation, and stacked process flow | Responsive QA, submission portal |
| `live_01_patient_entry.png` | Live Research Assessment | Persistent research boundary, three actual-record presets, and eight readable input controls | Live demo opening |
| `live_02_vqc_result.png` | Live Research Assessment | Experimental classification, uncalibrated score `0.509`, weak-model caution, and VQC architecture | Live demo result |
| `live_03_factor_explanation.png` | Live Research Assessment | Ranked local perturbation analysis with haemoglobin as the strongest influence | Explainability evidence |
| `live_04_similar_records.png` | Live Research Assessment | Five anonymised nearest UCI records, their stored classes, and same-input model decisions | Neighbour/comparison evidence |
| `live_05_model_comparison.png` | Live Research Assessment | VQC/QSVC/RBF decisions, `2 OF 3 AGREE`, and uncertainty warning | Live demo comparison |
| `live_06_review_checklist.png` | Live Research Assessment | Six generic review prompts and prominent clinical limitations | Responsible-use evidence |
| `live_07_quantum_circuit.png` | Live Research Assessment | Plain-English variational-model explanation and the real frozen eight-qubit circuit | Quantum technical evidence |
| `01_full_page_hero.png` | Single-page workstation | Q-CARE thesis, research boundary, workflow, and dual entry path | Final demo opening |
| `02_live_patient_assessment.png` | Single-page workstation | Same-profile RBF SVM, QSVC, and VQC assessment | Live demo |
| `03_model_agreement.png` | Single-page workstation | `2 OF 3 AGREE` and disagreement safety message | Responsible-use evidence |
| `04_vqc_transparency.png` | Single-page workstation | Frozen VQC metrics, weak-model caution, and uncalibrated score | VQC evidence |
| `05_similar_records.png` | Single-page workstation | Nearest benchmark records and clinician-review checklist | Explanation evidence |
| `06_data_health_check.png` | Single-page workstation | Uploaded-dataset schema, missingness, coverage, and readiness | Data-health evidence |
| `07_feature_reduction.png` | Single-page workstation | Wrapper RFE `24 → 8` and internal stability boundary | Feature evidence |
| `08_three_model_comparison.png` | Single-page workstation | Protocol-labelled RBF SVM, QSVC, and VQC table | Benchmark evidence |
| `09_quantum_circuits.png` | Single-page workstation | Actual frozen QSVC and VQC circuit disclosures | Quantum technical evidence |
| `10_robustness.png` | Single-page workstation | Frozen robustness tabs with no invented VQC values | Robustness evidence |
| `11_external_transportability.png` | Single-page workstation | External AUCs, intervals, and PARTIAL comparability | Transport evidence |
| `12_single_page_feature_transportability.png` | Single-page workstation | UCI-to-BD-KDD feature-signal comparison | Root-cause evidence |
| `13_final_evidence_report.png` | Single-page workstation | Final frozen status and clinical-use boundary | Demo close |

Metric-by-metric verification is recorded in [`../screenshot_validation.md`](../screenshot_validation.md). Reproducible capture paths are `scripts/capture_phase3d_screenshots.mjs`, `scripts/capture_live_vqc_screenshots.mjs`, and `scripts/capture_single_page_screenshots.mjs`.
