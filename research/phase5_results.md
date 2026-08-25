# Phase 5 Results — Final Hackathon Submission Package

## Outcome

Phase 5 is reconciled with the frozen Apple-HIG-inspired interface and the post-redesign validation package. No UI, model result, scientific artifact, patient workflow, or claim-registry value was changed. No presentation slides were created.

## Final pitch position

**One line:** Q-CARE is an evidence-first hybrid quantum healthcare benchmark that compares classical SVM and QSVC at the same feature budget—and reports when neither model transports reliably.

The 73-word spoken pitch is stored in `submission/final_pitch.md`.

## Winning evidence sequence

1. Open on internal RBF/QSVC ROC-AUC `1.000/0.999` becoming BD-KDD `0.511/0.525`, with both external intervals spanning chance.
2. Establish the fair experiment: 400 CKD records, `24 → 8`, fold-safe selection, identical classical/quantum budgets.
3. State the narrow positive result: QSVC sensitivity `0.985` versus classical `1.000`, within the predefined descriptive tolerance.
4. Reveal the cost: exact statevector QSVC approximately `464×` slower at eight variables.
5. Reveal shared transportability failure: BD-KDD RBF/QSVC ROC-AUC `0.511/0.525`, PARTIAL target comparability, and flattened feature-label signal.
6. Show dataset dependence: Cleveland mixed; Pima QSVC not competitive.
7. Close on the evidence verdict, not a quantum-advantage claim.

## Submission documents reconciled

All required files under `submission/` were reviewed against the frozen final UI:

- Problem coverage: `problem_statement_mapping.md`, `expected_deliverables.md`.
- Pitching: `final_pitch.md`, `pitch_story.md`, `five_minute_pitch.md`.
- Demo: `demo_script_2min.md`, `demo_script_60sec.md`.
- Quantum objections: `quantum_advantage_answer.md`, `quantum_explainer.md`.
- Judging: `judge_questions.md`, `judging_scorecard.md`.
- Novelty and architecture: `novelty_statement.md`, `architecture_spec.md`.
- Handover and control: `README_SUBMISSION.md`, `reproducibility_check.md`, `final_claim_review.md`.
- Visual use: `screenshot_pitch_mapping.md`, `screenshots/README.md`, `screenshot_validation.md`, `accessibility_check.md`.

All navigation instructions use the actual frozen labels: **Overview**, **CKD Benchmark**, **Robustness & Shift**, **Cross-Disease**, and **Quantum Evidence**. Retired “Lab,” “Validation,” and “Explorer” labels were removed from the final submission documents.

## Judge preparation

The bank contains more than 30 evidence-backed questions and now highlights the required TOP 10. It includes direct answers for the lack of quantum advantage, the rationale for testing quantum when classical is better, small sample size, near-perfect internal AUC, external failure, no entanglement, VQC rejection, real-hardware scope, early-detection positioning, and exact novelty.

The hardest answer is deliberately non-defensive: quantum was the hypothesis under test. QSVC produced a narrow internal competitiveness result, but not a performance, efficiency, robustness, or generalisation advantage. That decision prevents an unjustified quantum deployment path.

## Offline demo package

`submission/demo_backup/` now contains:

- final hero;
- CKD benchmark;
- matched classical/QSVC and runtime evidence;
- paired cross-cohort transport result;
- final evidence verdict;
- frozen circuit;
- architecture diagram;
- 60-second script;
- final one-line pitch;
- one-page presentation flow.

Every image is copied from the validated post-redesign screenshot set. No prototype image is referenced.

## Novelty

The final 104-word statement positions novelty as the integration of leakage-free stable selection, matched information budgets, paired benchmarking, PCA controls, runtime transparency, robustness, finite-shot/noise evaluation, external shift, cross-disease validation, and governed negative evidence. It makes no new-algorithm or quantum-advantage claim.

## Problem-statement coverage

The required hybrid pipeline, four biomedical datasets, classical candidates, stable features, QSVC fidelity kernel, paired metrics, interpretability, runtime, robustness, external transfer, cross-disease validation, circuit visualisation, documentation, reproducibility, and responsible-AI controls are delivered. Near-term compatibility is explicitly **PARTIAL** because execution is simulator-only; real-hardware validation is not claimed.

## Phase boundary

The stop condition prohibits slides. The package contains slide-ready screenshots and a standalone SVG architecture diagram, but no PPTX or presentation deck.

## Final release gate — 25 August 2026

- Full suite: **71 passed**.
- Claim-registry validation: **zero errors**.
- Claim-registry SHA-256: `fe3c78e294406358dddda332522bce35cb0483321c4d129069765c5225a90528`.
- Phase 3D route: all affected pages rendered successfully in local headless Chrome.
- Executable-source scans: no absolute `/Users/...` path and no credential-like assignment found.
- Frozen science and model artifacts: unchanged.
