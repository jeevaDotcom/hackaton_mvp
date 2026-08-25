# “Where Is the Quantum Advantage?”

## Hardest question — “If classical ML is faster and slightly better, why use quantum at all?”

### 10-second version

“Quantum was the hypothesis under test. The useful result is knowing exactly where QSVC stayed competitive—and where classical evidence says not to invest further.”

### 30-second version

“We did not choose quantum because we assumed it would win; we tested that hypothesis fairly. QSVC stayed within our internal tolerance at reduced CKD feature budgets, so there is a narrow positive result. But classical SVM was slightly stronger, about 464 times faster, and more robust in the tested stresses. Neither model retained reliable discrimination on BD-KDD. That complete answer is scientifically useful because it prevents an unjustified quantum deployment claim.”

### 60-second technical version

“QSVC was included as a falsifiable research hypothesis: can a fidelity quantum kernel remain competitive with a strong classical kernel when folds, preprocessing, regularisation, and feature dimensions are identical? At eight CKD variables it reached 0.985 sensitivity and approximately 0.999 ROC-AUC, within the predefined 0.05 descriptive tolerance of RBF SVM. That justifies further study of the representation, not deployment. Exact statevector evaluation was about 464 times slower, QSVC degraded more under missingness and perturbation, and showed no small-sample advantage. On BD-KDD, RBF SVM and QSVC AUCs were 0.511 and 0.525, both intervals included chance, and target comparability was partial. The value is the decision: Q-CARE identifies a narrow internal competitive result while showing no performance, efficiency, robustness, or transportability investment case.”

## 10-second answer

“We did not demonstrate quantum advantage. QSVC was internally competitive, but much slower and less robust; Q-CARE makes that evidence explicit.”

## 20–30-second answer

“We did not demonstrate quantum advantage, and we deliberately do not claim one. On this dataset, QSVC remained competitive at reduced feature budgets but was hundreds of times slower and less robust in several stress tests. Q-CARE’s contribution is that it measures this honestly instead of assuming quantum superiority. That evidence is essential before healthcare QML can move toward real deployment.”

## 30-second answer

“There is no demonstrated quantum advantage here. With identical features and folds, QSVC remained within a predefined 0.05 tolerance at eight and six CKD variables, which is a useful positive result. But it was roughly 464 to 477 times slower in exact simulation, classical SVM was more robust, and neither model retained reliable BD-KDD discrimination. The contribution is not a superiority claim; it is an evidence framework that distinguishes a competitive result from an advantageous or deployable one.”

## 60-second technical answer

“We use ‘competitive’ in a narrow, predefined descriptive sense: across sensitivity, specificity, F1, and ROC-AUC, QSVC could be no more than 0.05 below the matched RBF SVM. It met that rule at eight- and six-variable clinical budgets in repeated internal CKD cross-validation. That does not establish statistical superiority, clinical non-inferiority, speed-up, or generalisation. Exact statevector kernel evaluation was approximately 464 times slower at eight features and 477 times slower at six. QSVC degraded more under missingness and perturbation and showed no small-sample advantage. On BD-KDD, both model AUC intervals included chance and the paired difference included zero. So the honest answer is no quantum advantage was demonstrated. Q-CARE’s technical contribution is a paired, leakage-aware evaluation layer that makes positive and negative evidence equally auditable.”

## Evidence

`artifacts/phase3/reference_cv_summary.csv`; `artifacts/quantum_paired_comparison_summary.csv`; `reports/root_cause/external_auc_bootstrap.md`; `reports/root_cause/target_definition_audit.md`.
