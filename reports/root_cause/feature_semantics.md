# Frozen Feature Semantics Audit

## Decision

No documented unit or schema mismatch was found. Six mappings are exact. Hemoglobin and packed-cell volume are **likely matches**, because the UCI source description omits a denominator/unit that BD-KDD states explicitly. This is a documentation limitation, not measured evidence of a conversion mismatch.

| UCI feature | UCI meaning | UCI unit/category | BD-KDD feature | BD-KDD meaning | BD-KDD unit/category | Mapping confidence | Transformation |
|---|---|---|---|---|---|---|---|
| hemo | Hemoglobin | `hemo in gms` (denominator not stated) | Hemo | Hemoglobin level | g/dL | LIKELY MATCH | No conversion |
| al | Urine albumin | ordinal 0–5 | Al | Urine albumin level | 0–5 scale | EXACT MATCH | Numeric identity |
| dm | Diabetes mellitus | yes/no | Dm | Diabetes mellitus status | 0=no, 1=yes | EXACT MATCH | 0→no; 1→yes; one-hot |
| sg | Urine specific gravity | 1.005–1.025 nominal levels | Sg | Urine specific gravity | 1.005–1.025 | EXACT MATCH | Numeric identity |
| pcv | Packed cell volume | numeric; unit not stated | Pcv | Packed cell volume | percent | LIKELY MATCH | No conversion |
| appet | Appetite | good/poor | Appet | Appetite condition | 0=poor, 1=good | EXACT MATCH | 0→poor; 1→good; one-hot |
| htn | Hypertension | yes/no | Htn | Hypertension status | 0=no, 1=yes | EXACT MATCH | 0→no; 1→yes; one-hot |
| sc | Serum creatinine | mg/dL (source writes mgs/dl) | Sc | Serum creatinine | mg/dL | EXACT MATCH | Numeric identity |

## Qualification

The mapping is syntactically and clinically plausible, but source dictionaries cannot prove laboratory calibration, assay practice, coding practice, or target-assignment equivalence across hospitals. The experiment remains a full-signature cross-cohort stress test rather than clean clinical external validation.
