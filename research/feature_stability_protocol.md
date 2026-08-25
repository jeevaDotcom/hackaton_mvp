# Feature-stability protocol

Goal: distinguish a reproducible reduced signature from “one lucky six-feature subset.” This is an associational model-stability analysis, not a causal or clinical-guideline claim.

## 1. Resampling unit and leakage boundary

- Use the 25 outer-training partitions from repeated stratified 5-fold CV × 5 repeats defined in `experiment_protocol.md`.
- Each selector, imputer, encoder and ranker is fit from scratch inside an outer-training partition. If a selector needs tuning, that tuning uses only the inner folds.
- The outer-validation fold and locked test never affect ranks, selected budgets or stable-signature definitions.
- Dummy columns are grouped back to their source clinical variable before selection. A categorical variable is selected if its group is selected; it does not receive extra votes for having more levels.

## 2. Methods and budgets

Primary selectors:

1. Mutual information, with deterministic tie-breaking by source-variable name.
2. RFECV with a sparse logistic/linear-SVM estimator.
3. Permutation importance from a tuned random forest on inner out-of-fold predictions.

Secondary: TreeSHAP rank from a fold-fitted RF/XGBoost model. SHAP is model-specific and will not be presented as a clinical truth or used to choose the primary result after seeing outcomes.

Budgets: 12, 8, 6 and 4 source variables. Every method emits a complete 1–24 rank, using average ranks for genuine ties followed by deterministic naming only for subset construction.

## 3. Recorded quantities

For feature `j`, selector `s`, budget `k` and `B=25` outer fits:

- **Selection frequency:** `f(j,s,k) = count(j selected) / B`.
- **Mean and median rank**, rank standard deviation and rank IQR.
- **95% bootstrap interval for frequency:** resample outer repeats first, then folds within repeat, 2,000 draws. This respects the repeated-fold hierarchy better than treating 25 fits as independent.
- **Pairwise Jaccard:** `|A∩B| / |A∪B|` for every pair of selected sets at a fixed selector/budget; report median and IQR.
- **Kuncheva index** for fixed-size sets, correcting overlap expected by chance: `(r*n - k^2)/(k*(n-k))`, where `r` is intersection size, `n=24`, `k` is budget. Report mean/CI.
- **Nogueira stability estimate** across the selection matrix, with implementation/version and assumptions documented. Pairwise results remain available if a library implementation cannot be verified.
- **Cross-selector agreement:** Spearman rank correlation and overlap at k for selector pairs within the same outer partition.

## 4. Stable-signature rule

A variable is a **core stable variable at budget k** only when all are true:

1. selection frequency ≥0.80 for at least two of the three primary selectors;
2. median rank ≤k for those selectors;
3. upper rank-IQR boundary ≤k+2;
4. its frequency exceeds the 95th percentile from a label-permutation null described below.

A **stable reduced signature** exists only if:

- at least `ceil(0.75*k)` variables meet the core rule;
- median within-selector Jaccard ≥0.60 and mean Kuncheva ≥0.50;
- the corresponding model meets the pre-specified performance-preservation condition.

These thresholds are design choices for this project and will be shown, not portrayed as universal standards. Report the continuous stability measures even when the binary rule fails.

## 5. Chance and robustness controls

- **Permutation null:** for 100 label permutations per selector (or 25 if compute-limited), repeat ranks inside the same training partitions and estimate chance frequency/overlap. Never reuse permuted models for prediction claims.
- **Patient bootstrap:** on the development set, run 200 stratified bootstraps for the two most feasible selectors at budgets 8/6/4; compare with the repeated-CV result.
- **Missingness sensitivity:** repeat finalists with missing indicators and with complete cases only. The latter loses 242 rows and is descriptive, not preferred.
- **Algorithm sensitivity:** compare selector-specific signatures rather than collapsing them into one post hoc consensus.
- **Duplicate sensitivity:** if exact duplicate rows exist, use group-aware splits and compare the stability result.

## 6. Clinical relationship annotation

Create a literature-informed annotation only after selection frequencies are computed. Suggested fields:

| Feature | Selection frequency | Mean rank (IQR) | Selector agreement | Known relationship to CKD | Measurement family | Caveat |
|---|---:|---:|---:|---|---|---|
| hemoglobin | | | | Association with anaemia/renal impairment, if supported by cited clinical literature | blood | Associational; may reflect disease severity |
| serum creatinine | | | | Renal-function marker | blood | Could make the benchmark easy; not proof of early detection |
| specific gravity | | | | Urine concentration measure | urine | Site/lab-dependent |
| … | | | | | | |

Use language such as “known association,” “consistent with,” or “predictive in this cohort.” Never say a variable causes CKD, prevents CKD, or can be omitted from clinical care.

## 7. Planned figures

1. Feature × outer-fold selection heatmap, sorted by overall frequency.
2. Frequency with hierarchical-bootstrap intervals at each budget.
3. Rank-distribution violin/box plots for the top 12 variables.
4. Stability-versus-budget curve for Jaccard, Kuncheva and Nogueira estimates.
5. Performance-versus-stability scatter: each point is selector/budget/model; unstable high performance is visually distinguished.

## 8. Interpretation outcomes

- **Supported stable six:** stability and performance rules both pass at k=6. This supports further validation, not clinical sufficiency.
- **Stable eight, unstable six:** recommend eight as the smallest supported budget; remove the prototype's six-feature default.
- **No stable reduced set:** report that aggressive reduction is not supported; retain full/reduced classical reference only.
- **Stable predictors but QSVC worse:** the feature-signature finding survives; the quantum-preservation hypothesis fails.
- **QSVC similar but unstable features:** do not call the feature compressor successful; representation sensitivity is the finding.

