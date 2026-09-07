# Q-CARE Final Technical Acceptance

## Final date/time

2026-09-08. Acceptance was run against the current working tree, including uncommitted Phase 1–3 changes.

## Environment

Original environment:

- Python 3.11.9
- Streamlit 1.62.0
- pandas 3.0.5
- scikit-learn 1.9.0
- Qiskit 2.5.2
- qiskit-machine-learning 0.9.1
- Matplotlib 3.11.1
- PyMuPDF 1.28.2
- pytest 9.1.1
- joblib 1.5.3
- Tesseract 5.5.2

Clean smoke environment installed `requirements.txt` successfully and resolved Streamlit 1.63.0, joblib 1.6.0, with the same core Python/Qiskit/PyMuPDF/Matplotlib compatibility. Tesseract 5.5.2 was available.

## Tests

Original environment:

- `pytest -q`: **151 passed, 0 failed, 5 warnings, 15.96 seconds**

Clean copied environment:

- Full `pytest -q`: **151 passed, 0 failed, 5 warnings, 14.63 seconds**
- Critical acceptance tests: **65 passed, 0 failed, 5 warnings**

Warnings are the existing PyMuPDF/Swig deprecation warnings.

## Manifest

`scripts/final_acceptance_check.py` is read-only and returned:

- **FINAL ACCEPTANCE MANIFEST: PASS (34 passed, 0 failed)**

It checked application modules, frozen model artifacts and preprocessors, Phase 1/2/3/3C evidence, OCR assets, batch assets/tests, stage scope, report module/demo PDFs, critical tests, Python, Streamlit, and Tesseract.

## Functional acceptance

- Single Patient: PASS. Compare All and RBF-SVM/QSVC/VQC Single Model paths rendered and executed without exceptions. Research PDF generation/download was verified after analysis.
- CSV Batch: PASS. Sample batch produced 12 rows, 10 valid, 2 invalid; valid rows received all three predictions, invalid rows retained readable errors, filters/export/summary were verified, and serum albumin safety remained enforced.
- Scan/OCR: PASS. Digital embedded-text path, image path, source evidence, confirmation gate, bad-input handling, and mocked Tesseract fallback were verified.
- CKD Stage: PASS. Visible scope view; no generated Stage 1–5 output, score mapping, creatinine-only rule, or eGFR implementation.
- Research PDF: PASS for manual, scan, and batch reports. Three five-page demo PDFs open, contain text, IDs, disclaimers, page numbers, and no blank pages. Fifteen rendered page images were produced for QA; representative profile, feature, quantum, final, and batch pages were visually inspected.

## Visual evidence

Stored and/or rendered evidence includes performance, runtime, feature influence, 24-to-8 comparison, QSVC circuit, kernel heatmap, VQC circuit and training trace, robustness, transportability, and final evidence-report visuals. No blank demo PDF pages were found.

## Claim-safety scan

The final scan found no unsafe positive current-output claim. Matches were limited to explicit negative/protective wording, prohibited-wording documentation, or research narrative such as “no quantum advantage,” “not a clinical diagnostic system,” “not a calibrated disease probability,” partial transportability, and no clinical validation. No runtime absolute developer path was found in `app.py`, `src/`, or `scripts/`.

## Live quantum safety

Live runtime source contains no native Qiskit/Qiskit Machine Learning imports. QSVC uses the analytical ZFeatureMap(reps=1) fidelity-kernel path; VQC uses the NumPy statevector path. Offline experiment scripts/artifacts remain available and were not altered.

## Application health

Q-CARE started on disposable port 8599 and returned HTTP 200 for both `/_stcore/health` and `/`. The clean-copy app also returned HTTP 200 for both endpoints. Both temporary servers were stopped.

## Offline/local demo

The demo uses local frozen artifacts, local OCR samples, local Tesseract/PyMuPDF, and deterministic local report generation. No cloud OCR, external LLM, external quantum provider, API key, or internet dependency is required for the core demo.

## Remaining limitations

The AI Research Assistant checklist item remains **NOT IMPLEMENTED / OPTIONAL FUTURE ENHANCEMENT**. The deterministic Research PDF automated evidence summary is not a conversational assistant. Existing scientific limitations remain: research-only outputs, weak VQC, high QSVC computational cost, partial BD-KDD target comparability, no demonstrated external transportability, no Stage 1–5 validation, and no clinical deployment validation.

## Remaining blockers

None for the stated final technical acceptance scope.

No commit, push, branch change, remote change, authentication, or Git configuration change was performed.
