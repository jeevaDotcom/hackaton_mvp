1. **Best full-feature classical model:** random_forest.
2. **Full-feature CV sensitivity:** 1.000 (repeated nested-CV mean).
3. **Full-feature CV ROC-AUC:** 1.000 (repeated nested-CV mean).
4. **Best stable 8-variable signature:** hemo, al, dm, sg, pcv, appet, htn, sc; method wrapper_rfe; meets the predeclared stability rule.
5. **Best stable 6-variable signature:** hemo, al, dm, sg, pcv, appet; method wrapper_rfe; meets the predeclared stability rule.
6. **Best stable 4-variable signature:** hemo, pcv, rc, sc; method mutual_information; meets the predeclared stability rule.
7. **Stability score for each:** 4 variables Jaccard=0.920; 6 variables Jaccard=0.848; 8 variables Jaccard=0.912.
8. **Performance delta at each feature budget:** 4: sensitivity -0.028, specificity -0.033, ROC-AUC -0.016; 6: sensitivity +0.000, specificity -0.021, ROC-AUC -0.000; 8: sensitivity +0.010, specificity -0.004, ROC-AUC +0.000.
9. **Whether 8 variables meet the predefined 0.05 tolerance:** Yes.
10. **Whether 6 variables meet the predefined 0.05 tolerance:** Yes.
11. **Whether 4 variables meet the predefined 0.05 tolerance:** Yes.
12. **Selected clinical-feature strategy for Phase 2:** use the stable eight-variable signature as the primary interpretable representation, the stable six-variable signature as the aggressive-reduction comparison, and the stable four-variable signature only as a stress test because locked sensitivity fell to 0.880; keep the same locked IDs.
13. **Selected PCA configurations for Phase 2:** 8, 6 and 4 components fitted inside each training fold; the development-leading locked-test control uses 6 components with logistic_regression.
14. **Locked-test results:** best_pca_control: sensitivity 0.920, specificity 0.967, ROC-AUC 0.997; full_reference: sensitivity 0.980, specificity 1.000, ROC-AUC 1.000; selected_4: sensitivity 0.880, specificity 0.967, ROC-AUC 0.967; selected_6: sensitivity 0.960, specificity 1.000, ROC-AUC 1.000; selected_8: sensitivity 0.980, specificity 1.000, ROC-AUC 1.000.
15. **Largest uncertainty:** only 80 locked-test patients (50 CKD/30 not-CKD), yielding discrete, wide bootstrap intervals and no external/site validation.
16. **Any evidence of leakage or instability:** no train/outer-validation or development/locked-ID overlap was found; stability outcomes were 4: stable, 6: stable, 8: stable.
17. **GO / MODIFY / ABANDON reduced-feature hypothesis:** **GO** for the eight- and six-variable hypothesis; do not promote four variables as sufficient after its locked sensitivity fell to 0.880. This remains an engineering benchmark, not clinical non-inferiority.
18. **Exact inputs Phase 2 should send to QSVC:** selected-4: hemo, pcv, rc, sc; selected-6: hemo, al, dm, sg, pcv, appet; selected-8: hemo, al, dm, sg, pcv, appet, htn, sc; PCA: 8, 6 and 4 fold-fitted latent components from all 24 source variables.
