# Phase 3C — Proposed Claim Changes

## Status

**Proposal only.** No change has been made to `artifacts/claim_registry.json`, Streamlit, the result repository, README, submission material, or earlier research reports.

Phase 3C changes the interpretation boundary: BD-KDD is a cross-cohort transport stress test with **PARTIAL** target comparability, not established like-for-like CKD external validation. Both frozen model AUC intervals include 0.5, their paired difference includes zero, and all eight feature associations are flattened within BD-KDD.

## Registry-level proposal

| Claim ID | Disposition | Proposed action |
|---|---|---|
| `CLAIM_EXTERNAL_AUC` | REWORD | Keep the measured value 0.5253806. Change text to “Frozen QSVC ROC-AUC was 0.525 on the BD-KDD cross-cohort transport stress test; its 95% bootstrap CI [0.489, 0.561] included random discrimination.” Change scope to state target comparability is PARTIAL, there was no external retraining, and this is not like-for-like clinical external validation. Add `reports/root_cause/external_auc_bootstrap.md` and `reports/root_cause/target_definition_audit.md` as evidence if the schema permits multiple artifacts. |
| `CLAIM_QUANTUM_SUPERIORITY` | KEEP PROHIBITED | The paired external delta is +0.0148 [−0.0292, +0.0581]. It supplies no quantum benefit claim. |
| `CLAIM_CLINICAL_GRADE` | KEEP PROHIBITED | Partial target comparability and random-range external AUC reinforce the existing prohibition. |
| `CLAIM_COST_REDUCTION` | KEEP PROHIBITED | Unaffected. |
| `CLAIM_CKD_QSVC_INTERNAL` | KEEP | Internal UCI measurement remains valid within its existing scope. Do not connect it to clinical validity or external transport. |
| `CLAIM_CKD_CLASSICAL_INTERNAL` | KEEP | Internal UCI measurement remains valid within its existing scope. |
| `CLAIM_RUNTIME_8` | KEEP | Runtime measurement is unaffected. |

## Claim-family disposition

| Current claim family | Disposition | Required wording boundary |
|---|---|---|
| Raw BD-KDD sensitivity 0.992, specificity 0.010, and AUC 0.525 | KEEP | These are frozen descriptive measurements. Append stress-test scope, PARTIAL target comparability, and the AUC uncertainty where interpreting discrimination. |
| “The model classified almost everyone positive” | KEEP | Directly supported by frozen predictions; do not imply one proven upstream cause. |
| “No quantum performance/runtime/robustness/generalisation advantage was demonstrated” | KEEP | The tested evidence does not support such an advantage. For external performance, cite the paired interval and avoid model ranking. |
| “0.999 internally → 0.525 externally” | KEEP + QUALIFY | Keep as a descriptive tension, but label BD-KDD a cross-cohort stress test and state that 0.525 is indistinguishable from 0.5. It is not a quantum-versus-classical win. |
| Model-family-specific external-collapse wording | REWORD | Both models had random-range external discrimination. Use the exact Phase 3C wording below; do not assign the mechanism to one model family. |
| “External CKD transfer failed severely” / “external generalisation failed” | REWORD | Use “BD-KDD transport was not supported in this cross-cohort stress test.” State PARTIAL target comparability. |
| “Conditional shift” as the decisive or isolated cause | REMOVE/REWORD | Replace causal certainty with **BOTH**: documented target/cohort differences plus changed feature–target relationships. Pure conditional shift was not isolated. |
| “Independent CKD validation,” “independent validation,” or “external validation” for BD-KDD | REWORD | Use “independent BD-KDD cross-cohort transport stress test.” Do not imply like-for-like clinical endpoint validation. |
| “Transportability is disproven generally” | REMOVE | Evidence is limited to the frozen UCI→BD-KDD experiment and cannot establish a universal claim. |
| “QSVC outperformed classical externally” or emphasis on 0.525 > 0.511 | REMOVE / DO NOT ADD | The paired difference CI includes zero. Both model AUC CIs include 0.5. |
| “Scaling/clipping/bounded encoding fixed transport” | REMOVE / DO NOT ADD | All tested configurations include random discrimination; no material rescue occurred. |

## Exact replacement sentence

> External transport failure reflected both target/cohort differences and changed feature–target relationships; therefore the experiment demonstrates transportability risk but cannot isolate pure conditional shift.

For short UI labels, use **“BD-KDD transport not supported”** with the qualifier **“Cross-cohort stress test · target comparability PARTIAL.”**

## Source-by-source audit

The following locations contain claims that require a later, separately approved update. Line numbers refer to the Phase 3C audit state and may shift after edits.

| Location | Current claim/theme | Disposition |
|---|---|---|
| `README.md:24,79,101` | Independent transfer/generalisation and severe external failure framing | REWORD; retain numbers and nearly-all-positive observation |
| `app.py:116,141,332,434` | External generalisation/dashboard verdict | REWORD only the BD-KDD interpretation; retain no-advantage conclusion |
| `src/results_repository.py:243,271,287` | “External generalisation — Failed,” “external CKD transfer stress test,” “did not transfer usefully” | REWORD label/scope to BD-KDD cross-cohort stress test and PARTIAL comparability |
| `research/external_failure_root_cause.md:40,54,98,145,167` | Conditional shift treated as decisive/mechanistic | REWORD as superseded by Phase 3C BOTH classification |
| `research/phase3_decision.md:10` | Failed transport, not confirmation | KEEP + QUALIFY as cross-cohort stress test |
| `research/phase3_results.md:7` | Dataset-shift limitation | REWORD to BOTH wording |
| `research/phase4_decision.md:25,37,61` and `research/phase4_results.md:11,39` | Independent BD-KDD transfer and severe distribution-shift failure | REWORD scope/cause; retain frozen measurements |
| `research/phase5_decision.md:13,37,53,75,83,94` and `research/phase5_results.md:15,19,42` | Pitch hook, external validation, failed transport/generalisation | QUALIFY hook; REWORD external-validation/cause language; retain no-advantage claim |
| `research/final_claims.md:19` | No demonstrated transportability claim | KEEP prohibited/unsupported status |
| `submission/final_claim_review.md:15,17–19` | Robustness/generalisation and external shift claim approval | REWORD external claim; keep `QSVC generalises` prohibited |
| `submission/pitch_story.md:13,23,45` | Independent transfer/generalisation | REWORD to stress-test scope; add random-range CI |
| `submission/five_minute_pitch.md:9,23,31,43–47` | “Independent CKD dataset,” external validation, generalisation | REWORD; retain descriptive 0.999→0.525 hook with qualifier |
| `submission/demo_script_2min.md:11,14–15`, `submission/demo_script_60sec.md:19`, and `submission/demo_backup/` scripts/README | Demo narration of external result | QUALIFY as cross-cohort stress test; do not imply quantum-specific failure |
| `submission/judge_questions.md:9,12–13,24,26,136,158–180,274` | Why external validation failed; validation treated as decisive | REWORD answer to exact Phase 3C BOTH sentence; distinguish stress test from like-for-like validation |
| `submission/quantum_explainer.md:30–32` | External-validation causal answer | REWORD to target comparability PARTIAL + BOTH |
| `submission/quantum_advantage_answer.md:11,15,27,31` | External failure supporting no-advantage verdict | KEEP verdict; qualify BD-KDD evidence and avoid QSVC-vs-SVM ranking |
| `submission/README_SUBMISSION.md:26,73,84,89,115` | Independent CKD transfer and hero | REWORD/QUALIFY |
| `submission/problem_statement_mapping.md:19` and `submission/novelty_statement.md:3` | Independent CKD transfer/shift as delivered validation | REWORD to independent cross-cohort stress test |
| `submission/architecture_spec.md:34,74` | External CKD/validation label | REWORD label only |
| `submission/judging_scorecard.md:16`, `submission/screenshot_pitch_mapping.md:7,12,16`, `submission/screenshots/README.md:7,12,17` | 0.999→0.525 visual hook | KEEP + QUALIFY in captions/narration; screenshots remain historical evidence until UI change is approved |
| `submission/screenshot_validation.md:7,12,17–19` and `submission/reproducibility_check.md:20` | Numeric screenshot validation | KEEP as provenance/visual-validation records; interpretation needs the new qualifier elsewhere |

No handbook-named source or document was present in the repository at audit time.

## Required implementation order after approval

1. Update the registry scope/evidence for `CLAIM_EXTERNAL_AUC`; do not change its measured value.
2. Update the central result-repository/dashboard copy so downstream views use one wording.
3. Update README, research synthesis, pitch, judge answers, demo scripts, and submission copy.
4. Regenerate screenshots and their validation manifests only after the UI wording change is separately approved.
5. Run claim, UI, and frozen-artifact regression tests.

Until those steps are approved, Phase 3C reports—not the older dashboard phrasing—are the controlling interpretation for BD-KDD.
