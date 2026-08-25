# Architecture Diagram Specification

## Purpose

One-slide diagram showing how frozen evidence moves from biomedical sources to an auditable verdict. The audience should understand the paired comparison in under ten seconds.

## Recommended composition

Use a left-to-right flow with one deliberate fork and reunion. Avoid implementation filenames on the visual; place them in notes or the submission summary.

```text
BIOMEDICAL DATASETS
CKD · BD-KDD · Cleveland · Pima
          ↓
DATA QUALITY + PREPROCESSING                 PHASE 1
schema · provenance · fold-safe fitting
          ↓
STABLE FEATURE SELECTION                     PHASE 1
24 → 8 primary · 6 secondary
          ↓
REPRESENTATION LAYER                         PHASE 2
     ↙                         ↘
Clinical variables             PCA control
     ↓                         ↓
Classical RBF SVM        Quantum-kernel QSVC
     ↘                         ↙
PAIRED EVALUATION                            PHASE 2
same folds · same budgets · performance + runtime
          ↓
ROBUSTNESS ENGINE                           PHASE 3
missingness · perturbation · training size · shots/noise
          ↓
SHIFT VALIDATION                            PHASE 3
BD-KDD transportability · cross-disease methodology
          ↓
EVIDENCE VERDICT
supported · neutral · not supported · inconclusive
          ↓
Q-CARE DASHBOARD
frozen artifacts · claim registry · offline replay
```

## Final presentation surface

The dashboard exposes exactly five sidebar destinations: **Overview**, **CKD Benchmark**, **Robustness & Shift**, **Cross-Disease**, and **Quantum Evidence**. The final interface reads all scientific values through `src/results_repository.py`; screenshots and presentation documents must use these exact labels.

Recommended final visual references:

- `screenshots/11_demo_hero.png` for the one-slide scientific story.
- `screenshots/04_classical_vs_quantum.png` for the paired benchmark.
- `screenshots/09_quantum_circuit.png` for the circuit/resource explanation.
- `screenshots/10_responsible_ai.png` for the final verdict and responsible-use boundary.

The finished no-slide architecture visual is `demo_backup/architecture_diagram.svg`. It is part of the offline judging package and does not constitute a presentation deck.

## Visual encoding

- **Background:** warm off-white, matching Q-CARE.
- **Primary text/lines:** dark ink.
- **Quantum branch:** cobalt; **classical branch:** ink.
- **Shift validation:** muted red accent to signal the decisive failure, not danger theatre.
- **Phase labels:** small monospaced annotations outside the main flow.
- **Emphasis:** make the paired-evaluation reunion the centre of gravity; do not make the quantum branch visually dominant.

## Speaker line

“The branches differ at the kernel, then reunite under the same evaluation, stress, and shift tests before any verdict is shown.”

## Guardrails

- Do not draw a patient, hospital workflow, diagnostic output, or quantum-computer photograph.
- Do not label the QSVC branch “advanced,” “accelerated,” or “superior.”
- Do not imply that PCA and clinical variables are pooled.
- Keep the BD-KDD cross-cohort transportability stress test after the frozen paired experiment, with PARTIAL target comparability visible.
