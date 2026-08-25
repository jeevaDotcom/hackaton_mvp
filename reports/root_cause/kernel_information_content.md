# QSVC Kernel Information Content

The exact full-cohort kernel was computed analytically as `∏ cos²(xᵢ−yᵢ)`, previously verified against the persisted Qiskit `FidelityQuantumKernel` to maximum absolute error `3.19×10⁻¹³`.

| matrix | n | offdiag_mean | offdiag_median | offdiag_sd | offdiag_variance | offdiag_p5 | offdiag_p25 | offdiag_p75 | offdiag_p95 | within_class_mean | between_class_mean | within_minus_between | effective_rank | numerical_rank | condition_number_positive_spectrum | top_eigenvalue_fraction | centered_kernel_target_alignment |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| QSVC UCI development | 320 | 0.0596 | 0.0018 | 0.1543 | 0.0238 | 0.0000 | 0.0001 | 0.0257 | 0.3538 | 0.0980 | 0.0162 | 0.0818 | 32.9046 | 249 | 2740450619.0593 | 0.1250 | 0.4889 |
| QSVC BD-KDD | 988 | 0.0101 | 0.0004 | 0.0380 | 0.0014 | 0.0000 | 0.0000 | 0.0042 | 0.0487 | 0.0101 | 0.0101 | -0.0000 | 390.7980 | 988 | 3402.1251 | 0.0128 | 0.0199 |

The external kernel has high effective rank but almost no label-aligned separation: high rank here indicates many near-orthogonal directions, not useful target information. The positive-spectrum condition number excludes eigenvalues below `1e-10 × max(eigenvalue)` and should be interpreted only as a numerical descriptor. The full ordered spectrum is in `kernel_eigenvalue_spectra.csv`.

This distinguishes gross collisions from low-separation geometry: Phase 3B found zero high-distance/fidelity≥0.95 representative collisions, while Phase 3C shows generally uninformative external class geometry.
