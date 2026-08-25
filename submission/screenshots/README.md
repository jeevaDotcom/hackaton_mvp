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

Metric-by-metric verification for all 16 files is recorded in [`../screenshot_validation.md`](../screenshot_validation.md). The reproducible capture path is `scripts/capture_phase3d_screenshots.mjs`.
