# Phase 3 results

## Outcome

Phase 3 freezes an evidence-first benchmarking product, not a diagnostic claim. On 5×10 development CV, the eight-variable QSVC achieved sensitivity 0.985, specificity 0.980, and ROC-AUC 0.999 versus 1.000, 1.000, and 1.000 for the identical-budget classical RBF SVM. QSVC did not establish superiority.

On the later Phase 3C uncertainty audit, BD-KDD RBF SVM ROC-AUC was 0.511 [0.475-0.546] and QSVC ROC-AUC was 0.525 [0.489-0.561]. Neither model reliably exceeded chance and their paired difference included zero. Target comparability was only PARTIAL and all eight feature-label associations flattened, so this is a cross-cohort transportability stress-test failure rather than like-for-like validation.

## Product-story decision

| Story | Scientific defensibility | Hackathon impact | Problem alignment | Demo clarity | Technical novelty | Total / 25 |
|---|---|---|---|---|---|---|
| A. Quantum-enhanced CKD screening | 1 | 4 | 3 | 4 | 3 | 15 |
| B. Feature-efficient hybrid disease detection | 3 | 4 | 4 | 4 | 3 | 18 |
| C. Evidence-first quantum healthcare benchmarking platform | 5 | 5 | 5 | 5 | 5 | 25 |
| D. Generic multi-disease risk calculator | 1 | 3 | 2 | 4 | 2 | 12 |

Selected: **C. Evidence-first quantum healthcare benchmarking platform.** It matches what the evidence can support: transparent identical-budget comparisons, robustness diagnostics, external shift disclosure, and reusable disease-specific methodology.

## Frozen evidence package

- Primary representation: eight clinical variables `hemo, al, dm, sg, pcv, appet, htn, sc`.
- Optional compact representation: six variables `hemo, al, dm, sg, pcv, appet`.
- Quantum model: QSVC, ZFeatureMap reps=1, no entanglement, C=0.5, exact local statevector fidelity.
- Output category: class label plus signed decision score; no probability/risk percentage.
- Final model training population: 320-case UCI development partition only.
- Locked test: referenced only through the already-frozen Phase 2 evaluation; never reused for Phase 3 tuning or robustness.
