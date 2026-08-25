# Phase 4 UI audit

Audit scope: every page, control, metric, sentence family, visual component, and data source in the 206-line Phase 0 Streamlit prototype, reviewed before replacement.

## Global shell and visual system

| Existing element | Decision | Rationale / required change |
|---|---|---|
| Wide Streamlit layout | KEEP | Appropriate for evidence tables and scientific charts. |
| Dark sidebar navigation | MODIFY | Retain restrained navigation, rename all pages to the final five-page architecture, and add persistent research-prototype limitations. |
| Manrope + DM Mono typography | KEEP | Clear research/editorial hierarchy; use a local/system fallback so offline demo mode does not depend on Google Fonts. |
| Paper, ink, cyan visual palette | MODIFY | Preserve the calm laboratory character but move to a single cobalt evidence accent and consistent status colours. |
| Metric blocks with top rules | KEEP | Useful for artifact-backed evidence; every value must come from the repository layer. |
| Animated horizontal bars | MODIFY | Use only for measured comparisons, never patient risk or invented performance. Respect reduced-motion preferences. |
| Tags such as “ILLUSTRATIVE TARGETS” | REMOVE | Phase 4 prohibits illustrative numbers entirely. |
| Page headers and generous spacing | KEEP | Strong hierarchy; rewrite copy as research utility language. |

## Page 1 — Patient assessment

| Existing element | Decision | Rationale / required change |
|---|---|---|
| “Six signals. One earlier warning.” headline | REMOVE | Suggests a clinical screening workflow and unsupported sufficiency of six inputs. |
| Patient-entry controls for blood pressure, creatinine, haemoglobin, albumin, glucose, and diabetes | REMOVE | Patient-specific screening is prohibited. |
| Heuristic `PatientInputs → RiskResult` engine | REMOVE | Hand-authored coefficients have no place in the evidence platform. |
| CKD percentage, HIGH/MODERATE/LOW label, and “top contributors” | REMOVE | Fabricated patient risk and diagnosis-like output. |
| Diabetes → heart → kidney “risk cascade” | REMOVE | Unsupported multi-disease patient workflow. |
| “Inputs used 6/24; 18 fewer” | REMOVE | Implies clinical sufficiency and test reduction. |
| “Test reduction 75%” | REMOVE | Unsupported cost/test-saving claim. |
| “Sensitivity target ≥95%” | REMOVE | Illustrative target rather than measured evidence. |
| Prototype disclaimer | MODIFY | Replace with a persistent responsible-use footer covering diagnosis, treatment, triage, prospective validation, and hardware limits. |

## Page 2 — Model comparison

| Existing element | Decision | Rationale / required change |
|---|---|---|
| “Equivalent care, fewer inputs.” | REMOVE | Unsupported equivalence/clinical-care claim. |
| Illustrative Random Forest, SVM, QSVC, and VQC table | REMOVE | Every number is fake and model configurations are outdated. |
| Highlighted `QSVC · ZZ` row | REMOVE | Frozen winner is `ZFeatureMap`, reps=1, no entanglement. |
| Illustrative 24/12/8/6/4 compression ladder | REMOVE | Replace with artifact-backed feature-budget results and mark 4 variables as a non-retained stress test. |
| General paired-comparison concept | KEEP | Rebuild as CKD Benchmark Lab using Phase 1–3 artifacts only. |

## Page 3 — Quantum evidence

| Existing element | Decision | Rationale / required change |
|---|---|---|
| Weighted “Composite evidence” score | REMOVE | Fabricated weighting conceals evidence dimensions and is explicitly replaced by a matrix. |
| `FEATURE-EFFICIENT` verdict | REMOVE | Derived from illustrative values, not the frozen claim registry. |
| Accuracy/sensitivity/feature/runtime/noise scorelines | MODIFY | Retain the dimensions but show measured values and categorical evidence verdicts separately. |
| Statement to “advance only if ≥95% sensitivity” | REMOVE | Post-hoc development gate and screening-oriented framing. |
| Visible code-weight explanation | REMOVE | No weighted score remains. |

## Page 4 — Technical details

| Existing element | Decision | Rationale / required change |
|---|---|---|
| Five-stage pipeline visual | MODIFY | Keep the workflow concept; correct provenance, methods, and frozen model choices. |
| “Apollo Hospitals, Chennai” | REMOVE | Incorrect. Source metadata reports Apollo Hospitals, Karaikudi, Tamil Nadu. |
| Permutation-only ranking and 12-feature ladder | MODIFY | Use actual stability protocol and retained 8/6 budgets. |
| “PCA / scaling; ZZFeatureMap” | REMOVE | Frozen primary representation is clinical; feature map is non-entangling ZFeatureMap. |
| Hand-drawn entangled six-qubit circuit, reps=2 | REMOVE | Scientifically wrong for the final configuration. Replace with a real Qiskit-rendered ZFeatureMap, reps=1 circuit. |
| Illustrative noise matrix | REMOVE | Replace with frozen finite-shot/noise artifacts. |
| “Pima … non-Indian clinical-source data” | MODIFY | State precisely that it represents women of Pima heritage near Phoenix, Arizona and is not an Indian-population dataset. |
| Provenance links | KEEP | Rebuild from traceable artifact metadata and authoritative URLs. |

## Sidebar and navigation

| Existing element | Decision | Rationale / required change |
|---|---|---|
| `Q-CARE / EGREEN QUANTA` brand | MODIFY | Use final name: Q-CARE, Evidence-First Hybrid Quantum Healthcare Benchmarking Platform. |
| Four old navigation entries | REMOVE | Replace with Overview, CKD Benchmark Lab, Robustness & Shift Lab, Cross-Disease Validation, Quantum Evidence Explorer. |
| “Prototype · validation pending” | MODIFY | Phase 3 is complete; use “Research prototype · evidence frozen.” |
| “CKD · Apollo, Chennai” | REMOVE | Wrong location and too narrow for the cross-disease platform. |

## Code and data dependencies

| Existing element | Decision | Rationale / required change |
|---|---|---|
| `src/risk_engine.py` | REMOVE | Patient-specific heuristic is prohibited and will no longer be imported. |
| `src/evidence.py` weighted score | REMOVE | Replaced by an artifact-backed evidence matrix and claim registry. |
| Hard-coded metrics throughout `app.py` | REMOVE | Replace with `src/results_repository.py` as the only UI results layer. |
| No downloadable report | MODIFY | Add a deterministic Markdown evidence-summary download. |
| Live calculations on interaction | MODIFY | Experiment Replay must be lookup-only and offline; no QSVC retraining or cloud dependency. |

## Final audit decision

The visual foundation is reusable, but the old product logic and nearly all scientific content must be replaced. No patient-entry, risk, recommendation, illustrative-performance, weighted-score, entanglement, cost-saving, or diagnosis-like element is retained.
