# Screenshot Metric Validation

Validated on **25 August 2026** against the Phase 3D screenshot files and frozen repository artifacts. Values are compared at the same precision shown by the UI.

| Screenshot | Displayed metric | Artifact source | Expected value | Actual value | Result |
|---|---|---|---|---|---|
| `01_overview.png` | Internal RBF/QSVC AUC; external RBF/QSVC AUC and intervals; paired difference | Reference summaries; `external_ckd_metrics.csv`; `external_auc_bootstrap.csv` | `1.000/0.999`; `0.511 [0.475-0.546]`; `0.525 [0.489-0.561]`; `+0.015 [-0.029 to +0.058]` | Same | PASS |
| `02_ckd_benchmark.png` | Original → primary feature count; records | `artifacts/final_model_manifest.json`; `artifacts/data_provenance.json` | `24 → 8`; `400` | `24 → 8`; `400` | PASS |
| `03_feature_stability.png` | Selection frequencies; mean ranks; Jaccard stability | `reports/feature_stability.csv` | Frequencies `1.00/0.90`; ranks `1.0–7.9`; Jaccard `0.912` | Frequencies `1.00/0.90`; ranks `1.0–7.9`; Jaccard `0.912` | PASS |
| `04_classical_vs_quantum.png` | Eight/six-variable sensitivity, specificity, F1, ROC-AUC, runtime; `464×` | `artifacts/phase3/reference_cv_summary.csv`; `artifacts/quantum_cv_summary.csv` | 8-QSVC `0.985/0.980/0.986/0.999/0.5071`; 8-RBF `1.000/1.000/1.000/1.000/0.0016`; 6-QSVC `0.977/0.978/0.981/0.995/0.3236`; 6-RBF `0.998/0.987/0.995/1.000/0.0007`; `464×` | Same | PASS |
| `05_robustness_missingness.png` | Sensitivity at 0% and 20% additional missingness | `artifacts/phase3/missingness.csv` | RBF `1.000 → 0.962`; QSVC `0.985 → 0.930` | RBF `1.000 → 0.962`; QSVC `0.985 → 0.930` | PASS |
| `06_external_shift.png` | Paired internal/external AUC evidence; target comparability | Reference summaries; `external_auc_bootstrap.csv`; `phase3c_summary.json` | `1.000/0.999`; `0.511/0.525`; both intervals include `0.5`; `PARTIAL` | Same | PASS |
| `07_cross_disease.png` | CKD metrics and runtime; Cleveland and Pima results | `artifacts/phase3/reference_cv_summary.csv`; `artifacts/phase3/cross_disease_cv.csv`; `artifacts/quantum_cv_summary.csv` | CKD `1.000/1.000`, `0.985/0.999`, `464×`; Cleveland `0.784/0.898`, `0.767/0.860`, `353×`; Pima `0.526/0.833`, `0.043/0.653`, `498×` | Same | PASS |
| `08_quantum_evidence.png` | External-generalisation evidence row | `artifacts/claim_registry.json`; `external_auc_bootstrap.csv` | Classical `NOT SUPPORTED`; Quantum `NOT SUPPORTED`; `TRANSPORTABILITY FAILURE` | Same | PASS |
| `09_quantum_circuit.png` | Qubits; depth; gates; entanglement | `artifacts/final_model_manifest.json`; `artifacts/qsvc_z_reps1_8_circuit.txt` | `8`; `2`; `16`; none | `8`; `2`; `16`; none | PASS |
| `10_responsible_ai.png` | Finite-shot sensitivity, specificity, ROC-AUC; frozen verdict | `artifacts/quantum_finite_shot_results.csv`; `artifacts/claim_registry.json` | Tested shots: sensitivity `0.980`, specificity `1.000`, ROC-AUC `0.994–0.995`; no demonstrated quantum advantage | Same | PASS |
| `11_demo_hero.png` | Paired internal → external ROC-AUC | Same sources as `01_overview.png` | `1.000/0.999 → 0.511/0.525` | Same | PASS |
| `12_feature_transportability.png` | Signed feature AUCs and intervals | `reports/root_cause/univariate_auc.csv` | UCI `0.031–0.923`; all eight BD-KDD estimates `0.471–0.518`, with intervals including `0.5` | Same | PASS |
| `13_creatinine_comparison.png` | Serum-creatinine medians by cohort and label | `reports/root_cause/per_label_feature_profiles.csv` | UCI CKD/non-CKD `2.25/0.90`; BD-KDD CKD/non-CKD `7.71/7.10` mg/dL | Same | PASS |
| `mobile_overview.png` | External AUCs, intervals, and paired difference | Same sources as `01_overview.png` | `0.511`; `0.525`; `+0.015 [-0.029 to +0.058]` | Same | PASS |
| `mobile_external_shift.png` | External intervals and statistical finding | Same sources as `06_external_shift.png` | `0.475-0.546`; `0.489-0.561`; paired `+0.015`; neither reliably better than random | Same | PASS |
| `tablet_ckd_benchmark.png` | Original → primary feature count; records | Same sources as `02_ckd_benchmark.png` | `24 → 8`; `400` | `24 → 8`; `400` | PASS |
| `live_01_patient_entry.png` | Feature count and profile source | `artifacts/live_vqc/metadata.json`; `presets.json` | Eight frozen features; actual complete UCI development records | Same | PASS |
| `live_02_vqc_result.png` | Mixed-preset score, performance caution, architecture | Frozen weights/preprocessor; `metadata.json`; `metrics.json` | `0.509`; `WEAK — DISPLAY WITH CAUTION`; 8 qubits; ZFeatureMap/RealAmplitudes reps 1 | Same | PASS |
| `live_03_factor_explanation.png` | Top local perturbation | Frozen inference plus training median/mode references | Haemoglobin; absolute score change `0.214`; strong influence | Same | PASS |
| `live_04_similar_records.png` | Five neighbours and stored classes | `reference_records.csv`; frozen preprocessor | Five anonymised matches; all displayed stored classes non-CKD | Same | PASS |
| `live_05_model_comparison.png` | Same-profile decisions and agreement | Frozen VQC/QSVC/RBF artifacts | VQC CKD-like; QSVC/RBF non-CKD-like; `2 OF 3 AGREE` | Same | PASS |
| `live_06_review_checklist.png` | Review prompts and limitations | Live-page safety contract | Six generic prompts; clinical-review limitation visible | Same | PASS |
| `live_07_quantum_circuit.png` | Model process and real circuit | `metadata.json`; `circuit.txt` | 8 values/qubits; ZFeatureMap; trainable RealAmplitudes; linear entanglement; COBYLA | Same | PASS |
| `01_full_page_hero.png`–`11_external_transportability.png`, `12_single_page_feature_transportability.png`, `13_final_evidence_report.png` | Integrated single-page patient, upload, benchmark, circuit, robustness, transport, and verdict evidence | Frozen Phase 1–3D artifacts; `artifacts/live_vqc/`; claim registry | Same metrics and interpretations as the validated source panels; no new scientific estimates | Same | PASS |

## Result

**PASS — all 36 indexed screenshots validated; zero stale or illustrative scientific values.** The original claim registry remains unchanged and produced zero validation errors; final SHA-256 `fe3c78e294406358dddda332522bce35cb0483321c4d129069765c5225a90528`.
