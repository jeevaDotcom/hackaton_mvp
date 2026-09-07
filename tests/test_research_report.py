from __future__ import annotations

from datetime import datetime
from pathlib import Path

import fitz
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.csv_batch import FEATURE_ORDER, build_batch_results
from src.live_vqc import LiveVQCService
from src.results_repository import ResultsRepository
from src.research_report import (
    ReportStateError,
    create_batch_report,
    create_single_patient_report,
    generate_experiment_id,
)


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def service() -> LiveVQCService:
    return LiveVQCService(ROOT)


@pytest.fixture(scope="module")
def repo() -> ResultsRepository:
    return ResultsRepository(ROOT)


def extracted(data: bytes) -> str:
    return "\n".join(page.get_text() for page in fitz.open(stream=data, filetype="pdf"))


def single_report(repo: ResultsRepository, service: LiveVQCService, **kwargs: object) -> tuple[bytes, str]:
    result = service.analyse(service.presets["mixed"]["profile"])
    data = create_single_patient_report(
        repo,
        service,
        result,
        experiment_id="QCARE-20260908-021530-A4F2",
        generated_at=datetime(2026, 9, 8, 2, 15, 30),
        **kwargs,
    )
    return data, extracted(data)


def test_experiment_id_format_and_injection() -> None:
    assert generate_experiment_id(datetime(2026, 9, 8, 2, 15, 30), suffix="A4F2") == "QCARE-20260908-021530-A4F2"


def test_single_pdf_bytes_and_identity(repo: ResultsRepository, service: LiveVQCService) -> None:
    data, text = single_report(repo, service)
    assert data.startswith(b"%PDF")
    assert "QCARE-20260908-021530-A4F2" in text
    assert "2026-09-08T02:15:30" in text
    assert "Input mode" in text
    assert "Manual" in text


def test_single_pdf_profile_predictions_and_agreement(repo: ResultsRepository, service: LiveVQCService) -> None:
    _, text = single_report(repo, service)
    for feature in ("Haemoglobin", "Albumin", "Diabetes mellitus", "Specific gravity", "Packed cell volume", "Appetite", "Hypertension", "Serum creatinine"):
        assert feature in text
    for model in ("RBF SVM", "QSVC", "VQC"):
        assert model in text
    assert "CKD-like" in text
    assert "non-CKD-like" in text
    assert "2 OF 3 AGREE" in text
    assert "Experimental decision score" in text
    assert "NOT a calibrated disease probability" in text


def test_single_pdf_evidence_sections(repo: ResultsRepository, service: LiveVQCService) -> None:
    _, text = single_report(repo, service)
    normalized = " ".join(text.split()).replace("- ", "-")
    for section in (
        "MODEL PERFORMANCE COMPARISON", "COMPUTATIONAL COST", "FACTORS INFLUENCING THIS MODEL OUTPUT",
        "FEATURE-BUDGET EVIDENCE", "QUANTUM MODEL EVIDENCE", "ROBUSTNESS & STRESS TESTS",
        "EXTERNAL TRANSPORTABILITY", "CKD STAGE RESEARCH STATUS", "AUTOMATED EVIDENCE SUMMARY",
        "LIMITATIONS", "RESPONSIBLE USE",
    ):
        assert section in text
    for metric in ("Sensitivity", "Specificity", "F1", "ROC-AUC"):
        assert metric in text
    assert "approximately 464x slower" in text
    assert "MODEL INFLUENCE — NOT BIOLOGICAL CAUSATION" in text
    assert "24 original CKD predictors" in text
    assert "ZFeatureMap" in text
    assert "RealAmplitudes" in text
    assert "34.57 seconds" in text
    assert "Neither model demonstrated reliable better-than-random discrimination" in normalized
    assert "NOT VALIDATED" in text
    assert "This report summarizes a Q-CARE research experiment." in text


def test_scan_pdf_confirms_researcher_and_corrections(repo: ResultsRepository, service: LiveVQCService) -> None:
    _, text = single_report(
        repo,
        service,
        mode="Report Scan",
        source_name="sample_digital_report.pdf",
        researcher_confirmed=True,
        corrected_values=True,
    )
    assert "Report Scan" in text
    assert "AI-assisted / OCR-assisted report extraction" in text
    assert "Researcher verification: CONFIRMED" in text
    assert "Researcher-modified values were used" in text


def test_batch_pdf_is_summary_only(repo: ResultsRepository, service: LiveVQCService) -> None:
    frame = service.reference_records[FEATURE_ORDER].head(6).copy()
    results = build_batch_results(frame, {feature: feature for feature in FEATURE_ORDER}, service)
    data = create_batch_report(
        repo,
        service,
        results,
        source_name="qcare_batch_demo.csv",
        mapping={feature: feature for feature in FEATURE_ORDER},
        experiment_id="QCARE-20260908-021530-B4F2",
        generated_at=datetime(2026, 9, 8, 2, 15, 30),
    )
    text = extracted(data)
    normalized = " ".join(text.split()).replace("- ", "-")
    assert data.startswith(b"%PDF")
    assert "QCARE-20260908-021530-B4F2" in text
    for label in ("Total rows", "Valid rows", "Invalid rows", "3/3 agreement", "2/3 agreement", "Disagreement"):
        assert label in text
    assert "qcare_batch_demo.csv" in text
    assert "Detailed row-level results are available in the downloadable Q-CARE batch-results CSV." in normalized
    assert "row_number" not in text
    assert "Stage 1" in text


def test_batch_pdf_has_no_row_level_stage_or_probability_output(repo: ResultsRepository, service: LiveVQCService) -> None:
    frame = service.reference_records[FEATURE_ORDER].head(2).copy()
    results = build_batch_results(frame, {feature: feature for feature in FEATURE_ORDER}, service)
    text = extracted(create_batch_report(repo, service, results))
    assert "stage_prediction" not in text.lower()
    assert "Predicted Stage" not in text
    assert "65% CKD risk" not in text


def test_report_requires_completed_experiment(repo: ResultsRepository, service: LiveVQCService) -> None:
    with pytest.raises(ReportStateError):
        create_single_patient_report(repo, service, None)
    with pytest.raises(ReportStateError):
        create_batch_report(repo, service, pd.DataFrame())


def test_report_ui_gates_download_until_experiment() -> None:
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
    assert len(app.exception) == 0
    generate = next(button for button in app.button if button.label == "GENERATE RESEARCH PDF")
    assert generate.disabled is True
    assert not any(button.label == "DOWNLOAD RESEARCH PDF" for button in app.download_button)


def test_report_has_no_unsafe_current_output_claims(repo: ResultsRepository, service: LiveVQCService) -> None:
    _, text = single_report(repo, service)
    assert "Predicted Stage" not in text
    assert "Likely Stage" not in text
    assert "You are Stage" not in text
    assert "quantum advantage demonstrated" not in text.lower()
    assert "not a calibrated disease probability" in text.lower()
