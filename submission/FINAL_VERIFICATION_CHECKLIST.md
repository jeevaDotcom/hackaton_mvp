# Q-CARE Final Verification Checklist

## 1. UI

**COMPLETE**

Single Patient, CSV Batch, and Scan Report are visible as the three entry paths. The single-page workstation starts without exception, preserves the Apple-style theme, and exposes gated Research PDF generation.

## 2. Single Patient

**COMPLETE**

The eight-feature manual form, Compare All mode, and Single Model mode for RBF-SVM, QSVC, and VQC were exercised with synthetic frozen profiles. Outputs remain binary CKD-like/non-CKD-like research classifications with agreement and influence evidence.

## 3. CSV Batch

**COMPLETE**

The bundled synthetic batch completed mapping, validation, invalid-row isolation, three-model inference, consensus, summary charts, filters, and downloadable CSV export. Serum Albumin remains ambiguous and is not auto-mapped.

## 4. Model Comparison

**COMPLETE**

RBF-SVM, QSVC, and VQC are displayed with Sensitivity, Specificity, F1, and ROC-AUC from frozen artifacts. VQC remains weak/display-with-caution; QSVC is internally competitive without a quantum-advantage claim.

## 5. Visual Evidence

**COMPLETE**

Performance, runtime, feature-influence, agreement, 24-to-8, quantum-kernel, circuit, VQC-trace, robustness, transportability, and evidence-report visuals are present in the UI/artifacts and were checked for nonblank output.

## 6. 24 → 8 Features

**COMPLETE**

The UI and reports show 24 original predictors, leakage-safe selection, the eight selected features, and exact artifact-backed comparisons. No equivalence, test-replacement, or clinical cost-reduction claim is made.

## 7. Quantum Evidence

**COMPLETE**

QSVC evidence identifies 8 qubits, ZFeatureMap, reps=1, no entanglement, fidelity kernel, and C=0.5. VQC evidence identifies 8 qubits, ZFeatureMap, RealAmplitudes, linear entanglement, COBYLA, 40 evaluations, stored training trace, and stored circuit text.

## 8. Robustness & Research Evidence

**COMPLETE**

Missingness, perturbation, training-size, finite-shot, and simulated-noise artifacts render with model applicability stated. No VQC robustness values are invented.

## 9. Scan / Report

**COMPLETE**

Digital PDF extraction, image OCR, source provenance, units, confidence/review, confirmation gating, correction, manual fallback, and safe bad-input behavior were verified. OCR does not infer CKD stage.

## 10. AI Research Assistant

**NOT IMPLEMENTED / OPTIONAL FUTURE ENHANCEMENT**

The deterministic automated evidence summary in Research PDF is implemented. It is not a conversational, evidence-grounded AI Research Assistant.

## 11. Disease Stage

**COMPLETE AS RESPONSIBLE SCOPE CONTROL**

CKD STAGE RESEARCH VIEW is visible and states NOT VALIDATED IN CURRENT Q-CARE MODEL. No Stage 1–5 output, score-to-stage mapping, creatinine-only rule, or eGFR staging exists.

## 12. Research PDF

**COMPLETE**

Single Patient, Scan Report, and CSV Batch reports generate valid five-page PDFs with experiment IDs, evidence sections, charts, page numbers, disclaimers, and responsible-use wording. Batch reports remain summary-only and point to the row-level CSV.

## 13. Final Technical Test

**COMPLETE**

Original environment: 151 passed, 0 failed, 5 warnings. Clean copied environment: 151 passed, 0 failed, 5 warnings. Read-only final manifest: 34/34 checks passed. Disposable application health returned HTTP 200.
