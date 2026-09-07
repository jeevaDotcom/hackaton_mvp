from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.live_vqc import LiveVQCService
from src.report_scanner import (
    ProfileConfirmationError,
    ReportValidationError,
    SourceLine,
    confirm_profile,
    extract_report,
    parse_source_lines,
    parse_text_pages,
    profile_health,
    review_defaults,
    review_table,
    validate_upload,
)


ROOT = Path(__file__).resolve().parents[1]
OCR_ARTIFACTS = ROOT / "artifacts/ocr_demo"
COMPLETE_PROFILE = {
    "hemo": 10.4,
    "pcv": 31.0,
    "sc": 2.4,
    "al": 1.0,
    "sg": 1.01,
    "dm": "no",
    "htn": "yes",
    "appet": "good",
}


@pytest.fixture(scope="module")
def service() -> LiveVQCService:
    return LiveVQCService(ROOT)


def test_digital_pdf_prefers_embedded_text_and_preserves_source() -> None:
    path = OCR_ARTIFACTS / "sample_digital_report.pdf"
    result = extract_report(path.read_bytes(), path.name)
    assert result.method == "Embedded PDF text · PyMuPDF"
    assert result.page_count == 1
    assert result.detected_count == 4
    creatinine = result.safe_candidate("sc")
    assert creatinine is not None
    assert creatinine.normalized_value == pytest.approx(2.4)
    assert creatinine.original_unit == "mg/dL"
    assert creatinine.page == 1
    assert "Serum Creatinine" in creatinine.source


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Local OCR engine is optional")
def test_image_ocr_path_extracts_offline_photo_sample() -> None:
    path = OCR_ARTIFACTS / "sample_photo_report.png"
    result = extract_report(path.read_bytes(), path.name)
    assert result.method == "Local Tesseract OCR"
    assert result.detected_count == 8
    assert review_defaults(result) == {
        "hemo": 12.6, "pcv": 38.0, "sc": 1.4, "al": 1.0,
        "sg": 1.02, "dm": "no", "htn": "yes", "appet": "good",
    }


@pytest.mark.parametrize(
    ("line", "feature", "expected"),
    [
        ("HGB: 11.2 g/dL", "hemo", 11.2),
        ("Hematocrit: 34 %", "pcv", 34.0),
        ("S. Creatinine: 1.8 mg/dL", "sc", 1.8),
        ("Sp. Gravity: 1.015", "sg", 1.015),
        ("Known diabetic", "dm", "yes"),
        ("HTN: No", "htn", "no"),
        ("Normal appetite", "appet", "good"),
    ],
)
def test_alias_and_value_parsing(line: str, feature: str, expected: object) -> None:
    result = parse_text_pages([line])
    candidate = result.safe_candidate(feature)
    assert candidate is not None
    assert candidate.normalized_value == expected


def test_known_units_convert_and_missing_units_require_review() -> None:
    result = parse_text_pages(["Hemoglobin: 126 g/L\nCreatinine: 176.8 umol/L\nPCV: 31"])
    assert result.safe_candidate("hemo").normalized_value == pytest.approx(12.6)  # type: ignore[union-attr]
    assert result.safe_candidate("sc").normalized_value == pytest.approx(2.0)  # type: ignore[union-attr]
    assert result.field_status("pcv") == "REVIEW REQUIRED"


def test_serum_and_context_free_albumin_are_never_mapped_silently() -> None:
    serum = parse_text_pages(["Serum Albumin: 3.7 g/dL"])
    generic = parse_text_pages(["Albumin: 2 +"])
    urine = parse_text_pages(["Urine Albumin: 2 +"])
    assert serum.safe_candidate("al") is None
    assert "cannot automatically be assumed equivalent" in serum.candidates["al"][0].reason
    assert generic.safe_candidate("al") is None
    assert urine.safe_candidate("al").normalized_value == pytest.approx(2.0)  # type: ignore[union-attr]


def test_multiple_values_are_conflicts_with_page_provenance() -> None:
    result = parse_text_pages(["Serum Creatinine: 1.2 mg/dL", "Serum Creatinine: 2.4 mg/dL"])
    assert result.field_status("sc") == "MULTIPLE VALUES DETECTED"
    assert result.safe_candidate("sc") is None
    assert [candidate.page for candidate in result.candidates["sc"]] == [1, 2]


def test_missing_values_remain_manual_and_are_not_invented() -> None:
    result = parse_text_pages(["Haemoglobin: 10.4 g/dL"])
    assert result.detected_count == 1
    assert review_defaults(result)["htn"] is None
    assert result.field_status("htn") == "MANUAL"


def test_manual_override_and_confirmation_require_all_fields() -> None:
    profile = confirm_profile({**COMPLETE_PROFILE, "hemo": "11.7"})
    assert profile["hemo"] == pytest.approx(11.7)
    with pytest.raises(ProfileConfirmationError, match="Complete all eight fields"):
        confirm_profile({**COMPLETE_PROFILE, "appet": None})
    with pytest.raises(ProfileConfirmationError, match="dataset-compatible"):
        confirm_profile({**COMPLETE_PROFILE, "appet": "normal"})


def test_profile_data_health_checks_completeness_and_development_range(service: LiveVQCService) -> None:
    ready = profile_health(COMPLETE_PROFILE, service.observed_ranges)
    assert ready["FEATURE COMPLETENESS"] == "8 / 8"
    assert ready["MODEL INPUT STATUS"] == "READY"
    shifted = profile_health({**COMPLETE_PROFILE, "sg": 1.04}, service.observed_ranges)
    assert shifted["DEVELOPMENT-RANGE CHECK"] == "WARNING"
    assert "sg" in shifted["outside_features"]

    extracted = parse_text_pages(["Specific Gravity: 1.040"])
    row = [item for item in review_table(extracted, service.observed_ranges) if item["Q-CARE Feature"] == "Specific gravity"][0]
    assert row["Normalized"] == "1.04 unitless"
    assert row["Development range"] == "Outside Development Range"


def test_unsupported_empty_and_malformed_uploads_fail_friendly() -> None:
    with pytest.raises(ReportValidationError, match="Unsupported report format"):
        validate_upload("report.txt", b"text")
    with pytest.raises(ReportValidationError, match="empty"):
        validate_upload("report.pdf", b"")
    with pytest.raises(ReportValidationError, match="malformed"):
        validate_upload("report.png", b"not-a-png")
    assert "maxUploadSize = 10" in (ROOT / ".streamlit/config.toml").read_text()


def test_ocr_failure_returns_manual_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    path = OCR_ARTIFACTS / "sample_photo_report.png"
    original_which = shutil.which
    monkeypatch.setattr(shutil, "which", lambda name: None if name == "tesseract" else original_which(name))
    result = extract_report(path.read_bytes(), path.name)
    assert result.method == "Manual fallback"
    assert result.detected_count == 0
    assert "Automatic extraction could not confidently read this report" in result.warnings[0]


def test_scanner_module_has_no_model_execution_path() -> None:
    source = (ROOT / "src/report_scanner.py").read_text()
    assert "LiveVQCService" not in source
    assert "qiskit" not in source.lower()
    assert ".predict(" not in source
    assert ".fit(" not in source


def test_streamlit_sample_requires_confirmation_before_model_execution() -> None:
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
    entry = [control for control in app.segmented_control if control.label == "Entry path"][0]
    entry.set_value("Scan Report").run(timeout=30)
    [button for button in app.button if button.label == "TRY SAMPLE REPORT"][0].click().run(timeout=60)
    assert len(app.exception) == 0
    assert "workstation_analysis" not in app.session_state
    assert not [button for button in app.button if button.label == "RUN EXPERIMENT"]

    selections = {
        "Albumin · dataset ordinal grade": 1.0,
        "Diabetes mellitus": "no",
        "Hypertension": "yes",
        "Appetite · dataset category": "good",
    }
    for label, value in selections.items():
        [control for control in app.selectbox if control.label == label][0].set_value(value)
    [button for button in app.button if button.label == "CONFIRM FEATURE PROFILE"][0].click().run(timeout=30)
    assert "workstation_analysis" not in app.session_state
    assert app.session_state["ocr_confirmed_profile"] == COMPLETE_PROFILE
    assert [button for button in app.button if button.label == "RUN EXPERIMENT"]

    [button for button in app.button if button.label == "RUN EXPERIMENT"][0].click().run(timeout=30)
    assert len(app.exception) == 0
    decisions = app.session_state["workstation_analysis"]["comparison"]["decisions"]
    assert {decision.model for decision in decisions} == {"RBF SVM", "QSVC", "VQC"}
    assert any("OF 3 AGREE" in item.value for item in app.markdown)


def test_source_line_confidence_uses_engine_quality_without_percent_display() -> None:
    candidates = parse_source_lines([SourceLine(2, "Serum Creatinine: 2.4 mg/dL", 55.0)], "Local Tesseract OCR")
    assert candidates["sc"][0].confidence == "LOW"
    assert candidates["sc"][0].page == 2
