1. **Best QSVC configuration:** `z_reps1` with the frozen eight-variable clinical signature, C=0.5, exact statevector fidelity and full development-only repeated CV.
2. **Best feature-map configuration:** ZFeatureMap with reps=1 and entanglement=none; it first passed the joint 0.05 development tolerance across sensitivity, specificity, ROC-AUC and F1, then won the predefined lexicographic ranking.
3. **8-variable QSVC sensitivity:** 0.983 in repeated development CV; shared-test sensitivity 1.000.
4. **8-variable classical sensitivity:** 1.000 in identical-fold development CV; reused Phase 1 shared-test sensitivity 0.980.
5. **8-variable QSVC ROC-AUC:** 0.999 in development CV; shared-test ROC-AUC 1.000.
6. **8-variable classical ROC-AUC:** 1.000 in development CV; reused Phase 1 shared-test ROC-AUC 1.000.
7. **8-variable 0.05 tolerance:** met across mean sensitivity, specificity, ROC-AUC and F1 deltas; this is an experimental tolerance, not clinical non-inferiority.
8. **6-variable answers:** QSVC sensitivity 0.975 and ROC-AUC 0.994; classical sensitivity 1.000 and ROC-AUC 1.000; tolerance met; shared-test sensitivities QSVC/classical 0.920/0.960.
9. **4-variable stress test:** QSVC sensitivity 0.895, specificity 0.887, ROC-AUC 0.950; classical sensitivity 0.960; this representation remains a stress test and is not promoted.
10. **Selected-feature vs PCA quantum result:** QSVC clinical/PCA sensitivity was 0.983/0.973 at 8, 0.975/0.938 at 6, and 0.895/0.910 at 4 dimensions.
11. **Quantum vs classical runtime ratio:** mean training ratios were 464.1× at 8 clinical variables and 476.6× at 6; ideal local statevector acceleration and classical CPU timing make these machine-specific lower-bound simulator ratios.
12. **8-qubit vs 6-qubit resource difference:** depth 2 vs 2 (+0), gates 16 vs 12 (+4), and qubits 8 vs 6.
13. **Training-size robustness:** over the 25% and 50% development-training conditions, QSVC minus classical mean sensitivity was -0.054 and ROC-AUC was -0.003; no small-sample advantage is inferred without external repetition.
14. **Finite-shot conclusion:** across 256/1024/4096 shots and three seeds, mean sensitivity/F1 deltas from ideal were +0.000/+0.000; shot count did not create a reliable predictive improvement.
15. **Noise conclusion:** under the synthetic moderate Aer condition, mean sensitivity/F1 degradation from the noiseless finite-shot reference was +0.000/+0.000; these are simulator robustness results, not hardware validation.
16. **Kernel diagnostic conclusion:** the frozen 8-variable kernel had centered alignment 0.389, effective rank 80/80, positive-spectrum condition number 8.99e+07, and between-class similarity 0.019.
17. **Measurable QSVC benefit:** the most favorable mean sensitivity delta was -0.010 for pca at 8 dimensions; it is treated as NOT SUPPORTED rather than quantum advantage.
18. **Measurable QSVC disadvantage:** the least favorable sensitivity delta was -0.083 for pca at 4 dimensions, and every frozen QSVC representation had runtime utility labeled NOT SUPPORTED.
19. **Feature-efficient QML claim:** survives only as a competitiveness claim at the fixed 8/6 budgets; it does not support accuracy superiority or quantum advantage.
20. **Quantum Utility Score:** not justified; predictive, dimensional, runtime, finite-shot and noise evidence should remain separate because any weighting would be arbitrary and cosmetic.
21. **VQC decision:** **NO-GO** for this phase; the QSVC evidence does not identify a limitation that variational training would clearly resolve, while adding optimization variance and cost would not strengthen the central claim.
22. **Recommended hackathon headline:** At fixed low-dimensional clinical inputs, an exact-simulator QSVC was tested as a transparent competitiveness-and-cost benchmark against a near-ceiling RBF SVM.
23. **Claims we must NOT make:** quantum advantage, clinical non-inferiority, hardware readiness, diagnostic deployment readiness, causal biomarker discovery, external validity, or superiority derived from this single 400-row dataset.
24. **Phase 3 recommendation:** proceed with an evidence-first comparison interface and external/shift validation planning using the frozen classical and QSVC artifacts; keep VQC out unless a separately preregistered scientific question emerges.
