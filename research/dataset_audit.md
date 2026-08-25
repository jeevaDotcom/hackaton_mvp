# Dataset audit

Audit date: 24 August 2026. Suitability is scored out of 5 for this specific 24–36 hour research project, not as a judgment of general clinical value. “Public raw” means de-identified row-level data can actually be downloaded without a data-use application.

## Recommendation

- **Primary:** UCI Chronic Kidney Disease (CKD), because it is small enough for quantum simulation, Indian-origin, patient-level, openly licensed, traceable to Apollo Hospitals in Karaikudi, and already supports an exact-dataset literature comparison.
- **Secondary validation:** UCI Cleveland Heart Disease for a compact cross-disease reproducibility check; the CC BY Indian West Bengal non-obese T2DM cohort for population relevance if its file schema passes an implementation audit.
- **Do not replace the primary dataset.** The stronger Indian diabetes candidate has a distinct phenotype and variable set. The downloadable Indian heart candidate has an unnamed hospital and therefore weaker provenance than Cleveland. Both are better treated as supplementary stress tests.
- **Pima is not Indian.** “Pima Indians” refers to an Indigenous population near Phoenix, Arizona, USA—not a population in India.

## 1. UCI Chronic Kidney Disease — recommended primary (5.0/5)

| Field | Audit result |
|---|---|
| Dataset / institution | Early stage of Indians Chronic Kidney Disease; source clinician Dr P. Soundarapandian, Apollo Hospitals; creator L. Jerlin Rubini, Alagappa University |
| Original source | [UCI record and archive, DOI 10.24432/C5G020](https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease) |
| Publication / academic source | UCI archive metadata is the primary provenance record. Rashed-Al-Mahfuz et al. 2021 independently identify the source as Apollo Hospitals, Tamil Nadu ([paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC8075287/)). |
| Country / population | India; patients assessed for CKD |
| Collection location | The archive itself states **Apollo Hospitals, Managiri, Madurai Main Road, Karaikudi, Tamil Nadu, India**. This resolves inconsistent secondary descriptions; do not call it Chennai. |
| Sample / predictors / target | 400 rows; 24 predictors plus binary `class`; 250 CKD, 150 not-CKD |
| Numeric / categorical | Repository: 11 numeric, 13 categorical predictors; target categorical. Specific gravity, albumin and sugar are ordered discrete fields despite being declared nominal. |
| Features | `age`, `bp`, `sg`, `al`, `su`, `rbc`, `pc`, `pcc`, `ba`, `bgr`, `bu`, `sc`, `sod`, `pot`, `hemo`, `pcv`, `wc`/`wbcc`, `rc`/`rbcc`, `htn`, `dm`, `cad`, `appet`, `pe`, `ane` |
| Missing profile | Archive audit: 1,012 explicit `?` cells; 242/400 rows have at least one `?`, 158 are complete. Counts by field: age 9, bp 12, sg 47, al 46, su 49, rbc 152, pc 65, pcc 4, ba 4, bgr 44, bu 19, sc 17, sod 87, pot 88, hemo 52, pcv 71, wc 106, rc 131, htn 2, dm 2, cad 2, appet 1, pe 1, ane 1. The raw ARFF also has tabs/whitespace, two trailing delimiters and one malformed categorical row; an ingestion test must catch these. |
| Licence / download | CC BY 4.0; official archive download; de-identified patient rows are available |
| Published ML use | Extensive: SVM, LR, RF, gradient boosting/XGBoost, feature selection, cost-sensitive selection and SHAP |
| Published QML use | Yes: QSVM/QSVC, quantum kernels, VQC, QNN/HQNN, PCA/SVD and shot/design-space studies (see `benchmark_matrix.md`) |
| Strengths | Exact Indian provenance; open licence; modest size; heterogeneous clinical variables; large benchmark literature; computationally feasible |
| Limitations | Very small, single-site, old, missing-heavy, no external cohort identifiers or collection dates, unclear clinical inclusion/label adjudication, possible duplicates not documented, vulnerable to leakage and optimistic confidence intervals; not evidence of deployable screening performance |

## 2. UCI Cleveland Heart Disease — recommended compact secondary (4.2/5)

| Field | Audit result |
|---|---|
| Dataset / institution | Processed Cleveland subset of UCI Heart Disease; Cleveland Clinic Foundation; principal investigator Robert Detrano |
| Original source | [UCI record, DOI 10.24432/C52P4X](https://archive.ics.uci.edu/dataset/45/heart+disease) |
| Publication | Detrano et al. 1989, [DOI 10.1016/0002-9149(89)90524-9](https://doi.org/10.1016/0002-9149(89)90524-9) |
| Country / location | United States; Cleveland Clinic Foundation, Cleveland, Ohio |
| Sample / predictors / target | 303 rows; 13 predictors; `num` 0–4. Standard binary task is 0 (absence) versus 1–4 (presence). Raw processed distribution: 164/139. |
| Numeric / categorical | Numeric/continuous-like: age, trestbps, chol, thalach, oldpeak (5). Categorical/ordinal-coded: sex, cp, fbs, restecg, exang, slope, ca, thal (8). |
| Features | `age`, `sex`, `cp`, `trestbps`, `chol`, `fbs`, `restecg`, `thalach`, `exang`, `oldpeak`, `slope`, `ca`, `thal` |
| Missing profile | Six cells in the official processed file: `ca` 4 and `thal` 2. Complete-case analyses therefore use 297 rows, and class counts can change. Papers reporting 165/138 use a transformed/mirrored label version and must not be conflated with the official processed file. |
| Licence / download | CC BY 4.0; official row-level archive is downloadable |
| Published ML / QML use | Extensive classical use. Exact-dataset QSVC, QNN, VQC and bagged-QSVC published. |
| Strengths | Traceable, standard, compact, open, nearly complete, clear angiographic endpoint |
| Limitations | Not Indian; old and single-centre; only 303 rows; target binarisation differs among papers; invasive/diagnostic predictors make an “early low-cost screen” interpretation inappropriate |

## 3. Pima Indians Diabetes — baseline only, not India (3.0/5)

| Field | Audit result |
|---|---|
| Dataset / institution | Pima Indians Diabetes; source research associated with the US National Institute of Diabetes and Digestive and Kidney Diseases |
| Original source / paper | Smith et al. 1988, [PMC2245318](https://pmc.ncbi.nlm.nih.gov/articles/PMC2245318/) |
| Country / population / location | **United States, not India**; Pima Indian women aged at least 21 near Phoenix, Arizona |
| Sample / predictors / target | 768 women; 8 predictors; 268 diabetes-positive, 500 negative; onset of diabetes within five years in the source task |
| Numeric / categorical | Eight numeric/count predictors; binary target |
| Features | pregnancies, 2-hour plasma glucose, diastolic blood pressure, triceps skinfold thickness, 2-hour serum insulin, BMI, diabetes pedigree function, age |
| Missing profile | Common CSVs encode physiologically impossible zeros rather than `NA` in glucose, blood pressure, skinfold, insulin and BMI. Exact zero counts must be recomputed from the selected source file because mirrors and cleaned versions differ. |
| Licence / download | Row-level CSV is widely downloadable from mirrors; a current authoritative raw repository and reuse licence chain equivalent to UCI CC BY were **UNVERIFIED**. Do not redistribute until the chosen copy's terms are checked. |
| Published ML / QML use | Very extensive classical use; QSVC, VQC and other QML studies exist, including resource/feature-map sweeps |
| Strengths | Compact, familiar, binary, 8-dimensional and therefore inexpensive for simulation |
| Limitations | Not Indian; all-female, population-specific and historical; zero-as-missing issue; mirror/version ambiguity; heavily benchmarked, leaving little novelty |

## 4. Indian West Bengal non-obese T2DM community cohort — recommended Indian secondary (4.1/5, conditional)

| Field | Audit result |
|---|---|
| Dataset / institution | Community Health Cohort in “Non-obese T2DM Machine Learning Analysis”; CSIR–Indian Institute of Chemical Biology, Kolkata |
| Original source | [Mendeley Data v2, DOI 10.17632/c2mcxfw5m5.2](https://data.mendeley.com/datasets/c2mcxfw5m5/2) |
| Publication | Sarkar et al. 2019, [DOI 10.1177/2042018819889024](https://doi.org/10.1177/2042018819889024) |
| Country / location | India; community metabolic-health programme with SWANIRVAR in West Bengal; laboratory/institutional work in Kolkata |
| Sample / target | Repository description: 714 subjects—221 treatment-naive T2DM, 493 healthy (257 male, 457 female). The source paper's analytic cohort is 650 after exclusions, so the exact file-to-paper flow must be reconciled. |
| Features | Repository bundles multiple files. Community variables include age, sex, height/weight/BMI, waist circumference, body-fat percentage, fasting glucose, fasting insulin, cholesterol, triglycerides and leptin; HOMA-IR/HOMA-B may be derived. Exact selected file columns are **UNVERIFIED until ingestion**. |
| Numeric / categorical | Predominantly numeric biomarkers and anthropometrics plus categorical sex/label; exact file schema to verify |
| Missing / class distribution | Class distribution 221/493 at repository level. Feature-wise missingness is **UNVERIFIED until the downloadable workbook/CSV is audited**. |
| Licence / download | CC BY 4.0; downloadable patient-level community cohort is described by the repository |
| Published ML / QML use | Classical ML analysis associated with the release; exact-dataset QML use was **not found in reviewed literature** |
| Strengths | Indian, open, traceable, mixed-sex, treatment-naive phenotype, useful population-relevance check |
| Limitations | Different target/phenotype from CKD; modest size; paper/repository cohort counts differ; bundled cleaned national surveys can be confused with the community cohort; derived HOMA variables could leak label-defining physiology; not a direct external validation of a CKD model |

## 5. Mendeley Cardiovascular_Disease_Dataset — supplementary candidate, not replacement (3.2/5)

| Field | Audit result |
|---|---|
| Dataset / institution | Cardiovascular_Disease_Dataset by Doppala & Bhattacharyya; stated to come from one multispecialty hospital in India; hospital and city are unnamed |
| Original source | [Mendeley Data, DOI 10.17632/dzz48mvjht.1](https://data.mendeley.com/datasets/dzz48mvjht/1) |
| Publication | Doppala et al. 2022, [DOI 10.1155/2022/2585235](https://doi.org/10.1155/2022/2585235) |
| Country / location | India; exact hospital/location **UNVERIFIED** |
| Sample / predictors / target | 1,000 rows; repository-associated descriptions use 12 clinical predictors plus patient ID and binary target; 500/500 classes |
| Features | age, gender, resting blood pressure, serum cholesterol, fasting blood sugar, chest-pain type, resting ECG, maximum heart rate, exercise angina, oldpeak, ST slope, number of major vessels; ID and target |
| Numeric / categorical | Mixed numeric and categorical/ordinal; exact types must be inferred and validated from the CSV |
| Missing profile | Reported as complete in associated analyses, but a fresh raw audit is required |
| Licence / download | CC BY 4.0; row-level CSV publicly downloadable |
| Published ML / QML use | Published ensemble classical ML; exact-dataset QML use **not found in reviewed literature** |
| Strengths | Indian, balanced, open, larger than Cleveland, familiar tabular schema |
| Limitations | Unnamed source hospital and location weaken traceability; likely resembles/re-encodes common heart benchmark fields; collection protocol, dates, inclusion criteria and label adjudication are not adequately documented |

## 6. South-India 1,670-record CVD study — scientifically useful but ineligible here (2.4/5)

| Field | Audit result |
|---|---|
| Institution / source | Retrospective records acknowledged to Sagar Hospitals, Jayanagar, Bengaluru; [peer-reviewed paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC8282535/) |
| Population / sample | South Indian tertiary private hospital; 1,670 records, 893 CVD and 777 no-CVD; 13 predictors |
| Features | age, weight, height, total cholesterol, sex, hypertension, diabetes, alcohol, smoking, exercise, stress, family history, healthy diet |
| Missing | Authors report no missing values or outliers |
| Licence / raw availability | Article is open access, but a genuinely public raw patient-level download was **not found**. Article access is not dataset reuse permission. |
| Published use | LR, kNN, Naive Bayes, AdaBoost and RF; reported RF accuracy 93.8%, sensitivity 92.8%, specificity 94.6% under a single 70/30 split |
| Decision | Reject for the hackathon data pipeline unless the authors provide a public, permitted raw file. It fails the explicit download criterion. |

## Dataset decision table

| Candidate | Public raw | Traceable | Permissive licence | Suitable label | Quality / version risk | India relevance | Score | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| UCI CKD | Yes | High | CC BY 4.0 | Yes | Medium | High | 5.0 | Primary |
| Cleveland | Yes | High | CC BY 4.0 | Yes | Medium | None | 4.2 | Secondary reproducibility |
| Pima | Yes via mirrors | Medium | UNVERIFIED | Yes | High | None | 3.0 | Baseline only; do not call Indian |
| West Bengal T2DM cohort | Yes | High | CC BY 4.0 | Yes, different disease | Medium | High | 4.1 | Conditional Indian secondary |
| Mendeley Indian CVD | Yes | Low–medium | CC BY 4.0 | Yes | High | High | 3.2 | Supplementary only |
| South-India CVD 1,670 | No verified public file | High in paper | UNVERIFIED for data | Yes | Medium | High | 2.4 | Ineligible |

## Required ingestion gates before Phase 1

1. Preserve an immutable downloaded archive and checksum; record repository version/date.
2. Parse CKD with an explicit schema, trimming tabs/whitespace and rejecting unexpected column counts. Do not forward-fill clinical rows.
3. Recompute row count, class count, duplicate count, impossible values and field-wise missingness in a test.
4. Reconcile the one malformed CKD row and document the deterministic rule; do not silently shift columns.
5. Split labels before fitting any imputer, encoder, scaler, selector, PCA or resampler.
6. For every secondary dataset, map the clinical endpoint explicitly; never imply that a heart/diabetes experiment externally validates CKD predictions.

