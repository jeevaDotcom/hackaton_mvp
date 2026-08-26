# Live VQC Research Demonstration — Results

Frozen on **26 August 2026**. This is an additional research demonstration; it does not replace the matched RBF SVM/QSVC benchmark or alter the Phase 3C/3D external-transport interpretation.

## Model and data contract

| Item | Frozen value |
|---|---|
| Training data | UCI Chronic Kidney Disease only |
| Split | Existing 320-record development split; evaluation on the existing 80-record holdout |
| Input features | `hemo`, `al`, `dm`, `sg`, `pcv`, `appet`, `htn`, `sc` |
| Representation | Validated eight-variable clinical representation; no dimensional-reduction fallback |
| Qubits | 8 |
| Feature map | `ZFeatureMap`, 1 repetition |
| Ansatz | `RealAmplitudes`, 1 repetition, linear entanglement |
| Optimizer | COBYLA |
| Iteration/evaluation budget | 40 |
| Training runtime | 34.570 seconds |
| Frozen score threshold | 0.5 |

QSVC and VQC are genuinely different architectures. The existing QSVC combines a non-trainable quantum feature map, fidelity kernel, and classical SVM. The added VQC learns the parameters of a variational quantum circuit through a classical COBYLA optimizer.

The trained Qiskit VQC model, 16 learned circuit weights, preprocessing object, feature order, metadata, metrics, reference records, presets, circuit rendering, and training trace are persisted under `artifacts/live_vqc/`. The Streamlit path never trains or tunes a model. Live scoring executes the saved circuit and weights through a small deterministic exact statevector implementation. This avoids a macOS native Qiskit/PyO3 deserialization fault in Streamlit worker threads while preserving the frozen circuit mathematically; an isolated comparison matched Qiskit's exact statevector output to `1.11e-16` absolute error.

## Held-out performance

The table reports the frozen evaluation produced with the persisted Qiskit VQC and a seeded 4,096-shot `StatevectorSampler`. These scores are circuit class weights, not calibrated disease probabilities. The holdout had already been used in earlier project phases and is not prospective clinical validation.

| Model | Sensitivity | Specificity | F1 | ROC-AUC | Confusion matrix (TN / FP / FN / TP) |
|---|---:|---:|---:|---:|---:|
| VQC | 0.640 | 0.567 | 0.674 | 0.676 | 17 / 13 / 18 / 32 |
| Existing RBF SVM comparator | 0.980 | 1.000 | 0.990 | 1.000 | 30 / 0 / 1 / 49 |
| Existing QSVC comparator | 1.000 | 1.000 | 1.000 | 1.000 | 30 / 0 / 0 / 50 |

VQC accuracy was **0.613**, precision **0.711**, and PR-AUC **0.789**. Its frozen performance decision is **WEAK — DISPLAY WITH CAUTION**. The comparator results are shown transparently; VQC does not need to beat them to demonstrate a live trainable quantum-classifier architecture.

## Live workflow validation

| Required capability | Result | Evidence |
|---|---|---|
| Frozen live inference | PASS | Streamlit `AppTest` executed Analyse with zero exceptions; deterministic thread-level inference returned score `0.509454` |
| Local perturbation explanation | PASS | Holds other inputs fixed, moves each feature to the development median/mode, reruns the frozen circuit, and ranks the top five absolute score changes |
| Nearest-record retrieval | PASS | Uses the frozen preprocessor and eight-feature Euclidean distance; returns up to five anonymised UCI development records or an explicit no-match message |
| Model-agreement panel | PASS | Displays VQC, existing QSVC, and existing RBF SVM decisions without comparing incompatible raw score scales |
| Clinician review checklist | PASS | Six generic verification/context prompts; no treatment, medication, admission, or referral order |
| Presets | PASS | Three complete profiles copied from actual UCI development records |
| Circuit explainer | PASS | Plain-language five-step explanation plus the real persisted eight-qubit circuit rendering |
| Research boundary | PASS | Persistent research-prototype notice; score explicitly labelled as not a calibrated disease probability |

For the default borderline/mixed dataset preset:

- entered profile: haemoglobin 14.6 g/dL, albumin 0, diabetes no, specific gravity 1.020, packed cell volume 44%, appetite good, hypertension no, serum creatinine 1.0 mg/dL;
- VQC output: **Pattern closer to CKD class**, score **0.509454**;
- strongest local model influence: haemoglobin, absolute score change **0.214**;
- five closest stored records were all labelled non-CKD in the research dataset;
- VQC classified toward the CKD class while QSVC and RBF SVM classified toward the non-CKD class, producing **2 OF 3 AGREE** and the visible disagreement caution.

This example deliberately exposes uncertainty; it is not a diagnosis or a fabricated ideal case.

## Visual and automated evidence

Seven final-UI screenshots are stored in `submission/screenshots/`:

1. `live_01_patient_entry.png`
2. `live_02_vqc_result.png`
3. `live_03_factor_explanation.png`
4. `live_04_similar_records.png`
5. `live_05_model_comparison.png`
6. `live_06_review_checklist.png`
7. `live_07_quantum_circuit.png`

The complete repository suite passed **85 tests**. The live-specific coverage includes artifact integrity, feature order, preprocessing consistency, categorical encoding, reproducible prediction, worker-safe frozen-circuit execution, anonymised nearest records, ranked perturbations, actual-record presets, agreement logic, prohibited diagnostic/directive copy, the no-retraining inference boundary, frozen performance, and architecture differentiation.

## Run and decision

Run `streamlit run app.py`, open **http://localhost:8501**, and select **Live Research Assessment**. If port 8501 is occupied, use the localhost URL printed by Streamlit.

**READY — RESEARCH DEMONSTRATION ONLY.**

Clinical readiness remains **NOT READY** because discrimination is weak, the score is uncalibrated, the holdout is small and previously used, external VQC transportability is untested, and no prospective or clinical validation exists.
