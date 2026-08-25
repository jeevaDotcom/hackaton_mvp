# Quantum-Kernel Shift and State-Collision Audit

## Method

The persisted frozen QSVC `FidelityQuantumKernel` was evaluated on deterministic class-stratified representatives: 120 UCI-development and 160 BD-KDD records. The installed `ZFeatureMap` result matched the closed-form `∏ cos²(xᵢ−yᵢ)` with maximum absolute error **3.190e-13**.

## Within-cohort geometry

| matrix | n | offdiag_mean | offdiag_std | near_one_pct | near_zero_pct | kernel_variance | within_class_mean | between_class_mean | within_minus_between | effective_rank | numerical_rank | top_eigenvalue_fraction |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| within_UCI | 120 | 0.0853 | 0.1876 | 0.1261 | 60.2941 | 0.0352 | 0.1609 | 0.0109 | 0.1499 | 19.8294 | 106 | 0.1644 |
| within_BD-KDD | 160 | 0.0107 | 0.0400 | 0.0000 | 82.0440 | 0.0016 | 0.0109 | 0.0105 | 0.0003 | 125.7663 | 160 | 0.0194 |

## Cross-cohort geometry

| matrix | rows | columns | mean | std | near_one_pct | near_zero_pct | geometry_auc |
|---|---|---|---|---|---|---|---|
| BD-KDD_to_UCI | 160 | 120 | 0.0098 | 0.0380 | 0.0000 | 84.5052 | 0.5597 |

## Collision test

High clinical distance was predefined descriptively as the top 5% of pairwise Euclidean distances in the frozen transformed representation (5.299 or greater). A representation collision required fidelity at least 0.95. **0 of 39060 representative pairs (0.000%)** met both conditions.

Examples are stored in `kernel_collision_examples.csv`. Because the distance mixes UCI-standardised numeric values and one-hot clinical indicators, it is a representation-space clinical distance, not a validated clinical similarity metric.

## Plots

- [Kernel similarity distributions](figures/kernel_similarity_distributions.png)
- [Distance–fidelity collision audit](figures/kernel_collision_scatter.png)
