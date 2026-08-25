# Phase 3 decision — 20 frozen answers

1. Yes, descriptively within the frozen 0.05 tolerance: 8-variable QSVC sensitivity 0.985 and ROC-AUC 0.999, but every paired mean delta favours SVM; this is competitiveness, not non-inferiority.
2. Yes, descriptively within 0.05: 6-variable QSVC sensitivity 0.977 and ROC-AUC 0.995, again without superiority.
3. The classical SVM was more robust to added missingness: at 20%, mean sensitivity was 0.962 versus 0.930 and ROC-AUC 0.998 versus 0.986.
4. The classical SVM was more stable under numeric perturbation: at 10% SD noise, mean flip rate was 0.2% versus 0.9% for QSVC.
5. Sensitivity/specificity stayed comparatively stable under resampling; QSVC precision rose from about 0.952 at 30% prevalence to 0.991 at 70%, demonstrating prevalence dependence.
6. No. QSVC is classification-score only; leakage-safe calibration is internally descriptive and does not validate an absolute clinical risk probability.
7. Yes. BD-KDD supplied all eight variables with traceable public provenance and CC0 licensing, but later target audit rated comparability PARTIAL.
8. Frozen cross-cohort stress test: classical sensitivity/specificity/AUC 0.986/0.004/0.511 [0.475-0.546]; QSVC 0.992/0.010/0.525 [0.489-0.561]. Both were indistinguishable from chance and their paired difference included zero.
9. Cleveland 8-variable methodology validation: classical sensitivity/AUC 0.784/0.898; QSVC 0.767/0.860; overall tolerance missed on specificity.
10. Pima methodology validation: classical sensitivity/AUC 0.526/0.833; QSVC 0.043/0.653; QSVC was not competitive. Pima is an Arizona population, not Indian population.
11. It strengthens the evidence-first platform story because the method exposes both close and failed comparisons; it weakens any broad claim of QSVC competitiveness across diseases.
12. Strongest supported claim: a reproducible, identical-feature-budget quantum/classical healthcare benchmark with explicit robustness and shift limits.
13. Strongest unsupported claim: quantum outperforms, accelerates, or clinically validates classical disease detection.
14. Final positioning: evidence-first quantum healthcare benchmarking platform.
15. Final input count: 8 primary variables; 6 retained only as an optional compact research benchmark.
16. Final classical comparator: RBF SVM, C=0.5, gamma=scale, with the identical training-fold preprocessing and features.
17. Final QSVC: ZFeatureMap, 1 repetition, no entanglement, C=0.5, exact local statevector fidelity.
18. Remove diagnosis/confirmation language, risk percentages, clinical recommendations, treatment advice, quantum advantage/speed claims, and unsupported cost-reduction claims.
19. The dashboard may show frozen CV/locked-test metrics with provenance, runtime/resource comparison, robustness curves, the BD-KDD cross-cohort transportability failure, class labels, and signed decision scores.
20. MODIFY: keep the project, but pivot/freeze it as the evidence-first benchmarking platform; do not proceed as a clinical screening product.
