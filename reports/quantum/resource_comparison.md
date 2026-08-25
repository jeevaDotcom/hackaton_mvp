# Classical and quantum resource comparison

Wall times were measured locally and include no cloud queue time. QSVC training wall time includes quantum-kernel construction; model-fit time after kernel construction is retained in the CSV. Ideal CV used exact cached statevectors. Aer finite-shot/noise timings are reported separately in the Phase 2 results.

| Representation | Budget | Model | Map | Qubits | Depth | Reps | Train K shape | Infer K shape | Train s | Predict s | Kernel s | Train evals | Infer evals | Train ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| clinical | 4 | classical_rbf_svm | rbf | 0 | 0 | 0 | NR | NR | 0.0007 | 0.0003 | 0.0000 | 0 | 0 | 1.0 |
| clinical | 4 | qsvc | z_reps1 | 4 | 2 | 1 | 256×256 | 64×256 | 0.2721 | 0.1019 | 0.2715 | 32640 | 16384 | 370.2 |
| clinical | 4 | qsvc | zz_reps1 | 4 | 17 | 1 | 256×256 | 64×256 | 0.3584 | 0.1067 | 0.3577 | 32640 | 16384 | 487.6 |
| clinical | 4 | qsvc | zz_reps2 | 4 | 31 | 2 | 256×256 | 64×256 | 0.4312 | 0.1326 | 0.4305 | 32640 | 16384 | 586.6 |
| clinical | 6 | classical_rbf_svm | rbf | 0 | 0 | 0 | NR | NR | 0.0007 | 0.0002 | 0.0000 | 0 | 0 | 1.0 |
| clinical | 6 | qsvc | z_reps1 | 6 | 2 | 1 | 256×256 | 64×256 | 0.3139 | 0.1077 | 0.3133 | 32640 | 16384 | 476.6 |
| clinical | 6 | qsvc | zz_reps1 | 6 | 29 | 1 | 256×256 | 64×256 | 0.4559 | 0.1420 | 0.4551 | 32640 | 16384 | 692.2 |
| clinical | 6 | qsvc | zz_reps2 | 6 | 49 | 2 | 256×256 | 64×256 | 0.6304 | 0.1854 | 0.6294 | 32640 | 16384 | 957.1 |
| clinical | 8 | classical_rbf_svm | rbf | 0 | 0 | 0 | NR | NR | 0.0007 | 0.0002 | 0.0000 | 0 | 0 | 1.0 |
| clinical | 8 | qsvc | z_reps1 | 8 | 2 | 1 | 256×256 | 64×256 | 0.3464 | 0.1139 | 0.3457 | 32640 | 16384 | 464.1 |
| clinical | 8 | qsvc | zz_reps1 | 8 | 41 | 1 | 256×256 | 64×256 | 0.6484 | 0.1932 | 0.6476 | 32640 | 16384 | 868.9 |
| clinical | 8 | qsvc | zz_reps2 | 8 | 67 | 2 | 256×256 | 64×256 | 1.0001 | 0.2700 | 0.9992 | 32640 | 16384 | 1340.1 |
| pca | 4 | classical_rbf_svm | rbf | 0 | 0 | 0 | NR | NR | 0.0007 | 0.0002 | 0.0000 | 0 | 0 | 1.0 |
| pca | 4 | qsvc | z_reps1 | 4 | 2 | 1 | 256×256 | 64×256 | 0.2787 | 0.0997 | 0.2781 | 32640 | 16384 | 427.8 |
| pca | 6 | classical_rbf_svm | rbf | 0 | 0 | 0 | NR | NR | 0.0007 | 0.0002 | 0.0000 | 0 | 0 | 1.0 |
| pca | 6 | qsvc | z_reps1 | 6 | 2 | 1 | 256×256 | 64×256 | 0.3193 | 0.1080 | 0.3187 | 32640 | 16384 | 437.9 |
| pca | 8 | classical_rbf_svm | rbf | 0 | 0 | 0 | NR | NR | 0.0007 | 0.0002 | 0.0000 | 0 | 0 | 1.0 |
| pca | 8 | qsvc | z_reps1 | 8 | 2 | 1 | 256×256 | 64×256 | 0.3481 | 0.1176 | 0.3473 | 32640 | 16384 | 480.5 |
