# Q-CARE CSV batch results

## Scope

The CSV Batch workflow is a research-only extension of the existing single-profile workstation. It does not train models, change frozen artifacts, infer disease stage, or produce disease probabilities.

## Mapping

Column suggestions are deterministic and use normalized case, whitespace, punctuation, underscores, and project aliases. Supported aliases include:

- `hemo`: hemo, haemoglobin, hemoglobin, hb, hgb
- `al`: al, albumin, urinary albumin, albumin ordinal, albumin grade
- `dm`: dm, diabetes, diabetes mellitus
- `sg`: sg, specific gravity, urine specific gravity, sp gravity
- `pcv`: pcv, packed cell volume, hematocrit, haematocrit, hct
- `appet`: appet, appetite
- `htn`: htn, hypertension
- `sc`: sc, serum creatinine, creatinine, s creatinine, creat

`Serum Albumin`, `Serum Alb`, and `S. Albumin` are marked ambiguous and are never automatically mapped to the dataset albumin ordinal feature. Researchers must review every mapping, and duplicate source-column assignments block execution.

## Validation

Each row is independently normalized and validated. Numeric fields must be finite and within the observed frozen development ranges; albumin must be an integer dataset grade from 0 to 5. Diabetes and hypertension accept `yes/no`, `y/n`, and `true/false`. Appetite accepts the frozen `good/poor` categories. Invalid rows remain in the result table with readable errors and receive no model output.

## Batch limit

The MVP accepts up to 1,000 rows per batch. Larger files are rejected with an instruction to split them into smaller batches.

## Sample batch

`artifacts/batch_demo/qcare_batch_demo.csv` contains 12 synthetic/demo records, including valid records, a missing creatinine, and an unsupported appetite value. It contains no real patient data.

## Result columns

Results include the original 1-based `row_number`, validation status and errors, normalized eight-feature values, three predictions, model-specific experimental decision scores, and model agreement. Decision scores are not disease probabilities and must not be compared by raw magnitude across model families.

## Results and filters

The batch screen reports total, valid, invalid, agreement, and per-model output counts. It provides validation, agreement, RBF-SVM, QSVC, and VQC filters. Filtering only changes displayed rows and never reruns inference.

## Export

`DOWNLOAD BATCH RESULTS CSV` exports the documented result columns to `qcare_batch_results_<experiment_id>.csv`.

## Models and runtime safety

Valid rows use the existing frozen runtime-safe paths: the persisted RBF-SVM, analytical `ZFeatureMap(reps=1)` QSVC fidelity evaluation, and NumPy statevector VQC inference. No native Qiskit execution or model fitting occurs in Streamlit.

## Limitations

This is a research batch utility, not a clinical diagnostic or prevalence tool. Uploaded rows are not necessarily comparable to the UCI development cohort. The binary frozen model does not predict CKD stages 1–5, and this phase does not add a staging module.

## Tests

Dedicated tests cover canonical and alias mapping, serum-albumin safety, missing and duplicate mappings, numeric/category/row validation, invalid-row isolation, all three frozen model paths, consensus, summary counts, filtering, export, the demo fixture, the row limit, and no-training/no-native-Qiskit runtime constraints. Existing single-patient and OCR tests remain part of the regression suite.
