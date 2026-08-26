# Q-CARE FINAL HACKATHON BUILD

Q-CARE is a single-page, evidence-first quantum clinical research workstation. It compares three frozen model types—classical RBF SVM, quantum-kernel QSVC, and trainable VQC—without presenting the output as diagnosis or calibrated disease risk.

The workflow includes:

- live patient-style eight-variable research assessment;
- biomedical CSV upload and Data Health Check;
- frozen feature engineering and `24 → 8` reduction evidence;
- actual QSVC and VQC circuit views;
- matched classical/quantum benchmark evidence;
- missingness, perturbation, training-size, finite-shot, and noise robustness evidence;
- Phase 3C external transportability evidence with PARTIAL target comparability;
- a final claim-controlled evidence report.

VQC interaction uses exact NumPy statevector inference. QSVC interaction uses the analytical `ZFeatureMap(reps=1)` fidelity kernel. Streamlit interaction does not deserialize or execute native Qiskit models.

This is a research prototype, not a clinical diagnostic device. It is not clinically validated and does not provide treatment, triage, referral, or confirmed-CKD decisions.

Run:

```bash
streamlit run app.py
```

- Tests: **97 passed**
- Screenshots: **36 indexed**
- Commit SHA: **HEAD** — resolve the immutable release SHA with `git rev-parse HEAD`
- Final status: **SUBMISSION READY FOR RESEARCH DEMONSTRATION; NOT FOR CLINICAL USE**
