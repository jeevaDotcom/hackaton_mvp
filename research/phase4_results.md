# Phase 4 Results — Q-CARE Evidence-First Platform

## Outcome

Phase 4 replaces the prototype screening interface with **Q-CARE — Evidence-First Hybrid Quantum Healthcare Benchmarking Platform**. The application is now a deterministic research workspace built around frozen Phase 1–3 artifacts. It neither accepts patient measurements nor emits a diagnosis, probability, referral, or treatment recommendation.

The final narrative is deliberately evidence-led:

> **Internal stability → stress testing → external transportability audit**

The strongest internal QSVC result was 0.985 sensitivity and 0.999 ROC-AUC on repeated UCI CKD cross-validation. Phase 3C later established that both frozen models were indistinguishable from random discrimination on BD-KDD and that target comparability was PARTIAL. External transport failure reflected both target/cohort differences and changed feature–target relationships; therefore the experiment demonstrates transportability risk but cannot isolate pure conditional shift.

## Delivered information architecture

1. **Overview** — research question, six artifact-backed headline measures, and the core shift story.
2. **CKD Benchmark Lab** — dataset provenance, stable feature signatures, feature stability, repeated classical/QSVC comparison, feature budgets, PCA comparison, and experiment replay.
3. **Robustness & Shift Lab** — missingness, measurement perturbation, training-size experiments, and the BD-KDD cross-cohort stress test.
4. **Cross-Disease Validation** — separate CKD, Cleveland heart-disease, and Pima diabetes results without averaging incompatible tasks.
5. **Quantum Evidence Explorer** — evidence matrix, real frozen Qiskit circuit, runtime, finite-shot evidence, claim registry, and final verdict.

## Artifact-driven implementation

`src/results_repository.py` is the single results layer. It loads the final model manifest, Phase 1–3 summaries, robustness artifacts, cross-disease outputs, circuit metadata, and the claim registry. UI metrics are derived from this repository rather than copied throughout `app.py`.

The experiment replay is lookup-only. Its dataset, representation, budget, and model controls return existing sensitivity, specificity, F1, ROC-AUC, runtime, qubit count, circuit depth, tolerance, protocol, and source artifact. It does not retrain a model or require IBM Quantum connectivity.

## Claim control

`artifacts/claim_registry.json` connects every headline claim to a metric source, artifact, and permitted wording. Registry validation passes with no errors. It explicitly rejects clinical-grade performance, quantum superiority, and cost-reduction wording.

Supported conclusions are limited to the evidence:

- Stable reduced CKD representations were identified.
- QSVC was internally competitive within the predefined 0.05 descriptive tolerance at eight and six variables.
- Classical SVM was slightly stronger under repeated resampling.
- Selected clinical variables outperformed matched-dimension PCA for QSVC.
- Classical SVM was more robust to added missingness and measurement perturbation.
- No small-sample QSVC advantage appeared.
- Neither model retained reliable discrimination on BD-KDD; target comparability was PARTIAL and all eight feature-label relationships flattened.
- Heart-disease method transfer was mixed and diabetes transfer was poor.
- The platform reports positive, neutral, inconclusive, and negative quantum findings.

## Quantum configuration and runtime

The application renders the actual frozen Qiskit feature map:

- `ZFeatureMap`
- `reps=1`
- eight qubits primary, six qubits secondary
- depth two
- no entanglement

The note beside the circuit states that added circuit complexity did not improve the evidence in this experiment without generalising that result beyond the tested configuration.

At matched clinical budgets, exact local statevector evaluation made QSVC approximately 464× slower at eight variables and 477× slower at six. The interface explicitly says this does not demonstrate a hardware speed-up.

## Removed prototype elements

The pre-deletion audit is preserved in `research/phase4_ui_audit.md`. The final application removes patient inputs, risk percentages, diagnosis-like output, clinical recommendations, treatment/referral language, test-saving and cost-saving claims, the 75% diagnostic reduction claim, multi-disease patient risk cascades, illustrative metrics, the fabricated weighted quantum evidence score, and inaccurate circuit or provenance descriptions.

## Design and responsible use

The visual system follows a restrained scientific-instrument concept: off-white paper, dark ink, one cobalt accent, generous spacing, chart-led evidence, and consistent verdict labels. The layout was checked at desktop and 390 px mobile widths. A persistent footer states that Q-CARE is a research prototype and is not intended for diagnosis, treatment, clinical decision-making, or patient triage.

## Verification

- Automated suite: **57 tests passed**.
- Claim registry: **valid**.
- Source audit: no prohibited patient-risk or promotional claims in application source.
- Browser QA: all five pages rendered without application exceptions; replay controls changed the displayed frozen result; the evidence-summary download was present; desktop and mobile layouts were inspected.
- Offline demo: uses local dependencies and precomputed artifacts only.

## Run

```bash
.venv/bin/streamlit run app.py
```

During final QA the live local instance was served at `http://localhost:8502` because port 8501 was already occupied.

## Phase boundary

No pitch deck was created in Phase 4.
