# Phase 3C — Target Comparability, Univariate Signal, and External Uncertainty

## Frozen-evidence decision

**Final root-cause classification: BOTH.** Target comparability is **PARTIAL**, and all eight frozen features lose their individually detectable UCI label association inside BD-KDD. The evidence therefore supports both target/cohort differences and changed feature–target relationships. It does not isolate pure conditional shift.

**Exact approved wording:**

> External transport failure reflected both target/cohort differences and changed feature–target relationships; therefore the experiment demonstrates transportability risk but cannot isolate pure conditional shift.

The frozen models, Streamlit application, and `artifacts/claim_registry.json` were not modified.

## 1. Target and cohort evidence

| Cohort | Total | CKD | non-CKD | CKD prevalence | Raw labels |
|---|---:|---:|---:|---:|---|
| UCI full source cohort | 400 | 250 | 150 | 62.50% | `ckd`, `notckd` |
| BD-KDD | 988 | 507 | 481 | 51.32% | `1` (kidney disease), `0` (healthy) |

Prevalence differs but is not used alone to infer incompatibility. The target-definition audit rates comparability **PARTIAL** because public documentation does not establish equivalent chronicity, staging, diagnostic rules, or control recruitment. See [target_definition_audit.md](../reports/root_cause/target_definition_audit.md) and [bd_kdd_target_profile.md](../reports/root_cause/bd_kdd_target_profile.md).

## 2. Within-cohort feature–target signal

Signed ROC-AUC preserves raw increasing orientation; `dm=yes`, `appet=poor`, and `htn=yes` are the binary risk-coded orientations.

| Feature | UCI signed AUC (95% CI) | BD-KDD signed AUC (95% CI) | UCI → BD-KDD |
|---|---:|---:|---|
| `hemo` | 0.0312 [0.0161, 0.0487] | 0.4944 [0.4589, 0.5307] | FLATTENED |
| `al` | 0.8708 [0.8397, 0.8995] | 0.4981 [0.4633, 0.5333] | FLATTENED |
| `dm` | 0.7740 [0.7440, 0.8060] | 0.5023 [0.4707, 0.5341] | FLATTENED |
| `sg` | 0.0787 [0.0538, 0.1069] | 0.5171 [0.4809, 0.5515] | FLATTENED |
| `pcv` | 0.0476 [0.0266, 0.0722] | 0.4708 [0.4354, 0.5078] | FLATTENED |
| `appet` | 0.6640 [0.6340, 0.6940] | 0.5153 [0.4839, 0.5461] | FLATTENED |
| `htn` | 0.7940 [0.7620, 0.8240] | 0.5053 [0.4744, 0.5368] | FLATTENED |
| `sc` | 0.9227 [0.8952, 0.9467] | 0.5182 [0.4828, 0.5550] | FLATTENED |

All eight UCI intervals exclude 0.5, while every BD-KDD interval includes 0.5. No association is genuinely reversed: a few BD-KDD point estimates lie on the opposite side of 0.5, but their intervals do not support a directional claim. Complete distributions and methods are in [per_label_feature_profiles.md](../reports/root_cause/per_label_feature_profiles.md) and [univariate_auc.md](../reports/root_cause/univariate_auc.md).

ROC-AUC depends on ranking. Positive-factor unit conversion, standardisation, min-max scaling, and any other strictly increasing transformation preserve AUC. A strictly decreasing transform reverses orientation; a non-monotonic transform can change ranking. Ordinary scaling therefore cannot rescue the near-random within-BD-KDD feature rankings.

## 3. External uncertainty

The uncertainty audit used 10,000 class-stratified, patient-level bootstrap replicates, paired across predictions.

| Comparison | Point estimate | 95% CI | Decision |
|---|---:|---:|---|
| Frozen RBF SVM AUC | 0.5106 | [0.4750, 0.5456] | Indistinguishable from random |
| Frozen QSVC AUC | 0.5254 | [0.4891, 0.5606] | Indistinguishable from random |
| QSVC − SVM AUC | +0.0148 | [-0.0292, +0.0581] | Includes zero; models not distinguishable |

The paired bootstrap delta was positive in 75.2% of replicates, which is insufficient to establish superiority. Clipping and three post-hoc bounded encodings also had intervals spanning 0.5. **No tested configuration demonstrated reliable better-than-random external discrimination.** See [external_auc_bootstrap.md](../reports/root_cause/external_auc_bootstrap.md).

## 4. Geometry shared by both model families

| Diagnostic | UCI development | BD-KDD |
|---|---:|---:|
| QSVC within − between similarity | 0.0818 | -0.00005 |
| QSVC centered kernel-target alignment | 0.4889 | 0.0199 |
| QSVC effective rank | 32.90 / 320 | 390.80 / 988 |
| QSVC off-diagonal variance | 0.02380 | 0.0014465 |
| RBF within − between similarity | 0.2449 | -0.00011 |
| RBF centered kernel-target alignment | 0.7544 | 0.0053 |
| RBF external score overlap | — | 0.8780 |
| QSVC external score overlap | — | 0.9278 |

The external QSVC kernel does not show a low-rank collision collapse. It becomes high-rank and largely near-orthogonal, but almost label-unaligned: within- and between-class similarity are essentially identical. The RBF kernel independently loses its stronger UCI class geometry. This is generally uninformative external geometry shared by both model families, not evidence of a quantum-specific failure or benefit. See [kernel_information_content.md](../reports/root_cause/kernel_information_content.md) and [classical_geometry.md](../reports/root_cause/classical_geometry.md).

## 5. Serum-creatinine diagnostic

| Cohort/label | Median documented serum creatinine | Missing |
|---|---:|---:|
| UCI non-CKD | 0.90 mg/dL | 5/150 |
| UCI CKD | 2.25 mg/dL | 12/250 |
| BD-KDD non-CKD | 7.10 mg/dL | 0/481 |
| BD-KDD CKD | 7.71 mg/dL | 0/507 |

The histogram overlap coefficient rises from 0.4160 in UCI to 0.8097 in BD-KDD. Signed AUC falls from 0.9227 [0.8952, 0.9467] to 0.5182 [0.4828, 0.5550]. Both sources document mg/dL-equivalent units with high confidence. These distributions suggest a substantially different renal-function cohort or label/cohort construction; they do not by themselves define a CKD stage. See [serum_creatinine_deep_dive.md](../reports/root_cause/serum_creatinine_deep_dive.md).

## 6. Decision boundary

The most defensible interpretation is **BOTH**, not target incompatibility alone and not pure conditional shift:

- **Target/cohort differences:** endpoint wording, chronicity criteria, stage, control selection, and comparable diagnostic rules are not established; the observed renal-function distributions differ materially.
- **Changed feature–target relationships:** every frozen feature with strong UCI discrimination is statistically indistinguishable from random univariate ranking within BD-KDD, and both kernels lose class separation.
- **What is not established:** the audit cannot apportion causality between target construction, population case mix, measurement/record practices, or another upstream process.

BD-KDD remains useful as a frozen cross-cohort **transport stress test**, but it should not be described as clean like-for-like clinical external validation.

## Reproducibility and integrity

The Phase 3C runner is [run_phase3c.py](../scripts/run_phase3c.py). It verifies SHA-256 hashes before and after the audit for the two frozen models, external metrics/predictions, and claim registry. All five hashes matched. Numerical tables use the full UCI source cohort for within-dataset target analysis and the frozen 320-record UCI development cohort only for model/kernel diagnostics.
