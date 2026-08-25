# Existing MVP research audit

Scope: read-only audit of `app.py`, `src/evidence.py` and `src/risk_engine.py` on 24 August 2026. **No UI or model code was changed in Phase 0.** The prototype includes caveats, but prominent numbers and confident labels still risk being read as evidence.

## Component decision table

| Existing UI element | Keep | Modify | Remove | Reason |
|---|:---:|:---:|:---:|---|
| Six-feature patient assessment | Shell only | ✓ | Current predictions | The six inputs are a hand-authored heuristic and are not supported by a fitted/nested experiment. “Proposed top-six” and “Six signals. One earlier warning” prematurely fix the answer. Disable predictions or label the entire view static until a stable budget is found. Do not substitute experimental CKD classification for a patient risk probability. |
| Risk cascade (diabetes → heart → kidney) | | | ✓ for research demo | No trained causal/multidisease cascade or joint cohort supports these percentages. Separate disease datasets cannot train a patient-level cascade without a common population/endpoint. The current heart/diabetes logits are illustrative coefficients. Defer beyond Phase 1 unless independently designed and validated. |
| Quantum Evidence Score | Concept of transparent dimensions | ✓ | Scalar score/verdict | The weighted score uses illustrative values, rewards feature count as if clinically meaningful, and can conceal a dominated model. Replace with a measured **Quantum Utility Profile** that displays sensitivity, specificity, AUC, stability, runtime, qubits/depth/shots and noise delta separately. No composite headline or “advantage” verdict. |
| Compression ladder | Ladder structure 24→12→8→6→4 | ✓ | Current 97.2–92.0% bars and “75%” outcome | The ladder is the experiment, not a result. Add selected-versus-PCA tracks and fold uncertainty after runs. Call entries source-variable budgets/dimensions, not compression success or test reduction. |
| Model comparison | Table structure | ✓ | Illustrative metrics as default evidence | Replace only from versioned out-of-fold/final-test artifacts. Show protocol, n, representation, CI and comparability. Do not visually highlight QSVC until the pre-registered selection rule identifies a finalist. |
| Circuit visualisation | ✓ | ✓ | | Render the actual transpiled finalist circuit/configuration from an artifact. Current “six-qubit, ZZ, reps=2” is an untested proposal. Include logical qubits, transpiled depth, two-qubit gates, shots, simulator/backend and fold/config ID. |
| Noise matrix | Structure after evidence exists | ✓ | Current .952/.943/.927/.861/.910 values | Values are illustrative and mix statevector, shots, depolarising and thermal conditions without a complete noise definition. Replace with the pre-specified N0/N1/N2 artifact and intervals; thermal relaxation requires T1, T2 and gate times. |
| Test/cost-saving language | | | ✓ | “6/24,” “18 fewer,” “Test reduction 75%,” “Equivalent care, fewer inputs,” and “cost-saving” are unsupported. A feature is not necessarily a distinct test; multiple features can come from one sample/test and costs were not measured. |
| Risk percentages and High/Moderate/Low label | | | ✓ from any evidence-facing mode | `risk_engine.py` states coefficients are hand-authored. A sigmoid output is not a calibrated CKD probability. Keep only in a clearly separated design mock, never beside research results. |
| Sensitivity target ≥95% | Research goal | ✓ | Claim-like display | Retain only as a pre-registered target/margin with achieved CI shown later. The literature does not make ≥95% a guaranteed model outcome. |
| Apollo location label | | ✓ | “Apollo, Chennai” | Official UCI archive metadata states Apollo Hospitals, Managiri, Madurai Main Road, **Karaikudi, Tamil Nadu**. Correct after Phase 0 review; do not use Chennai. |
| Research disclaimer | ✓ | Strengthen | | Existing disclaimer is valuable. Add “simulated QML,” “not a calibrated patient risk,” dataset version, protocol ID, and artifact timestamp. Caveats should be adjacent to results, not only at the bottom. |

## Specific claims inventory

| Current text/value | Phase 0 status | Required evidence before reuse |
|---|---|---|
| “Six signals. One earlier warning.” | **Unsupported** | Stable-signature rule passes at k=6 plus preserved sensitivity/AUC; “earlier” additionally requires a longitudinal/early-stage endpoint that this dataset does not demonstrate. |
| Patient CKD 0–99% result | **Illustrative heuristic** | A fitted, calibrated, externally validated probabilistic model with a suitable clinical-use definition. This is outside the MVE. |
| “24 → 6” / “75% test reduction” | **Unsupported and conceptually inaccurate** | Feature-ladder result supports six variables; acquisition/test groups and actual costs measured separately. Use “75% fewer source variables” only if supported, never “tests.” |
| QSVC accuracy 95.2%, sensitivity 96.0%, AUC .981 | **Illustrative** | Versioned artifact from the new protocol, CI, sample flow, identical paired baseline and circuit ledger. |
| Random Forest 96.8%, full SVM 95.6%, reduced SVM 94.7%, VQC 91.4% | **Illustrative** | Same artifact requirements and comparability labels. |
| Evidence score and FEATURE-EFFICIENT verdict | **Illustrative/arbitrary weighting** | Remove scalar. Report the underlying measured profile and Pareto dominance only. |
| 1,024-shot/noise accuracies | **Illustrative** | N0/N1/N2 protocol, shot seeds, complete Aer configuration and uncertainty. |
| “Quantum-ready feature path” | **Acceptable only as architecture language** | Must not imply successful quantum model; say “planned simulator evaluation.” |
| “swap for serialized QSVC” | **Premature implementation promise** | Final model decision, serialized preprocessing+model artifact, reproducibility and clear non-clinical boundary. |

## What survives Phase 0

- Visual shell/navigation and research-prototype disclaimer.
- Dataset-audit/benchmark/experiment views as future containers.
- The feature-budget ladder **as an unanswered research question**.
- Side-by-side classical/quantum comparison **when fed by identical versioned artifacts**.
- Circuit/resource visualisation tied to the actually executed configuration.
- A multi-axis evidence profile without a weighted score.

## What must wait or change after review

1. Freeze patient assessment and do not connect Phase 1 experiments to patient-facing probability language.
2. Remove the Risk Cascade from the research story.
3. Replace all illustrative values from a machine-readable run manifest only; before that, show “not run.”
4. Replace “Apollo, Chennai” with the verified Karaikudi/Tamil Nadu provenance.
5. Change “test reduction” to “source-variable budget,” and never infer savings.
6. Present the stable feature signature only if it passes the pre-registered rule; otherwise show the instability finding.
7. Show classical superiority or a null result with equal visual prominence.

## Phase boundary

No changes above are authorised in Phase 0. The existing files remain a prototype shell. Phase 1 should begin only after the dataset choice, hypothesis, compute cap and UI claim policy are approved.

