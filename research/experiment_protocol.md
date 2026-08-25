# Pre-registered experiment protocol

Status: Phase 0 design only; no model results exist yet. Primary dataset: UCI CKD v1, DOI [10.24432/C5G020](https://doi.org/10.24432/C5G020). This protocol deliberately prioritises paired fairness, leakage prevention and uncertainty over a high headline accuracy.

## 1. Research questions and endpoints

1. Can a stable, interpretable 12/8/6/4-source-variable CKD signature preserve predictive performance relative to full-variable classical references?
2. At matched source-variable/dimension budgets and on identical folds, how does an RBF-SVM compare with QSVC?
3. At 8/6/4 dimensions, how do selected clinical variables compare with PCA latent dimensions for each model?
4. Are any observed quantum results robust to seeds, finite shots and the limited noise/resource study in `quantum_resource_protocol.md`?

Primary metrics:

- **Sensitivity:** missed CKD cases are the central model error, so true-positive rate is co-primary.
- **Specificity:** prevents a sensitivity-only threshold from labeling nearly everyone CKD.
- **ROC-AUC:** threshold-independent ranking quality, reported with uncertainty; not sufficient alone.

Secondary metrics: accuracy, precision, F1, PR-AUC, balanced accuracy, Brier score/calibration intercept and slope where estimable, and runtime. PR-AUC exposes positive-class performance under prevalence; runtime establishes the computational trade-off. No metric implies clinical utility without external validation.

## 2. Data contract and immutable audit

- Pin the official archive version, retrieval date and SHA-256.
- Expect exactly 400 rows, 24 source predictors and one binary label; 250 CKD/150 not-CKD.
- Trim leading/trailing spaces and tabs; normalise documented spelling variants; reject rather than shift records with unexpected column counts.
- Store a reconciliation log for the two trailing delimiters and one malformed categorical field seen in the official ARFF.
- Convert `?` and a schema-approved blank to missing only after preserving the raw token.
- Test allowed domains for `sg`, `al`, `su`, `rbc`, `pc`, `pcc`, `ba`, `htn`, `dm`, `cad`, `appet`, `pe`, `ane` and label.
- Check exact duplicates and label conflicts. A duplicate patient identifier is absent, so any identical rows will be reported and grouped into the same split as a conservative sensitivity analysis.
- Never use missingness or cleanup information from held-out outcomes. Missing indicators may be included only as a pre-registered sensitivity analysis because site workflow may itself encode the label.

## 3. Split and resampling design

### Locked test

Create one stratified 20% holdout (expected n=80, approximately 50 CKD/30 non-CKD) with seed 20260824. Save only row indices and label counts. Do not inspect its feature distributions by class, tune thresholds, select features or choose a winning model against it.

Why retain a test despite n=400: it gives one untouched final check after model selection. Why not rely on it: an 80-row test has wide confidence intervals, so it cannot prove clinical equivalence. The repeated nested-CV estimates on development data remain the main model-development evidence.

### Development evaluation

- Development set: remaining 80% (expected n=320).
- Outer evaluation: repeated stratified 5-fold CV × 5 repeats using split seeds `[11, 29, 47, 71, 101]` (25 outer assessments).
- Inner selection/tuning: stratified 4-fold CV within each outer-training partition. Inner splitter seed is a deterministic hash of outer repeat/fold and is logged.
- Hyperparameter selection uses mean inner ROC-AUC, with sensitivity as the first tie-break and lower complexity as the second.
- After the full protocol and model family are frozen, refit the selected pipeline on all development rows and evaluate the locked test once.

If compute limits prevent the complete quantum schedule, run the Minimum Viable Experiment below without changing the folds. Never substitute an easier split after observing results.

## 4. Fold-contained preprocessing

Every step below is fit on the current inner/outer training partition and applied unchanged to validation/test rows.

1. **Schema cleaning:** deterministic token cleanup only; no statistics.
2. **Types:**
   - Numeric: age, bp, bgr, bu, sc, sod, pot, hemo, pcv, wc, rc.
   - Ordered discrete: sg, al, su, encoded in their documented clinical order.
   - Binary nominal: rbc, pc, pcc, ba, htn, dm, cad, appet, pe, ane.
3. **Imputation:** median for numeric/ordered fields and most-frequent for nominal fields. No forward-fill because row order is not a patient time series. Tune/compare iterative imputation only as a later sensitivity analysis.
4. **Encoding:** one-hot encode nominal fields with unknown categories ignored. Track feature groups so one source variable and all its dummy columns move together during selection.
5. **Scaling:** StandardScaler for LR/SVM/PCA pathways, fit after imputation/encoding. Tree models receive imputed encoded values without unnecessary scaling.
6. **Quantum angle scaling:** after selection/PCA, a fold-fitted MinMax transform maps each dimension to `[0, π]`. The paired classical SVM receives **the same quantum-scaled matrix** in the primary SVM–QSVC comparison. A standard-scaled SVM is a labelled sensitivity analysis.

The “24 features” ladder refers to **24 source clinical variables**, not the larger number of one-hot columns.

## 5. Model families

### Full-source-variable classical references

Run all 24 source variables:

- Logistic regression: `C ∈ {0.01, 0.1, 1, 10}`, L2, `class_weight ∈ {None, balanced}`.
- RBF-SVM: `C ∈ {0.1, 1, 10}`, `gamma ∈ {scale, 0.01, 0.1, 1}`, `class_weight ∈ {None, balanced}`; probability calibration occurs inside training data.
- Random Forest: trees `{300, 600}`, max depth `{None, 4, 8}`, min leaf `{1, 3, 5}`, `class_weight ∈ {None, balanced_subsample}`.
- XGBoost, if installed and version-pinned: trees `{200, 400}`, depth `{2, 3, 5}`, learning rate `{0.03, 0.1}`, subsample/column sample `{0.8, 1.0}`, `scale_pos_weight ∈ {1, n_neg/n_pos}`. If unavailable, HistGradientBoosting is reported as a separately named replacement—not silently called XGBoost.

The grid may be pruned *before* outcome inspection by a timed dry run. Any pruning is logged.

### Track A: interpretable feature selection

Budgets: 12, 8, 6 and 4 source variables. Candidate selectors are independently evaluated, not blended post hoc:

- mutual information, estimated only on inner-training data;
- RFECV using logistic regression or linear SVM, with an inner-inner split or a selector included in the main inner pipeline;
- permutation importance from a tuned RF, calculated on inner-validation data rather than its fit data;
- SHAP only for a tree model as a secondary ranking, computed within training/validation boundaries. It is not the universal primary selector.

For each selector and budget, group dummy columns back to a source variable. Inner CV chooses selector+budget+model hyperparameters. At a chosen budget, fit RBF-SVM and QSVC on exactly the same selected source variables, rows, scaling and outer test fold.

### Track B: latent compression

PCA dimensions: 8, 6 and 4. PCA is inside the pipeline after imputation/encoding/standardisation and is fit only on training data. Record fold-wise explained variance, but never use full-data PCA to pick dimensions.

At each dimension, run RBF-SVM and QSVC on the identical component matrix. VQC is optional at 8/6/4 only after the QSVC minimum experiment completes.

### QSVC

- Qiskit `FidelityQuantumKernel`/`QSVC`, version pinned; ideal statevector for the primary paired screen.
- Candidate maps: Z and ZZ angle-type maps with repetitions `{1,2}` and linear/ring entanglement when applicable.
- `C ∈ {0.1, 1, 10}` for the classical SVC layer.
- Kernel normalization/PSD enforcement and duplicate evaluation policy are fixed and logged.
- Inner tuning is computationally expensive: cache kernels by fold/configuration, but never reuse a kernel across different fitted scalers, selectors or PCA models.

### VQC (secondary)

Only budgets 4 and 6 in the MVE extension; budget 8 only if the pilot fits the resource cap. Use a shallow documented feature map, RealAmplitudes-like ansatz with reps `{1,2}`, COBYLA or SPSA, at most 100 objective evaluations, and three deterministic parameter initialisations. Do not select the best seed; report the seed distribution and aggregate.

## 6. Imbalance and threshold policy

The 250/150 split is moderate. The primary analysis uses no SMOTE/autoencoder augmentation. Class weights are inner-tuned where supported. A resampling sensitivity analysis may use RandomOverSampler or SMOTE **inside each inner-training fold only**; synthetic samples never enter validation/test folds.

For sensitivity/specificity, choose one threshold per fitted pipeline using inner out-of-fold predictions. Primary threshold maximises Youden's J; a secondary clinically conservative threshold targets sensitivity ≥0.90 where attainable. Freeze the resulting threshold before the outer/test prediction. Accuracy/F1 at a default 0.5 are labelled separately.

## 7. Seed and reproducibility policy

- Split seeds: `[11, 29, 47, 71, 101]`; final holdout seed 20260824.
- Estimator, permutation and quantum initialisation seeds are derived from and logged with the fold ID.
- Run stochastic classical finalists under five estimator seeds if their variance is non-negligible.
- Run VQC under at least three starts; finite-shot results under five shot seeds.
- Record Python/package versions, OS, CPU, RAM, thread counts, simulator method, BLAS/OpenMP settings and git commit.
- Save configurations and out-of-fold predictions, not patient-identifiable data copies.

## 8. Confidence intervals and statistical comparisons

- Report each outer-fold metric distribution and mean with a 95% interval. Because folds overlap, do not treat 25 scores as independent patients; use a corrected repeated-CV interval or a hierarchical bootstrap over repeat/fold with its limitation stated.
- On the locked test, calculate 95% stratified patient bootstrap intervals (2,000 resamples) for metrics. For paired model differences, resample the same patient indices.
- AUC difference: paired bootstrap as primary; DeLong as a secondary check if assumptions/software are verified.
- Binary errors at the frozen threshold: McNemar exact test on the locked test.
- Repeated outer comparisons: report paired deltas and effect sizes; use a corrected resampled test or permutation test. Wilcoxon across folds is descriptive because folds are dependent.
- Correct the finite family of planned model comparisons with Holm's method. Publish raw and adjusted p-values; do not equate non-significance with equivalence.
- Non-inferiority is exploratory: margin −0.05 for both sensitivity and ROC-AUC. Claim only if the relevant lower paired 95% bound exceeds −0.05. The margin is a hackathon criterion, not clinically validated.

## 9. Runtime measurement

On the same machine, measure wall time and CPU time with fixed thread counts:

- preprocessing/selection;
- kernel construction (train–train and test–train separately);
- classical fit;
- VQC optimisation;
- prediction;
- transpilation and simulation where relevant.

Perform one unmeasured warm-up; report median and IQR over at least three timed repeats for deterministic finalists. Include peak resident memory where possible. Never compare GPU and CPU or different simulators as if runtime were algorithmic speedup.

## 10. Planned result table

| Representation | Budget | Selector / variance | Model | Sensitivity | Specificity | ROC-AUC | Accuracy | Precision | F1 | PR-AUC | Runtime | 95% CI | Qubits/depth/shots |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Full variables | 24 | None | LR/RF/XGB/SVM | | | | | | | | | | N/A |
| Selected | 12/8/6/4 | MI/RFECV/permutation | SVM | | | | | | | | | | N/A |
| Selected | 12/8/6/4 | same subset | QSVC | | | | | | | | | | |
| PCA | 8/6/4 | explained variance | SVM/QSVC | | | | | | | | | | |
| Finalist | 4/6 | same representation | VQC optional | | | | | | | | | | |

## 11. Minimum viable experiment (MVE)

1. Audit/clean the official CKD archive and create the locked split.
2. Run full-24 LR, RF, XGBoost and RBF-SVM under repeated nested CV.
3. Use mutual information and permutation importance inside folds; evaluate selected budgets 8, 6 and 4 (12 may run classically first).
4. Run paired RBF-SVM and ideal-statevector QSVC at selected 8/6/4, using ZZ reps=1 first.
5. Run PCA 8/6/4 paired SVM/QSVC if kernel timing stays under the cap; otherwise 6/4.
6. Produce feature-stability, paired-metric and runtime/resource tables.
7. Evaluate one frozen finalist per representation on the locked test once.

No VQC, finite shots, noise, secondary disease or MVP integration is required to complete the MVE.

## 12. Stretch experiment and stopping rules

Stretch, in order: finite-shot finalists; shallow VQC at 4/6; calibrated Aer toy noise; Cleveland replication; West Bengal T2DM data audit/replication.

Stop a configuration when any pre-declared limit is reached: 30 minutes per kernel build, 2 hours per outer quantum configuration, 8 GB incremental memory, or a circuit count estimate above the remaining budget. Report `not run—resource cap`, not an imputed result. Reduce configuration count, not test-set size or methodological safeguards.

## 13. Interpretation rules

- “Preserved” requires the pre-specified paired confidence-bound criterion, not rounded equality.
- “Stable signature” requires the protocol in `feature_stability_protocol.md`; one full-data top-six list is insufficient.
- “Quantum advantage” is prohibited: simulator accuracy/runtime does not establish computational advantage.
- Feature reduction is not test reduction and is not a cost saving without acquisition-group and cost evidence.
- All outputs are research-only and are not diagnosis, triage, prognosis or clinical-decision support.

