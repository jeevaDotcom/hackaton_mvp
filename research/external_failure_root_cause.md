# Phase 3B — External Failure Root-Cause Analysis

## Frozen result

The original external result is unchanged:

| Model | Sensitivity | Specificity | ROC-AUC |
|---|---:|---:|---:|
| Classical RBF SVM | 0.986 | 0.004 | 0.511 |
| QSVC | 0.992 | 0.010 | 0.525 |

Phase 3B did not tune, recalibrate, or overwrite either frozen model. Ablation and bounded-encoding models are disposable diagnostic or post-hoc research copies. Hashes of both frozen models, the external metrics/predictions, and the claim registry were identical before and after the analysis.

## Phase 3D interpretation freeze

Phase 3C added source-level target comparability and paired uncertainty analysis. It supersedes Phase 3B's earlier attempt to name one dominant conditional-shift mechanism.

**External transport failure reflected both target/cohort differences and changed feature–target relationships; therefore the experiment demonstrates transportability risk but cannot isolate pure conditional shift.** Target comparability is **PARTIAL**. RBF SVM AUC was 0.511 [95% CI 0.475-0.546] and QSVC AUC was 0.525 [95% CI 0.489-0.561]; neither was reliably better than chance. The paired difference was +0.0148 [95% CI -0.0292 to +0.0581].

The evidence does not support a positive-class bug, a documented unit conversion error, frozen-scaler range extrapolation, or clinically meaningful quantum-state collision as the dominant cause. BD-KDD values shift strongly in prevalence and location—serum creatinine has the largest PSI at 1.912—but remain inside UCI-development numeric min/max. More importantly, every frozen feature loses most or all of its UCI class association: UCI-directed single-feature AUCs of 0.673–0.975 become 0.483–0.529 on BD-KDD.

Both kernels then lose class separation. Classical external ROC-AUC is 0.511 and QSVC ROC-AUC is 0.525. About 99% of both models’ external scores lie above the CKD decision boundary. This directly produces near-zero specificity.

## Mandatory label gate

**PASS.** UCI `ckd` maps to `1`; UCI `notckd` maps to `0`. BD-KDD’s dictionary specifies `1 = kidney disease` and `0 = healthy`, and the loader preserves that mapping. Clean counts are:

- UCI full: 250 CKD / 150 non-CKD; development: 200 / 120.
- BD-KDD: 507 kidney disease / 481 healthy.
- Frozen SVM and QSVC classes: `[0, 1]`.
- Positive decision score: class `1`.
- Metric confusion-matrix order: TN, FP, FN, TP from labels `[0, 1]`.

The deliberate inversion test produced `1 − AUC`: QSVC `0.525 → 0.475`; classical `0.511 → 0.489`. Recomputed scores and predictions exactly match the frozen external artifact. Full audit: [`../reports/root_cause/label_mapping_audit.md`](../reports/root_cause/label_mapping_audit.md).

## Feature semantics

Six mappings are exact: `al`, `dm`, `sg`, `appet`, `htn`, and `sc`. Hemoglobin and packed-cell volume are likely matches: BD-KDD states g/dL and percent, while the UCI description says “gms” and omits the packed-cell-volume unit. No conversion was applied. No measured range pattern indicates a factor-of-10 or factor-of-100 conversion error.

This supports syntactic compatibility, not laboratory or target-definition equivalence. Full table: [`../reports/root_cause/feature_semantics.md`](../reports/root_cause/feature_semantics.md).

## Distribution and class-conditional shift

### Marginal shift

| Feature | UCI median | BD-KDD median | KS | PSI |
|---|---:|---:|---:|---:|
| hemo | 12.60 | 12.10 | 0.079 | 0.062 |
| al | 0.00 | 2.00 | 0.345 | 0.554 |
| sg | 1.020 | 1.015 | 0.170 | 0.407 |
| pcv | 40.0 | 37.0 | 0.122 | 0.154 |
| sc | 1.30 | 7.52 | 0.595 | 1.912 |

BD-KDD also has no missing values, while UCI-development missingness is 4.7–16.9% across numeric frozen features. Risk-category prevalence rises by 14.1 percentage points for diabetes, 28.0 for poor appetite, and 16.1 for hypertension.

### Feature-label relationship collapse

The risk direction was fixed from UCI development and applied unchanged to BD-KDD:

| Feature | UCI-directed AUC | BD-KDD AUC in UCI direction | Change |
|---|---:|---:|---:|
| hemo | 0.975 | 0.506 | −0.469 |
| al | 0.820 | 0.498 | −0.322 |
| sg | 0.890 | 0.483 | −0.407 |
| pcv | 0.958 | 0.529 | −0.429 |
| sc | 0.919 | 0.518 | −0.401 |
| dm | 0.780 | 0.502 | −0.278 |
| appet | 0.673 | 0.515 | −0.157 |
| htn | 0.795 | 0.505 | −0.290 |

For example, UCI-development mean serum creatinine is 0.901 for non-CKD and 4.146 for CKD; BD-KDD means are 7.411 and 7.653. The external cohort therefore places both classes in a region that UCI associates with CKD while removing most within-cohort class separation. This explains the shared positive-score shift.

Evidence: [`../reports/root_cause/raw_feature_shift.md`](../reports/root_cause/raw_feature_shift.md) and [`../reports/root_cause/class_conditional_shift.csv`](../reports/root_cause/class_conditional_shift.csv).

## Frozen scaler

Using the exact persisted UCI-development preprocessor:

- BD-KDD numeric cells below/above the UCI transformed min/max: **0.00%**.
- BD-KDD records with any numeric feature outside that range: **0.00%**.
- BD-KDD values beyond ±3 transformed SD: **0.00%**.
- Values beyond ±2 occur for 0.7% of hemoglobin, 20.0% of albumin, 19.1% of specific gravity, 8.4% of PCV, and 7.5% of creatinine, but all remain within observed UCI range.

The preprocessing reveals a location/prevalence shift, not unsupported numerical extrapolation. Full audit: [`../reports/root_cause/scaler_shift.md`](../reports/root_cause/scaler_shift.md).

## Quantum phase and kernel geometry

The installed Qiskit `ZFeatureMap(reps=1)` circuit applies `P(2*x[i])`. The kernel is therefore periodic in each scaled feature with period `π` and equals `∏ cos²(xᵢ−yᵢ)`; the closed form matched the persisted `FidelityQuantumKernel` with maximum absolute error `3.19×10⁻¹³`.

Principal-interval wrapping occurs for numeric features, but no BD-KDD value is one full 2π phase period from zero. UCI itself contains full-period serum-creatinine phases because of an extreme training value. Thirteen distinct cross-cohort creatinine values have near-identical modulo phase under the audit threshold, but this does not produce whole-state collision.

On 120 class-stratified UCI and 160 class-stratified BD-KDD representatives:

- High-distance/high-fidelity pairs: **0 / 39,060**.
- Within-UCI quantum similarity separation: `0.1609 − 0.0109 = 0.1499`.
- Within-BD-KDD separation: `0.0109 − 0.0105 = 0.0003`.
- BD-KDD quantum off-diagonal similarities ≤0.01: **82.0%**.
- No off-diagonal BD-KDD similarity was ≥0.99.

The external quantum kernel becomes mostly near-orthogonal and loses class structure, but it does not collapse clinically distant samples onto near-identical quantum states. This is label-uninformative kernel geometry, not demonstrated angle aliasing. Because target comparability is only partial, it cannot be isolated as proof of pure conditional shift.

Evidence: [`../reports/root_cause/quantum_angle_audit.md`](../reports/root_cause/quantum_angle_audit.md) and [`../reports/root_cause/kernel_shift.md`](../reports/root_cause/kernel_shift.md).

## Classical comparison and score mechanism

The classical RBF kernel also loses class structure:

- Within-UCI same-minus-different similarity: **0.3435**.
- Within-BD-KDD same-minus-different similarity: **−0.0020**.
- Classical AUC: **0.511**; QSVC AUC: **0.525**.
- Classical non-CKD above boundary: **99.58%**; QSVC: **98.96%**.
- Median classical score: CKD 1.347, non-CKD 1.342.
- Median QSVC score: CKD 0.922, non-CKD 0.919.

The near-complete overlap by actual class explains both models’ false-positive rates and specificity. Full evidence: [`../reports/root_cause/score_distribution.md`](../reports/root_cause/score_distribution.md).

## Mechanism probes

### Diagnostic feature ablation

Removing one feature at a time changes external quantum-kernel AUC by only −0.013 to +0.003. The best removal is `sg`, AUC 0.528 versus the eight-feature diagnostic replay at 0.525. No single shifted feature dominates the failure. See [`../reports/root_cause/ablation_diagnostic.md`](../reports/root_cause/ablation_diagnostic.md).

### Frozen-model clipping

Min/max and ±3-SD clipping change no cells. UCI p1/p99 clipping changes 0.291% of cells and moves AUC only from 0.52538 to 0.52554. Out-of-range encoding is not a material cause. See [`../reports/root_cause/clipping_diagnostic.md`](../reports/root_cause/clipping_diagnostic.md).

### Post-hoc bounded encoding

Three UCI-only fitted bounded encodings were tested with experimental QSVC copies:

- MinMax to `[−π/4, π/4]`: AUC 0.499.
- RobustScaler plus bounded tanh: AUC 0.499.
- Quantile map to `[−π/4, π/4]`: AUC 0.500.

All are worse than the original 0.525. Bounded encoding does not rescue transport, so no optional feature-map search is scientifically justified. See [`../reports/root_cause/exploratory_bounded_encoding.md`](../reports/root_cause/exploratory_bounded_encoding.md).

## Root-cause decision tree

| Candidate cause | Classification | Evidence |
|---|---|---|
| LABEL BUG | NOT SUPPORTED | Raw/clean mappings, model class order, score sign, metrics, inversion test, and frozen predictions agree. |
| SCHEMA/UNIT MISMATCH | NOT SUPPORTED | Six exact and two likely semantic matches; no documented conversion mismatch. Source documentation remains incomplete for two units. |
| PREPROCESSING EXTRAPOLATION | NOT SUPPORTED | 0% of BD numeric cells outside UCI-development min/max; clipping changes AUC by +0.00016 at best. |
| QUANTUM ANGLE ALIASING | NOT SUPPORTED | No full-period BD crossing, zero high-distance/high-fidelity whole-state collisions, no clipping/bounding rescue. |
| GENERAL DATASET SHIFT | SUPPORTED | Strong marginal/prevalence shift and collapse of all eight UCI-directed feature AUCs toward 0.5. Both kernels lose class separation. |
| TARGET/COHORT COMPARABILITY | PARTIAL | Positive-label wording, diagnostic rules, chronicity, staging, and control recruitment are not established as equivalent. |
| MULTIPLE CAUSES | SUPPORTED | Target/cohort differences coexist with changed feature-label relationships; no independent label, unit, scaler, or quantum-aliasing fault is supported. |
| PURE CONDITIONAL SHIFT | NOT ESTABLISHED | Partial target comparability prevents isolation of a like-for-like conditional mechanism. |

## Required completion answers

1. **Label mapping correct?** YES.
2. **Any unit/schema mismatch?** No documented mismatch; hemoglobin and PCV are likely rather than exact because UCI unit documentation is incomplete.
3. **Worst shifted feature:** serum creatinine (`sc`), PSI 1.912; median 1.30 → 7.52.
4. **BD-KDD outside UCI scaler range:** 0.00% of numeric cells; 0.00% of records have any numeric feature outside the UCI-development min/max.
5. **Evidence of phase wrapping?** Limited principal-interval wrapping, yes; full-period BD crossing, no. It is not supported as the failure mechanism.
6. **Evidence of quantum-state collisions?** No: 0/39,060 high-distance representative pairs reached fidelity ≥0.95.
7. **Classical external AUC:** 0.511.
8. **QSVC external AUC:** 0.525.
9. **Does clipping change AUC?** No materially; best 0.52554, +0.00016.
10. **Does bounded encoding change AUC?** Yes, downward; best 0.500, −0.026.
11. **Final root cause:** BOTH target/cohort differences and changed feature-label relationships.
12. **Quantum-specific, dataset-specific, or mixed?** Shared cross-cohort transportability failure; no supported quantum-specific mechanism.
13. **New scientifically defensible finding:** internal feature stability did not guarantee external feature transportability; neither scaler overflow nor quantum-state collision explains the result.
14. **Does the Q-CARE story need updating?** YES: describe a cross-cohort stress-test failure with PARTIAL target comparability, not clean external validation or proof of pure conditional shift.

## Scientific boundary

The combined Phase 3B/3C evidence cannot apportion causality among target definition, population case mix, laboratory practice, record construction, or another provenance process. Resolving that upstream question requires source-level clinical/data-governance evidence and multi-site design, not post-hoc model tuning.
