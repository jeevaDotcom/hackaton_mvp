# Quantum-kernel diagnostics

Diagnostics use a fixed, stratified 80-patient sample from development data only. Kernels are exact statevector fidelities; the reported positive-spectrum condition number excludes eigenvalues ≤1e-10.

| Representation | Budget | Map | Shape | Diag mean | Offdiag mean | Within CKD | Within non-CKD | Between | Centered KTA | Condition | Rank |
|---|---|---|---|---|---|---|---|---|---|---|---|
| clinical | 4 | z_reps1 | 80×80 | 1.000 | 0.181 | 0.257 | 0.225 | 0.107 | 0.274 | 5.27e+10 | 70 |
| clinical | 4 | zz_reps1 | 80×80 | 1.000 | 0.097 | 0.123 | 0.076 | 0.081 | 0.127 | 3.51e+10 | 76 |
| clinical | 4 | zz_reps2 | 80×80 | 1.000 | 0.098 | 0.121 | 0.075 | 0.087 | 0.110 | 1.11e+10 | 77 |
| clinical | 6 | z_reps1 | 80×80 | 1.000 | 0.065 | 0.047 | 0.246 | 0.028 | 0.375 | 1.73e+05 | 60 |
| clinical | 6 | zz_reps1 | 80×80 | 1.000 | 0.030 | 0.029 | 0.047 | 0.025 | 0.147 | 1.81e+01 | 76 |
| clinical | 6 | zz_reps2 | 80×80 | 1.000 | 0.023 | 0.025 | 0.031 | 0.020 | 0.136 | 7.36e+00 | 76 |
| clinical | 8 | z_reps1 | 80×80 | 1.000 | 0.055 | 0.031 | 0.245 | 0.019 | 0.389 | 8.99e+07 | 80 |
| clinical | 8 | zz_reps1 | 80×80 | 1.000 | 0.014 | 0.012 | 0.035 | 0.011 | 0.156 | 1.40e+01 | 80 |
| clinical | 8 | zz_reps2 | 80×80 | 1.000 | 0.008 | 0.008 | 0.012 | 0.008 | 0.122 | 5.55e+00 | 80 |
| pca | 4 | z_reps1 | 80×80 | 1.000 | 0.100 | 0.083 | 0.268 | 0.065 | 0.333 | 1.00e+06 | 80 |
| pca | 6 | z_reps1 | 80×80 | 1.000 | 0.032 | 0.022 | 0.110 | 0.018 | 0.255 | 1.76e+02 | 80 |
| pca | 8 | z_reps1 | 80×80 | 1.000 | 0.012 | 0.006 | 0.048 | 0.005 | 0.190 | 2.03e+01 | 80 |

For the frozen `z_reps1` eight-clinical-variable kernel, the weaker within-class minus between-class similarity gap is +0.011. Centered kernel-target alignment is 0.389. The matrix has effective rank 80/80 and positive-spectrum condition number 8.99e+07. These diagnostics describe separability and numerical structure; they do not establish quantum advantage.
