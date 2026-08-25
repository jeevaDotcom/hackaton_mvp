# Transparent quantum-utility evidence

No weighted composite score is calculated. Labels follow disclosed rules: predictive utility is SUPPORTED only when a paired bootstrap interval is wholly positive, NOT SUPPORTED when any primary mean degradation exceeds 0.05, and otherwise NEUTRAL. Runtime is SUPPORTED only below parity. Unmeasured representation-specific robustness is INCONCLUSIVE.

| Representation | Budget | Δ sens | Δ spec | Δ AUC | Δ F1 | Qubits | Depth | Runtime × | Predictive | Feature budget | Small sample | Runtime | Noise |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| clinical | 8 | -0.017 | -0.021 | -0.001 | -0.015 | 8 | 2 | 464.1 | NEUTRAL | NEUTRAL | NOT SUPPORTED | NOT SUPPORTED | INCONCLUSIVE |
| clinical | 6 | -0.025 | -0.008 | -0.006 | -0.015 | 6 | 2 | 476.6 | NEUTRAL | SUPPORTED | INCONCLUSIVE | NOT SUPPORTED | SUPPORTED |
| clinical | 4 | -0.065 | -0.062 | -0.027 | -0.053 | 4 | 2 | 370.2 | NOT SUPPORTED | NOT SUPPORTED | INCONCLUSIVE | NOT SUPPORTED | INCONCLUSIVE |
| pca | 8 | -0.010 | -0.233 | -0.020 | -0.070 | 8 | 2 | 480.5 | NOT SUPPORTED | INCONCLUSIVE | INCONCLUSIVE | NOT SUPPORTED | INCONCLUSIVE |
| pca | 6 | -0.050 | -0.175 | -0.037 | -0.075 | 6 | 2 | 437.9 | NOT SUPPORTED | INCONCLUSIVE | INCONCLUSIVE | NOT SUPPORTED | INCONCLUSIVE |
| pca | 4 | -0.083 | -0.133 | -0.052 | -0.082 | 4 | 2 | 427.8 | NOT SUPPORTED | INCONCLUSIVE | INCONCLUSIVE | NOT SUPPORTED | INCONCLUSIVE |

A single Quantum Utility Score is not justified: the evidence dimensions have different meanings, scales and uncertainty, and weighting them would conceal rather than clarify trade-offs.
