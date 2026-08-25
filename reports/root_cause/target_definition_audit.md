# Target Definition Audit

## Decision

**Target comparability: PARTIAL.** The sources overlap at the broad concept of renal disease versus a negative/healthy label, but the available documentation does not establish a like-for-like chronic-kidney-disease endpoint. UCI names its classes `ckd` and `notckd` but does not report the diagnostic rule. BD-KDD reports physician/laboratory-based `Kidney Disease` and `Healthy` labels, which are broader than a documented chronic CKD definition, and reports no chronicity, eGFR, or staging rule. Cohort construction and control selection also differ or are incompletely documented.

This rating is based on documentation, not on observed feature values.

## Source-level comparison

| Audit item | UCI Chronic Kidney Disease | BD-KDD |
|---|---|---|
| Raw target labels | `ckd`, `notckd` | `0`, `1` |
| Canonical mapping used here | `ckd` → CKD; `notckd` → non-CKD | `1` (“kidney disease”) → CKD; `0` (“healthy”) → non-CKD |
| Intended outcome | Chronic kidney disease classification | Kidney disease classification |
| What determines the label? | **Not reported** in the official repository metadata | The article states that labels were based on clinical/physician evaluation in medical reports and laboratory findings |
| Clinician assigned? | **Not reported** | **Reported yes:** physician evaluation is part of the label description |
| Algorithmically derived? | **Not reported** | No algorithmic derivation is reported; the article describes physician/laboratory assessment |
| CKD staging involved? | **Not reported** | **Not reported** |
| Diagnostic criteria | **Not reported**; no eGFR, albuminuria, duration, or other formal rule is given | **Not reported**; no eGFR threshold, albuminuria rule, chronicity duration, or formal CKD criterion is given |
| Chronicity established? | Implied by the dataset title, but the evidentiary rule is **not reported** | **Not reported**; the documented positive label is the broader “Kidney Disease” |
| Negative/control construction | `notckd` is documented as a class; recruitment or verification criteria are **not reported** | `Healthy` records are documented, but how healthy controls were recruited or verified beyond the reported label is **not reported** |
| Inclusion rules | **Not reported** | Complete relevant/key laboratory results and a clear diagnostic label |
| Exclusion rules | **Not reported** | Missing critical laboratory values, contradictory/inconsistent records, duplicates, and incomplete diagnostic reports |
| Collection setting | Hospital data from Apollo Hospitals, Karaikudi, India; 400 records collected over approximately two months | Retrospective routine diagnostic/EMR data from Popular Diagnostic Center, Savar, Dhaka, Bangladesh; 988 records |
| Label counts | 250 `ckd`, 150 `notckd` | 507 raw `1`, 481 raw `0` |
| Disease severity comparability | No stage distribution is documented | No stage distribution is documented |

## Evidence supporting PARTIAL rather than HIGH

1. The positive-label wording differs: chronic kidney disease at UCI versus the broader kidney disease label at BD-KDD.
2. Neither source supplies enough diagnostic detail to prove that the same chronicity, eGFR, albuminuria, or staging standard was applied.
3. BD-KDD reports physician/laboratory assessment and explicit completeness exclusions; corresponding UCI label-assignment and cohort-selection rules are not documented.
4. `notckd` and `Healthy` may overlap semantically, but their recruitment and verification are not documented as equivalent.
5. The collections differ in country, centre, period/context, and record-selection process.

These limitations prevent a **HIGH** rating. The explicit disease/negative labels and shared renal focus provide more comparability than **LOW**, so **PARTIAL** is the most defensible classification. A clean, like-for-like clinical external validation is not established.

## Severity and the feature evidence

The feature audit shows a materially different renal-function cohort: for example, documented serum-creatinine medians are 0.90/2.25 mg/dL for UCI non-CKD/CKD and 7.10/7.71 mg/dL for BD-KDD non-CKD/CKD. This is evidence about observed cohort composition and label separation, not proof of how either label was assigned. No CKD stage is inferred from creatinine alone.

## Primary sources

- [UCI Chronic Kidney Disease dataset page](https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease), DOI [10.24432/C5G020](https://doi.org/10.24432/C5G020).
- [BD-KDD data article in Data in Brief](https://pmc.ncbi.nlm.nih.gov/articles/PMC13092092/), DOI [10.1016/j.dib.2026.112738](https://doi.org/10.1016/j.dib.2026.112738).
- [BD-KDD Harvard Dataverse record](https://doi.org/10.7910/DVN/MB1LES).

Sources checked 2026-08-25. “Not reported” means not found in the cited public dataset documentation/article; it does not mean the information never existed at the originating institutions.
