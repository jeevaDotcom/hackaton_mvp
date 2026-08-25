# Screenshot-to-Pitch Mapping

Use only the post-redesign files indexed in `screenshots/README.md`.

| Pitch moment | Screenshot | Why this screenshot | Metric shown | Backup if live demo fails |
|---|---|---|---|---|
| Opening hook | `screenshots/11_demo_hero.png` | Strongest single visual; gives both models equal visual weight | Internal RBF/QSVC `1.000/0.999` → external `0.511/0.525` | `demo_backup/01_demo_hero.png` |
| Problem framing | `screenshots/01_overview.png` | Puts paired performance and uncertainty on one surface | External intervals `0.475–0.546` and `0.489–0.561`; paired difference includes zero | `demo_backup/01_demo_hero.png` |
| CKD experiment | `screenshots/02_ckd_benchmark.png` | Establishes the controlled protocol and stable reduction | `24 → 8`; 400 records | `demo_backup/02_ckd_benchmark.png` |
| Fair classical/quantum comparison | `screenshots/04_classical_vs_quantum.png` | Shows identical budgets and the positive internal result without hiding the classical reference | QSVC `0.985/0.999`; RBF SVM `1.000/1.000` | `demo_backup/03_classical_vs_quantum.png` |
| Quantum cost | `screenshots/04_classical_vs_quantum.png` | Keeps runtime beside prediction; no extra live navigation | `464× slower` at eight variables | `demo_backup/03_runtime_result.png` |
| External-shift reveal | `screenshots/06_external_shift.png` | Shows that neither model retained reliable discrimination and target comparability is partial | RBF `0.511`; QSVC `0.525`; paired `+0.015 [-0.029–+0.058]` | `demo_backup/04_external_shift.png` |
| Root-cause evidence | `screenshots/12_feature_transportability.png` | Shows why the result is transportability risk, not isolated pure conditional shift | All eight strong UCI feature-label relationships flatten toward chance in BD-KDD | `screenshots/13_creatinine_comparison.png` |
| Cross-disease evidence | `screenshots/07_cross_disease.png` | Shows dataset-dependent outcomes rather than an averaged claim | CKD supported; Cleveland mixed; Pima not supported | Use indexed screenshot directly |
| Evidence methodology | `screenshots/08_quantum_evidence.png` | Summarises performance, cost, robustness, and the shared external result | Classical and quantum both `NOT SUPPORTED`; `TRANSPORTABILITY FAILURE` | Use indexed screenshot directly |
| Quantum explanation | `screenshots/09_quantum_circuit.png` | Answers “what is quantum here?” with the executed circuit | 8 qubits; depth 2; 16 gates; no entanglement | `demo_backup/06_quantum_circuit.png` |
| Closing verdict | `screenshots/10_responsible_ai.png` | Ends on the frozen claim and responsible-use boundary | No demonstrated performance, runtime, robustness, or generalisation advantage | `demo_backup/05_evidence_verdict.png` |
