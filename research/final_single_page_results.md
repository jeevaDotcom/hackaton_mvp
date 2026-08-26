# Final Single-Page Q-CARE Results

Validated on **26 August 2026** against the frozen repository artifacts.

1. **Application URL:** `http://127.0.0.1:8501` after a controlled clean restart with one localhost-only Streamlit process.
2. **Single-page structure:** Patient or CSV entry, data health, live assessment, explanations, neighbours, feature engineering, benchmark, circuits, robustness, transportability, and final evidence report are presented in one continuous workstation.
3. **Patient workflow:** PASS — the three supplied UCI demonstration profiles and all eight frozen input controls execute without retraining.
4. **Dataset workflow:** PASS — CSV upload, target selection, and local schema/data-health analysis execute without automatic model evaluation.
5. **Data health:** PASS — sample count, feature count, target classes, class balance, missingness, duplicates, types, range anomalies, required-feature coverage, and shift flags are disclosed. Incompatible data is blocked with the required review message.
6. **Three-model comparison:** PASS — RBF SVM, QSVC, and VQC receive the identical eight-variable profile and display model type, prediction, evidence status, and agreement.
7. **VQC status:** PASS — sensitivity `0.640`, specificity `0.567`, F1 `0.674`, ROC-AUC `0.676`, and **WEAK — DISPLAY WITH CAUTION** remain frozen. Scores are explicitly uncalibrated and are not presented as disease probabilities.
8. **Similar records:** PASS — five anonymised UCI neighbours are shown after the same frozen preprocessing, with an explicit non-diagnostic boundary.
9. **Quantum circuits:** PASS — the real frozen QSVC and VQC circuit text and architecture descriptions are disclosed.
10. **Robustness:** PASS — missingness, perturbation, training-size, finite-shot, and simulated-noise evidence is retained. No VQC robustness result is invented.
11. **External validation:** PASS — RBF SVM `0.511 [0.475–0.546]`, QSVC `0.525 [0.489–0.561]`, PARTIAL target comparability, and the Phase 3C interpretation are unchanged.
12. **Final evidence report:** PASS — the report ends at **RESEARCH EVIDENCE ONLY — NOT A CLINICAL DIAGNOSTIC SYSTEM**.
13. **Screenshots:** PASS — 13 regenerated single-page captures are stored in `submission/screenshots/`, alongside the retained 16 historical and seven live-workflow captures (**36 total**).
14. **Automated tests:** PASS — `97 passed` on the final crash-safe rerun. Local headless-browser validation also completed with zero page, console, or Streamlit exceptions.
15. **Remaining limitations:** research-only system; weak VQC; uncalibrated circuit score; no clinical or prospective validation; no real-hardware claim; limited noise study; external target comparability is partial. The original native Qiskit UI execution was replaced by exact NumPy statevector VQC inference and the exact analytical `ZFeatureMap(reps=1)` QSVC fidelity kernel to prevent native worker crashes without changing frozen predictions or metrics.
16. **Release decision:** **READY FOR RESEARCH DEMONSTRATION. NOT READY FOR CLINICAL USE.**

No model was retrained, tuned, or recalibrated during this integration.

The restart audit found no new Python crash report, segmentation fault, native Qiskit thread fault, or Streamlit traceback. Runtime source contains no Qiskit deserialization import; VQC interaction uses the exact NumPy statevector executor and QSVC interaction uses the analytical separable `ZFeatureMap(reps=1)` fidelity kernel.
