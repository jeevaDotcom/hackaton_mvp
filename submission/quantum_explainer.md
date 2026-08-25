# Quantum Explainer

## Level 1 — Non-technical judge (35 words)

A quantum kernel turns each record into a quantum state and measures how similar two states are. QSVC uses that similarity table in a support-vector classifier, allowing a fair comparison with a classical kernel method.

## Level 2 — Technical ML judge

The selected, scaled variables enter a `ZFeatureMap`. Each variable parameterises a single-qubit Z rotation. A fidelity quantum kernel evaluates pairwise overlap between encoded quantum states, producing a kernel matrix. QSVC supplies that precomputed quantum similarity to the same support-vector classification idea used by classical SVMs. The comparison fixes folds, preprocessing boundaries, classifier regularisation, and feature dimensionality; only the kernel construction differs.

## Level 3 — Quantum expert

- **Architecture choice:** A limited, development-only search compared low-depth feature maps. `ZFeatureMap`, `reps=1` produced the best measured development evidence.
- **No entanglement:** The selected map contains only single-qubit encoding operations. More complex tested circuits did not improve the measured outcome. This weakens any claim of distinctly quantum representational advantage and is disclosed rather than hidden.
- **Kernel evaluation:** Pairwise state fidelities form the training and evaluation kernel matrices consumed by `QSVC` with frozen `C=0.5`.
- **Resources:** Eight qubits are primary and six are secondary; the decomposed logical feature-map depth is two.
- **Execution:** Primary comparison uses exact local statevector kernel evaluation. It is simulator evidence, not quantum-hardware evidence.
- **Finite shots:** Separate local finite-shot experiments test whether estimates remain stable at the evaluated shot counts. Their verdict is limited to the tested simulation.
- **Noise:** A small Aer noise experiment used 48 training and 24 validation cases. Its size and synthetic noise setting make the result inconclusive for broad hardware robustness.
- **Limitations:** No hardware latency, queueing, transpilation, device drift, mitigation, or scaling claim is supported. Fidelity-kernel construction also scales poorly with the number of sample pairs.

## Judge answer — Why no entanglement?

“The architecture search was deliberately limited, and the low-depth `ZFeatureMap` with one repetition gave the best evidence. Adding circuit complexity did not improve the measured outcome. This experiment evaluates a quantum-kernel pipeline; it does not assume entanglement is required. The absence of entanglement weakens any strong claim of distinctly quantum representational advantage, so we report it transparently rather than hiding it.”

## Dangerous question — “Is this really quantum machine learning?”

“Yes, as an implementation: it is a QSVC using a quantum fidelity kernel. Each feature vector is encoded into an eight-qubit quantum state, and pairwise kernel similarities are calculated from quantum-state fidelity before the support-vector classifier uses that matrix. The winning `ZFeatureMap` was deliberately shallow—one repetition, depth two—and contains no entanglement. More complex tested maps did not improve the evidence. We therefore make no claim of a distinctly quantum representational or computational advantage. The absence of entanglement is not hidden; it is an important limitation on any strong quantum-advantage interpretation.”

## Judge answer — Why did external validation fail?

“We cannot attribute the result to one pure mechanism. Target comparability between UCI and BD-KDD was only partial, and the eight feature-label relationships that were strong in UCI flattened to approximately random discrimination in BD-KDD. RBF SVM AUC was 0.511 [0.475-0.546] and QSVC AUC 0.525 [0.489-0.561]. We therefore report a cross-cohort transportability failure rather than a quantum-specific failure or clean conditional-shift proof.”

## Evidence

`artifacts/quantum_config.json`; `artifacts/qsvc_z_reps1_8_circuit.txt`; `artifacts/quantum_environment.json`; `artifacts/quantum_finite_shot_results.csv`; `artifacts/quantum_noise_results.csv`; `reports/validation/shift_profile.md`.
