# Cross-disease methodology validation

These experiments validate the benchmark method, not one universal clinical model. Cleveland used a disease-specific 13-variable full classical baseline and mutual-information rankings learned inside each outer training fold for the matched 8/6-variable comparisons. Pima used all eight source predictors and disease-specific missing-code handling. All comparisons used identical 5-fold × 2-repeat partitions within each dataset.

| Dataset | Disease | Original features | Reduced/features used | Classical sensitivity | QSVC sensitivity | Classical ROC-AUC | QSVC ROC-AUC | 0.05 tolerance met? | Fit-time ratio | Primary conclusion |
|---|---|---|---|---|---|---|---|---|---|---|
| UCI CKD | Chronic kidney disease | 24 | 8 | 1.000 | 0.985 | 1.000 | 0.999 | Yes | 317.1× | Internally competitive within 0.05; no superiority |
| UCI CKD | Chronic kidney disease | 24 | 6 | 0.998 | 0.977 | 1.000 | 0.995 | Yes | 478.4× | Internally competitive within 0.05; no superiority |
| UCI Cleveland | Heart disease | 13 | 8 | 0.784 | 0.767 | 0.898 | 0.860 | No | 352.9× | Sensitivity/AUC close; specificity tolerance missed |
| UCI Cleveland | Heart disease | 13 | 6 | 0.767 | 0.734 | 0.880 | 0.827 | No | 203.9× | AUC and specificity tolerance missed |
| OpenML 37 / UCI Pima | Diabetes | 8 | 8 | 0.526 | 0.043 | 0.833 | 0.653 | No | 498.3× | QSVC sensitivity collapsed; tolerance missed |

Heart 8-feature selection frequency: {'thal': 10, 'thalach': 8, 'slope': 9, 'cp': 10, 'sex': 5, 'oldpeak': 10, 'fbs': 1, 'ca': 10, 'chol': 6, 'exang': 8, 'restecg': 1, 'age': 1, 'trestbps': 1}. Mean pairwise Jaccard stability across outer folds: 0.709. This is moderate evidence that dimensionality constraints can be studied honestly across diseases; it is not proof of quantum advantage or clinical transportability.
