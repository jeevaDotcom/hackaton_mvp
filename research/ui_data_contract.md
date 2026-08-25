# UI data contract

This contract is for the later application phase; Phase 3 makes no Streamlit changes.

## Accepted model input

Primary ordered fields: `hemo, al, dm, sg, pcv, appet, htn, sc`. Optional compact fields: `hemo, al, dm, sg, pcv, appet`. Numeric values use source units; categorical values must use the frozen vocabularies (`yes/no`, `good/poor`). Missing values may be null and are handled by the bundled training-fitted imputer.

## Returned result

```json
{
  "model_id": "qsvc_ckd_8_z_reps1_c0.5",
  "output_category": "class_and_decision_score",
  "predicted_class": 0,
  "class_label": "not_ckd_pattern",
  "decision_score": -0.42,
  "threshold": 0.0,
  "research_only": true,
  "warnings": ["Not a diagnosis", "Not a calibrated clinical probability"]
}
```

Never convert the score to a percent, label it “risk,” or hide the matched classical result. Display the model/version, source cohort, missing fields, and research-only warning. Aggregate robustness and external-shift evidence may be shown from frozen report tables. Individual explanations, if later added, must be labeled model sensitivity—not causal contribution.

## Explainability

Allowed: model-agnostic perturbation/sensitivity of the signed score, with direction and magnitude labelled as model behaviour. Required limitation: it is neither causal contribution nor clinical importance. Do not infer treatment or physiology from it.

## Frozen benchmark sources

- Development repeated CV: `artifacts/phase3/reference_cv_summary.csv` and `reference_cv_paired.csv`.
- Already-frozen shared test: `artifacts/phase2_locked_test_evaluation.json`; display-only, never threshold/tuning input.
- Robustness/calibration/external/cross-disease: corresponding CSV files under `artifacts/phase3/`.
- Exact model identity and file hashes: `artifacts/final_model_manifest.json`.

## Quantum/resource fields

Eight inputs use 8 qubits, logical depth 2, and 16 decomposed feature-map gates. Six inputs use 6 qubits, logical depth 2, and 12 gates. Runtime must be labelled local exact statevector benchmark time, never hardware runtime or speed-up. Display the measured classical/QSVC values from the frozen artifact, not hard-coded marketing copy.

## Wording

Allowed: “experimental,” “research prototype,” and “decision-support research.” Disallowed: diagnosis, confirmed disease, clinical recommendation, treatment advice, clinical probability, quantum advantage, hardware-ready, or production-ready.
