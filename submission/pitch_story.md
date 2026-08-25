# Winning Story

## Final one-line pitch

**Q-CARE is an evidence-first hybrid quantum healthcare benchmark that tests quantum ML against a matched classical baseline—and reveals when runtime, robustness, or cross-cohort transportability breaks the result.**

## Opening line

**“99.9% ROC-AUC sounds excellent. But what happens when the hospital changes?”**

## The problem

Biomedical ML projects can look exceptional on familiar benchmark datasets. That does not establish robustness, generalisation, clinical reliability, or the usefulness of a quantum method. If the only visible number is the best internal score, the most consequential failure may stay hidden.

## The question

**When does quantum machine learning actually add value?**

Q-CARE asks that question under controlled feature budgets, consistent resampling, robustness tests, computational accounting, and a frozen cross-cohort stress test.

## The platform

Q-CARE is an evidence-first hybrid quantum healthcare benchmarking platform. It gives classical RBF SVM and fidelity-kernel QSVC the same variables, folds, and preprocessing boundaries, then tests what survives missingness, measurement perturbation, less training data, cross-cohort transport, and new disease datasets.

## The hero experiment

The primary UCI CKD dataset begins with 400 records and 24 predictors. Training-partition selection identifies a stable eight-variable clinical representation. At that identical budget, classical RBF SVM is compared directly with QSVC.

## The positive result

QSVC reaches **0.985 sensitivity** in development-only 5-fold cross-validation repeated 10 times. Classical sensitivity is **1.000**. QSVC remains within the predefined 0.05 descriptive competitiveness tolerance at both eight and six variables.

This supports a narrow conclusion: low-depth QSVC can remain internally competitive on this controlled, reduced-feature benchmark.

## The cost

At eight variables, exact local statevector QSVC training is approximately **464× slower** than the matched classical SVM. The platform displays this beside predictive performance instead of treating compute as invisible.

## The stress tests

Classical SVM degrades less under added missingness and measurement perturbation. QSVC shows no small-sample advantage in the tested training-size experiment.

## The reveal

Internal CKD ROC-AUC is approximately **1.000** for RBF SVM and **0.999** for QSVC. On the BD-KDD cross-cohort stress test, the corresponding AUCs are **0.511 [0.475-0.546]** and **0.525 [0.489-0.561]**. Neither reliably exceeds chance, and their paired difference includes zero.

Target comparability is **PARTIAL**, and all eight internally predictive UCI feature-label associations flatten toward chance in BD-KDD. External transport failure reflected both target/cohort differences and changed feature–target relationships; therefore the experiment demonstrates transportability risk but cannot isolate pure conditional shift.

## The broader evidence

Method transfer is mixed for Cleveland heart disease and poor for Pima diabetes. The outcomes are reported separately rather than averaged into a reassuring headline.

## The value

Q-CARE does not stop at “How accurate is the quantum model?” It asks:

- Is the comparison fair?
- Is the result robust?
- Is the computation efficient?
- Does the result generalise?
- Is the claim supported by a frozen artifact?

## The ending

**Q-CARE does not assume quantum is better. It produces the evidence needed to decide when quantum healthcare models deserve further investment—and when they do not.**
