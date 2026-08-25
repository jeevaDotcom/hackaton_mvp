# Novelty and research-gap analysis

Research cut-off: 24 August 2026. “Not found” means **not found in the reviewed literature**, not proof that no such work exists. The search focused on exact UCI CKD studies and then exact Cleveland/Pima studies to check whether the proposed evaluation patterns are already routine in biomedical QML.

## Candidate-hypothesis verdict

The original question—whether QML can classify CKD after feature reduction—is **not novel enough by itself**. Exact UCI CKD papers already combine feature selection or PCA with QSVM/QSVC/VQC/QNN. One 2025 study directly compares PCA+CSVM with PCA+QSVM, and a 2026 preprint explores hundreds of hybrid circuit/shot configurations.

The defensible project is a **methodological benchmark**:

> Under leakage-free nested resampling, how do classical SVM and quantum-kernel SVC change across identical, clinically interpretable feature budgets, and are the selected variables stable enough that the result is more than one lucky subset? At matched dimensions, does PCA change that trade-off?

This is a preservation/non-inferiority investigation, not an advantage claim. “Quantum utility” should be a vector of measured outcomes, not a fabricated scalar score.

## A–M prior-work classification

| ID | Idea | Status | Evidence and boundary |
|---|---|---|---|
| A | CKD + QSVC | **DONE EXTENSIVELY** | Sridevi 2025, Hossain 2025 and Shinde 2026 all use the exact UCI CKD data with a QSVM/QSVC-like model. |
| B | CKD + VQC/QNN | **DONE PARTIALLY** | Parthasarathi 2025 reports VQC; Sridevi 2025 reports QNN; Kashif 2026 explores HQNNs. Reproducibility and fair paired baselines remain weak. |
| C | CKD + quantum kernel | **DONE EXTENSIVELY** | Multiple QSVM/QSVC studies use angle/Pauli/fidelity kernels on the same 400-row data. |
| D | CKD + feature selection + QML | **DONE EXTENSIVELY** | Top-eight filters/trees (Sridevi), LASSO-13 (Parthasarathi), and classical cost/SHAP selections already exist. |
| E | CKD + PCA + QML | **DONE PARTIALLY** | Hossain compares PCA/SVD with QSVM/CSVM; Kashif uses PCA to eight. The exact retained dimensions and leakage controls are not consistently transparent. |
| F | Exact feature ladder 24→12→8→6→4 | **NOT FOUND IN REVIEWED LITERATURE** | Individual reduced subsets exist, but no reviewed exact-CKD study pre-registers this entire source-variable budget ladder with paired uncertainty. The sequence itself is only a design device, not a scientific contribution. |
| G | Interpretable selected variables vs PCA latent variables at matched dimensions for QML | **RARE** | PCA/SVD and selected-variable studies exist separately. A fold-internal, matched-dimension, selected-vs-PCA comparison using the same SVM/QSVC folds was not found. |
| H | Classical SVM/XGBoost and QSVC/VQC on identical subsets | **DONE PARTIALLY** | Sridevi pairs SVM/QSVM on one top-eight subset; Parthasarathi reports several models after LASSO. A full budget ladder with common tuning/evaluation and an XGBoost full-feature reference was not found. |
| I | Feature-selection stability across CV folds combined with QML | **NOT FOUND IN REVIEWED LITERATURE** | Feature importance is reported, but selection frequency, rank uncertainty and formal stability across outer folds are absent from the reviewed CKD QML papers. |
| J | Noise-aware CKD QML | **DONE PARTIALLY** | Hossain injects 1–5% synthetic noise; recent hybrid work studies robustness/design. A pre-specified calibrated Aer noise model paired with circuit resources and clinical metrics remains underdeveloped. |
| K | Shot-count sensitivity | **DONE PARTIALLY** | Kashif's 625-model design space includes five shot settings. Repeating a shot sweep alone is not novel. |
| L | Performance versus training-set size | **DONE PARTIALLY** | Hossain includes a dataset-size analysis. Learning curves alone are not a sufficient gap. |
| M | Multidimensional quantum utility | **DONE PARTIALLY** | Kashif uses a composite performance score including predictive dimensions. A transparent profile spanning sensitivity, feature efficiency, generalisation, runtime and noise remains useful, but turning it into another arbitrary headline scalar is not novel or defensible. |

## Existing-study gap matrix

| Existing study | Dataset | What they did | What they did not do | Our possible difference | Meaningful? | How we test it |
|---|---|---|---|---|---|---|
| Sridevi et al. 2025 | UCI CKD | Same top-eight variables for SVM and QSVM; QNN; AUC and runtime | No fold-wise selection stability; feature selection appears pre-split; no PCA match; incomplete clinical metrics/noise/shots | Select inside outer-training data at 12/8/6/4, pair SVM/QSVC on exactly the same folds and transforms | **Yes—removes a major source of optimistic bias** | Repeated nested CV; locked final test; paired deltas and selection-frequency plots |
| Parthasarathi et al. 2025 | UCI CKD | LASSO-13, sparse-autoencoder balancing, VQC and classical comparisons | Evaluation boundary, augmented n, qubits and shots unclear; no stability; no matched PCA | No augmentation in primary analysis; transparent source-variable groups; VQC only as a feasible secondary model | **Yes—reproducibility and leakage resistance** | Pipeline audit tests; model cards; compare primary estimates with/without inner-fold-only resampling as sensitivity analysis |
| Hossain et al. 2025 | UCI CKD | PCA/SVD + CSVM/QSVM, 5-fold results, runtime, synthetic noise, sample-size analysis | No clinically interpretable subset at the same dimensions; unclear quantum resource details; no nested selection stability | Selected variables vs PCA at 8/6/4 with identical models and folds; publish resource ledger | **Yes—separates interpretability from latent compression** | Paired outer-fold SVM and QSVC deltas at each dimension; depth/kernel-call/runtime table |
| Shinde et al. 2026 | UCI CKD | Angle and Pauli QSVM versus classical SVM; 99–100% accuracy/F1 | Insufficient accessible split/resource detail; no uncertainty or reduction ladder | Reproducible protocol and confidence intervals, with null result welcomed | **Yes scientifically, modest algorithmically** | Versioned config, fixed seeds, bootstrapped/pairwise uncertainty, no advantage language |
| Kashif et al. 2026 preprint | Four CKD variants including UCI | 625 HQNNs; encodings, entanglement, bases and shots; CV and composite score | No stable interpretable signature vs PCA; many-way winner selection; not a clinical-metric/resource profile | Small pre-registered circuit set after classical feasibility screen; preserve all utility dimensions separately | **Yes—reduces researcher degrees of freedom** | Pre-register 2 feature maps × 2 reps × 3 shot regimes only on selected finalist budgets; never tune on final test |
| Rashed-Al-Mahfuz et al. 2021 | UCI CKD | Strong full classical models, SHAP top-13 and clinical grouping | No QML; reduced selection not independently nested; stability not quantified | Treat RF/XGBoost as ceiling references and evaluate selector stability | **Yes—stronger baseline and honest feature evidence** | Full-24 LR/RF/XGB/SVM plus nested MI/RFECV/permutation ranks |
| Ali et al. 2020 | UCI CKD | Cost-sensitive ranking and roughly six-feature solutions | Costs imported/assumed; feature count conflated with acquisition cost risk; no QML | Do not claim test or money savings; report only variable budget and, if later available, empirically sourced acquisition groups | **Yes clinically** | MVP language audit; no cost endpoint in primary experiment |
| Abdulsalam et al. 2023 | Cleveland | RFE/PCA with SVM, QSVC, QNN, VQC and bagging-QSVC | Selection appears pre-split; unequal model protocols; no stability | Apply the same nested template as a compact cross-disease reproducibility check | **Moderate** | Run only after CKD MVE; do not pool disease results |
| Khan et al. 2025 | Pima | 76 VQC variants, 4/8 features/qubits, several maps/optimizers/layers and mitigation | Different geography; many-way selection; no CKD stability question | Shows resource sweeps are prior art and Pima adds little India relevance | **No as primary novelty** | Keep only as contextual benchmark; prefer West Bengal cohort if schema passes |

## Top three opportunities

Scoring: 1 = weak/low, 5 = strong/high. For **risk**, 5 means high risk (worse). “24–36 h” scores the chance of obtaining an interpretable result, including a defensible null result—not the chance of beating classical ML.

| Rank | Opportunity | Novelty | Defensibility | Clinical relevance | Quantum relevance | Feasibility | Demo potential | Risk | Measurable in 24–36 h | Total excluding risk |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **Leakage-resistant feature-budget benchmark plus fold-wise feature stability** | 4 | 5 | 5 | 4 | 5 | 5 | 2 | 5 | 38/40 |
| 2 | **Matched-dimension interpretable variables versus PCA for SVM and QSVC** | 4 | 5 | 4 | 5 | 4 | 5 | 3 | 4 | 35/40 |
| 3 | **Resource-aware utility profiles for finalist reduced configurations under ideal, finite-shot and calibrated toy noise** | 3 | 4 | 3 | 5 | 3 | 5 | 4 | 3 | 30/40 |

### 1. Strongest: stability-aware, leakage-free feature budgets

Scientific contribution: quantify whether a reduced CKD signature is reproducible across folds and selectors while comparing SVM and QSVC under identical data. This tests a clinically meaningful prerequisite that existing QML accuracy papers generally omit.

Falsifiable outputs:

- frequency/rank/stability of each clinical variable at 12/8/6/4;
- sensitivity, specificity and ROC-AUC degradation from full models;
- paired QSVC–SVM differences and confidence intervals at every common subset;
- explicit evidence that a six-feature configuration is stable, unstable or unsupported.

### 2. Second: interpretable versus latent compression

Scientific contribution: at 8/6/4 dimensions, isolate whether QSVC behavior comes from feature count alone or from the representation. The selected-variable track preserves source-variable meaning; PCA does not. Neither is presumed superior.

Falsifiable output: paired selected-minus-PCA deltas for SVM and QSVC, plus stability (selected track), explained variance (PCA), runtime and circuit resources.

### 3. Third: quantum utility profile, not score

Scientific contribution: document predictive trade-offs against finite-shot variance, transpiled depth/two-qubit gates, kernel evaluations and runtime on only the finalist budgets. Recent work means this is incremental unless tied to the stable-signature experiment.

Falsifiable output: a Pareto/profile plot. No weighted scalar and no “quantum advantage” badge.

## Measurable hypothesis

Primary, pre-registered hypothesis:

> On the UCI CKD dataset, at least one fold-internally selected **8- or 6-source-variable** signature will have selection frequency ≥0.80 for a core subset and will retain sensitivity and ROC-AUC within absolute margins of **0.05** of the corresponding full-feature classical reference under repeated nested cross-validation. Under the identical reduced inputs and outer folds, QSVC will be reported as non-inferior only if the lower confidence bound for (QSVC − RBF-SVM) is above **−0.05** for both sensitivity and ROC-AUC; no superiority is assumed.

Important qualification: the full-feature reference differs by model family, and the locked 80-row test is too small to establish clinical non-inferiority on its own. The margins are hackathon research criteria, not clinically validated margins.

## Decision on the current concept

**MODIFY.** Keep the Indian CKD dataset, feature-budget story, classical/quantum side-by-side comparison and real circuit/resource visualization. Replace the assumed “Adaptive Quantum Feature Compressor,” six-feature answer, 75% claim and scalar evidence score with a pre-registered experiment whose result may be negative. A credible finding that classical SVM is better, or that no six-feature signature is stable, still completes the research question.

