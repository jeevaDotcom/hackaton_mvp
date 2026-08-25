# Quantum-resource protocol

Status: designed, not run. The objective is to measure a bounded simulator experiment honestly—not to imply hardware speedup. Official Qiskit defines a fidelity kernel as `K(x,y)=|<φ(x)|φ(y)>|²` and constructs an N×M kernel matrix ([documentation](https://qiskit-community.github.io/qiskit-machine-learning/stubs/qiskit_machine_learning.kernels.FidelityQuantumKernel.html)). This pairwise structure is the principal cost risk.

## 1. Resource questions

1. How do source dimension/qubits, feature-map repetitions and transpiled two-qubit gates affect kernel build time and memory?
2. How much variance and predictive degradation appear at finite shots?
3. Does a labelled toy noise model change sensitivity/specificity or only kernel conditioning?
4. Is any finalist Pareto-competitive with the paired classical SVM when predictive metrics, runtime and robustness are kept separate?

## 2. Pre-registered configurations

### QSVC screen

| Tier | Representation | Qubits | Feature maps | Reps | Simulation | Purpose |
|---|---|---:|---|---:|---|---|
| MVE | Selected/PCA 4 | 4 | Z, ZZ-linear | 1 | ideal statevector | Guaranteed first quantum comparison |
| MVE | Selected/PCA 6 | 6 | ZZ-linear | 1 | ideal statevector | Main reduced comparison |
| Conditional | Selected/PCA 8 | 8 | ZZ-linear | 1 | ideal statevector | Run only after kernel pilot |
| Screen only | Selected 12 | 12 | Z only | 1 | ideal statevector or stratified training subsample | Resource scaling, not headline performance |
| Finalists | best 4 and 6 | same | winning pre-registered map | 1 and 2 | finite shots 1,024 and 4,096 | Shot/repetition sensitivity |

Do not tune across an unrestricted circuit library. Choose finalists using development folds only. Repetitions=2 is tested only for the best representation at 4/6 qubits.

### VQC extension

- Dimensions/qubits: 4 and 6; 8 only if a timed pilot completes within 30 minutes per fit.
- Encoding: angle encoding to `[0,π]`.
- Ansatz: RealAmplitudes-like ring entanglement, reps 1 and 2.
- Optimizer: COBYLA and, resource permitting, SPSA; maximum 100 objective evaluations.
- Starts: three deterministic initial parameter seeds; report all, not the best.
- Shots: ideal estimator for screen, then 1,024 for finalists; 4,096 only for the single final circuit.

## 3. Circuit and compute ledger

For every fold/configuration record:

- logical qubits and any ancillas;
- source input dimension and post-encoding parameter count;
- feature-map/ansatz name, repetitions and entanglement topology;
- raw and transpiled depth;
- total gates, one-qubit gates, two-qubit gates and measurements;
- transpiler basis gates, coupling map, optimisation level and seed;
- shots and shot seed;
- number of train–train and test–train kernel elements requested and actually evaluated;
- number of circuits, jobs and backend calls after symmetry/duplicate reuse;
- kernel matrix condition number and PSD correction magnitude;
- wall/CPU time by transpilation, simulation, optimisation and classical SVC stage;
- peak memory, software versions and host hardware.

The square training kernel has up to `n_train(n_train−1)/2` unique off-diagonal pairs plus the diagonal; test evaluation adds `n_test*n_train`. Nested CV multiplies this cost by folds, hyperparameters, representations and maps. Caching is allowed only for an identical fitted transform and circuit configuration.

## 4. Shot experiment

For the best selected-variable and PCA configurations at 4/6 dimensions:

1. Ideal statevector reference.
2. 1,024 shots × 5 shot seeds.
3. 4,096 shots × 5 shot seeds for the single most feasible dimension/map.

Report mean/SD and full range of kernel entries, metrics and runtime. Compare each finite-shot kernel with ideal using Frobenius norm, kernel-target alignment, PSD correction and prediction disagreement. Do not choose the favourable shot seed.

## 5. Noise experiment

Qiskit Aer supports custom depolarising, thermal-relaxation and readout noise and warns that backend-derived models are approximations ([official tutorial](https://qiskit.github.io/qiskit-aer/tutorials/3_building_noise_models.html)). Therefore label all results **simulation under a specified toy/approximate noise model**, never “hardware performance.”

### A. Reproducible depolarising matrix

At 1,024 shots on finalist 4/6-qubit circuits:

- N0: no gate/readout noise.
- N1 mild: 1-qubit depolarising `p=0.001`, 2-qubit `p=0.01`, symmetric readout flip `p=0.01`.
- N2 stress: 1-qubit `p=0.005`, 2-qubit `p=0.05`, readout flip `p=0.03`.

The requested `0.01/0.05` values are assigned to two-qubit stress levels only; applying the same value indiscriminately to every gate would be poorly calibrated.

### B. Optional backend-shaped approximation

If an official fake backend is version-pinned, generate `NoiseModel.from_backend`, transpile to its basis/coupling map and record the snapshot. This remains an approximation, not access to that device.

### C. Thermal relaxation

Only run if gate durations are available. `T1`/`T2` without gate time is not a defined relaxation experiment. Log every qubit's T1/T2, gate duration and the physical constraint `T2 ≤ 2*T1`.

## 6. Feasibility and stopping rules

| Configuration | Expected feasibility | Main concern | Action |
|---|---|---|---|
| 4-qubit ideal QSVC, n≈256 train/fold | High | tens of thousands of pair evaluations across nested folds | Cache exact kernels; run first |
| 6-qubit ideal QSVC | Medium–high | same quadratic pairs plus deeper states | Main quantum target |
| 8-qubit ideal QSVC | Medium | hyperparameter/fold multiplication | Pilot one fold; proceed only below cap |
| 12-qubit ideal QSVC | Low for full nested grid | circuit and pair count; memory/time | Screen one fixed config or subsample; no headline |
| 4/6-qubit finite shots | Medium | shots × pair count × seeds | Finalists only |
| 8-qubit finite shots/noise | Low | multiplication by shots/noise/seeds | Stretch only |
| VQC 4/6 | Medium | objective evaluations × circuits × starts | Shallow ansatz, capped evaluations |
| VQC 8 | Low | trainability and runtime | Conditional pilot |

Hard stops per configuration: 30 minutes for one kernel matrix pilot, 2 hours for an outer-fold configuration, 8 GB incremental memory, or >250,000 estimated circuit executions. Mark stopped configurations explicitly. Do not promise that 6–8 qubits “run in seconds.” Actual times must come from the ledger.

## 7. Utility reporting

Report a profile with no arbitrary weighted total:

| Model/config | Sensitivity | Specificity | ROC-AUC | Δ vs SVM | Variables/dimensions | Qubits | Depth / 2Q gates | Shots | Runtime | Noise ΔAUC | Stability |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|

A configuration is Pareto-dominated if another is no worse in all reported dimensions and better in at least one. That is a descriptive engineering result, not proof of quantum utility or advantage.

## 8. Claims explicitly excluded

- Statevector or Aer runtime is not quantum hardware runtime.
- More qubits, reps or shots are not assumed to improve accuracy.
- Feature map expressivity is not a clinical mechanism.
- Noise robustness under N1/N2 is not safety, clinical robustness or hardware validation.
- An equal accuracy does not show speedup; the full resource ledger must accompany any comparison.

