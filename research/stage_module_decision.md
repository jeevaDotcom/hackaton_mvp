# CKD stage research module decision

## Current model target

Q-CARE's frozen RBF-SVM, QSVC, and VQC workflows evaluate a binary experimental target: CKD-like versus non-CKD-like pattern.

## Current staging status

CKD Stage 1–5 prediction is **not validated and not available in the current Q-CARE model**. No stage values are produced for single profiles, OCR-confirmed profiles, or CSV batch rows.

## Why

The current artifacts do not contain a stage-labelled training target, a separate stage-specific model, or stage-specific internal and external validation. A binary classification output cannot answer the clinically different question of which CKD stage applies. A raw model score, isolated creatinine value, or OCR-extracted laboratory value cannot safely be converted into a stage.

## Responsible scope control

Allowed wording:

- “Stage cannot be inferred from the current Q-CARE binary classifier.”
- “Stage 1–5 prediction is not validated in the current Q-CARE model.”

Prohibited as current model output:

- “Predicted CKD Stage 3”
- “Likely Stage 4”
- “Model score indicates Stage 2”

Those phrases may appear only when explicitly describing unsupported claims that Q-CARE refuses to make.

## What would be required

A separate research program would need an appropriately stage-labelled and clinically harmonized cohort, required staging measurements and metadata, a stage-specific target definition, training-only preprocessing, a separate staging model, internal validation, calibration where appropriate, external validation, and clinical governance.

This phase deliberately does not implement KDIGO rules, eGFR calculation, treatment guidance, referral logic, or any clinical decision rule.

## Checklist status

**Disease Stage: COMPLETE — RESPONSIBLE SCOPE CONTROL**

The unsupported Stage 1–5 prediction is blocked, the limitation is visible in the workstation and evidence report, and future validation requirements are documented. This does not mean a stage prediction model is complete.
