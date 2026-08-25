# Reproducibility Check

Checked on **25 August 2026** after the Phase 3D interpretation freeze and artifact update.

## Method

The validation used the project’s isolated Python 3.11 environment, a fresh headless Streamlit process, local headless Chrome at fixed desktop/mobile-width viewports, and local frozen artifacts only. No model was retrained, no metric was recomputed, and no network dataset or IBM Quantum request was required.

## Results

| Check | Method | Result |
|---|---|---|
| Dependency specification | `pip install --dry-run --no-index -r requirements.txt` | PASS — every declared requirement was already satisfied by the isolated environment. |
| Environment consistency | `pip check` | PASS — no broken requirements. |
| Full tests | `.venv/bin/python -m pytest -q` | PASS — **71 passed** in the final Phase 3D rerun. |
| Artifact repository | Instantiate `ResultsRepository` from staged root | PASS — headline values loaded and the CKD reference table contained four rows. |
| Claim registry | `validate_claim_registry()` | PASS — zero errors. |
| Application launch | Fresh headless Streamlit process on port 8520 | PASS — server started without traceback at `http://localhost:8520`. |
| Phase 3D page rendering | Headless-browser navigation through affected pages | PASS — Overview, Robustness & Shift, and Quantum Evidence rendered without application or browser-page errors. |
| Demo artifact loading | Inspect paired overview, feature transport, creatinine, and evidence matrix | PASS — both external AUCs/CIs, paired difference, PARTIAL target comparability, signed feature AUCs, label medians, and the shared verdict loaded from local artifacts. |
| Screenshot regeneration | `scripts/capture_phase3d_screenshots.mjs` at fixed viewports | PASS — 13 desktop, 2 mobile-width, and 1 tablet screenshot retained/generated. |
| Screenshot metric audit | Compare every displayed metric with its source artifact | PASS — zero stale scientific values; see `screenshot_validation.md`. |
| Accessibility QA | Contrast, hierarchy, focus, targets, captions, responsive layout | PASS WITH NOTE — app-owned targets meet 44 pixels; compact Streamlit chrome is documented in `accessibility_check.md`. |
| Claim-registry integrity | SHA-256 plus repository validation | PASS — zero validation errors; SHA-256 `fe3c78e294406358dddda332522bce35cb0483321c4d129069765c5225a90528`. |
| Frozen model/data integrity | SHA-256 comparison with pre-Phase 3D values | PASS — primary RBF SVM, QSVC, external metrics/predictions, BD-KDD, and UCI full-source data are unchanged. |
| Layman handbook | Generate, render all eight pages, inspect, and extract text | PASS — clean eight-page PDF with required external interpretation and limitations. |
| Hard-coded metric audit | Source scan after remediation | PASS — the remaining CKD classical AUC literal was replaced with the frozen reference lookup. |
| Offline behaviour | Launch and page navigation without any IBM Quantum or dataset request | PASS — the demo used local artifacts only. |
| Absolute-path portability | Source scan after remediation | PASS — the only repository-local `/Users/...` path was replaced by `data/raw/chronic_kidney_disease.arff`. |
| Reference resolution | UCI CKD, UCI Heart, OpenML 37, and BD-KDD DOI/provenance checked | PASS WITH NOTE — UCI pages resolved directly; OpenML resolved to its JavaScript application; BD-KDD DOI was cross-confirmed through the dataset’s Data in Brief/PubMed record and Harvard Dataverse persistent ID. |

## Clean-environment qualification

No new dependency download was attempted because network-independent verification was required and the dependencies were already installed. The dry run and `pip check` establish that `requirements.txt` is internally satisfiable in the current Python 3.11 environment; they are not a guarantee against a future upstream package release within the declared version ranges.

## Startup commands

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
streamlit run app.py
```

Expected URL: `http://localhost:8501` when the default port is free.

## Outcome

The repository is reproducible for judging and deterministic offline demonstration. The temporary Phase 3D validation instance used `http://localhost:8520`; the default command still uses `http://localhost:8501` when that port is free. Full Phase 1–3 experiment reruns remain separate, computational research workflows; the live demo does not depend on them.
