# Q-CARE research PDF results

## PDF engine

Reports use the local Matplotlib A4 PDF backend already present in the project environment. PyMuPDF is used in tests and QA to open and extract generated text. No external service, LLM, or model execution is used during report generation.

## Report types

- Single Patient: completed manual frozen-model experiment.
- Report Scan: completed researcher-confirmed OCR profile and frozen-model experiment.
- CSV Batch: completed batch summary with row counts, output distributions, agreement counts, mapping summary, and a pointer to the downloadable row-level CSV.

## Experiment IDs

IDs use `QCARE-YYYYMMDD-HHMMSS-XXXX`, combining local generation time and a short UUID suffix. Tests can inject a fixed ID and timestamp.

## Sections and evidence

Reports include experiment information, confirmed eight-feature profile where applicable, model outputs and agreement, frozen performance metrics, computational cost, profile-specific feature influence when available, 24-to-8 feature evidence, quantum architecture, VQC transparency, robustness/stress-test scope, Phase 3C external transportability, CKD stage limitation, deterministic automated evidence summary, limitations, and the responsible-use statement.

All values come from the existing `ResultsRepository`, frozen live service artifacts, or completed experiment state. No training or inference runs are triggered by PDF generation.

## Charts

Single/scan reports include the frozen model performance comparison and profile-specific VQC influence chart. Batch reports include the frozen performance comparison and summary-only batch sections. Runtime and 24-to-8 evidence are presented from current artifacts; no illustrative values are added.

## Batch behavior

Batch PDFs deliberately do not embed hundreds or thousands of rows. They include total/valid/invalid counts, mapping and validation notes, model output counts, agreement counts, and the sentence: “Detailed row-level results are available in the downloadable Q-CARE batch-results CSV.”

## Responsible-use wording

Every report identifies Q-CARE as a research prototype and not a clinical diagnostic report. It states that model scores are not calibrated disease probabilities, that CKD stage cannot be inferred from the binary classifier, and that the report is not a diagnosis, treatment recommendation, triage decision, validated probability, or clinically validated staging result.

## Tests and visual QA

`tests/test_research_report.py` covers PDF signatures, injected IDs/timestamps, feature and prediction content, agreement, metrics, runtime, influence, 24-to-8 evidence, quantum evidence, robustness, transportability, stage limitations, automated summary, limitations, responsible use, batch summary-only behavior, and pre-result UI gating. Manual and batch Streamlit AppTest flows verify generation/download controls.

Demo PDFs are generated from synthetic/demo profiles and the existing fictional sample batch. They are opened with PyMuPDF and rendered to PNG for page-count, clipping, blank-page, readability, page-number, disclaimer, and experiment-ID checks.

## Known limitations

Matplotlib PDF text extraction can insert line-break hyphenation into long sentences; visual rendering remains the source of truth. The report is a research evidence summary and does not add clinical staging, calibration, or deployment validation.
