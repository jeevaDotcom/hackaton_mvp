# Deterministic Two-Minute Demo — Final UI

## Setup

- Start `streamlit run app.py`; wait for **Overview**.
- Keep the sidebar open, browser zoom fixed, and every page at its top.
- Use frozen Demo mode only. Do not open every chart or run an experiment.

| Time | Exact action | Presenter line | Point at |
|---|---|---|---|
| 0–18 s | **Overview** — stay at the top. | “Q-CARE tests whether a quantum result survives fair comparison, compute cost, stress, and cross-cohort transport. Internal RBF/QSVC AUCs were 1.000/0.999; on BD-KDD they were 0.511/0.525, with both intervals including chance.” | Paired internal → BD-KDD hero |
| 18–48 s | Click **CKD Benchmark**. Point to `24 → 8`, then make one rehearsed scroll to **Classical vs quantum**. | “Leakage-free selection reduced 24 CKD predictors to a stable eight-variable representation. At the same budget, QSVC sensitivity was 0.985 versus 1.000 for RBF SVM, so it remained internally competitive within our predefined descriptive tolerance.” | `24 → 8`; 8-variable rows |
| 48–65 s | Stay on **Classical vs quantum**. | “But competitive did not mean advantageous: exact statevector QSVC was about 464 times slower. We found competitiveness, not acceleration.” | `464× slower` |
| 65–100 s | Click **Robustness & Shift** and stay at the top. | “This was not a quantum-specific failure. Both model AUC intervals included chance, target comparability was only partial, and all eight internally predictive features flattened toward chance in BD-KDD.” | Paired external comparison, PARTIAL label, feature chart |
| 100–120 s | Click **Quantum Evidence**, press **End**, stop at **Final evidence summary**. | “Q-CARE’s value is the evidence verdict: QSVC was competitive internally, but no performance, runtime, robustness, or generalisation advantage was demonstrated.” | Frozen verdict and validated claim status |

## Failure recovery

If Streamlit stalls, open `demo_backup/README.md` and present the same sequence over the numbered images. Do not improvise stronger claims.
