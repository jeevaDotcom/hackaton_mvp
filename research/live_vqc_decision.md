# Live VQC Decision Freeze

**Decision date:** 26 August 2026  
**Demo decision:** **READY — RESEARCH DEMONSTRATION ONLY**  
**Clinical decision:** **NOT READY**

## Frozen performance decision

**WEAK — DISPLAY WITH CAUTION**

- Sensitivity: **0.640**
- Specificity: **0.567**
- F1: **0.674**
- ROC-AUC: **0.676**
- Training runtime: **34.570 seconds**
- Confusion matrix (TN / FP / FN / TP): **17 / 13 / 18 / 32**

The VQC uses all eight frozen primary UCI variables, eight qubits, `ZFeatureMap(reps=1)`, `RealAmplitudes(reps=1, entanglement="linear")`, COBYLA, and 40 optimizer evaluations. It is a trainable variational circuit and is architecturally distinct from the existing non-trainable feature-map/fidelity-kernel QSVC pipeline.

## Readiness basis

The demonstration is ready because the frozen artifact loads, deterministic live inference runs without retraining, all three actual-record presets work, the local perturbation and anonymised neighbour panels work, same-input VQC/QSVC/RBF decisions and disagreement messaging work, the clinical-review boundary is persistent, seven screenshots exist, and **85 tests pass**.

The model is not ready for clinical use. Its score is not a calibrated disease probability; performance is weak; the 80-record holdout is small and previously used; no prospective validation, clinical-utility study, external VQC validation, or real-hardware validation has been completed. Outputs must remain labelled **Experimental model classification** and **Clinical review required**.

## Frozen operating boundary

- No training, tuning, hyperparameter search, or dataset download occurs in Streamlit.
- No confirmed diagnosis, treatment recommendation, medication recommendation, admission instruction, or referral order is generated.
- Similar UCI records are anonymised research examples, not clinical precedents.
- Raw scores are not compared across VQC, QSVC, and RBF SVM.
- Existing QSVC results and Phase 3C/3D external-transport findings remain unchanged.

Launch with `streamlit run app.py`, then open **http://localhost:8501** and choose **Live Research Assessment**.
