from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.csv_batch import FEATURE_ORDER, build_batch_results, result_columns
from src.live_vqc import LiveVQCService


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def service() -> LiveVQCService:
    return LiveVQCService(ROOT)


def test_stage_research_view_renders_with_scope_status() -> None:
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
    assert len(app.exception) == 0
    rendered = "\n".join(item.value for item in app.markdown)
    assert "CKD STAGE RESEARCH VIEW" in rendered
    assert "NOT VALIDATED IN CURRENT Q-CARE MODEL" in rendered
    assert "CKD-like versus non-CKD-like" in rendered
    assert "Stage 1–5 prediction" in rendered


def test_single_patient_outputs_do_not_contain_a_stage_prediction() -> None:
    for preset_fragment in ("CKD-like", "non-CKD-like"):
        app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
        preset = next(button for button in app.button if preset_fragment in button.label)
        preset.click().run(timeout=30)
        next(button for button in app.button if button.label == "ANALYSE PROFILE").click().run(timeout=30)
        consensus = next(item.value for item in app.markdown if item.value.startswith('<div class="consensus-table">'))
        assert "Stage 1" not in consensus
        assert "Stage 2" not in consensus
        assert "Stage 3" not in consensus
        assert "Stage 4" not in consensus
        assert "Stage 5" not in consensus


def test_batch_result_schema_has_no_stage_prediction_column(service: LiveVQCService) -> None:
    frame = service.reference_records[FEATURE_ORDER].head(2).copy()
    results = build_batch_results(frame, {feature: feature for feature in FEATURE_ORDER}, service)
    assert not any("stage" in column.lower() for column in results.columns)
    assert not any("stage" in column.lower() for column in result_columns())


def test_ocr_source_has_no_staging_logic_or_output() -> None:
    source = (ROOT / "src/report_scanner.py").read_text().lower()
    assert "stage" not in source
    assert "egfr" not in source
    assert "stage_prediction" not in source


def test_stage_scope_has_no_score_creatinine_or_egfr_rule() -> None:
    source = (ROOT / "src/workstation_page.py").read_text()
    stage_view = source[source.index("def _stage_research_view"):source.index("def _factor_panel")]
    assert "eGFR" not in stage_view
    assert "creatinine" not in stage_view.lower()
    assert "classification_threshold" not in stage_view
    assert "score_to_stage" not in stage_view
    assert "stage_prediction" not in stage_view


def test_ui_does_not_expose_unsafe_stage_output_phrases() -> None:
    source = (ROOT / "src/workstation_page.py").read_text()
    for phrase in ("Predicted Stage", "Likely Stage", "You are Stage", "CKD Stage prediction"):
        assert phrase not in source
    assert "Stage cannot be inferred from this binary Q-CARE classification." in source


def test_frozen_model_outputs_remain_unchanged(service: LiveVQCService) -> None:
    profile = service.presets["mixed"]["profile"]
    comparison = service.model_comparison(profile)
    assert {item.model: item.predicted_class for item in comparison["decisions"]} == {
        "VQC": 1,
        "QSVC": 0,
        "RBF SVM": 0,
    }
    assert service.vqc_score(profile) == pytest.approx(0.5094535749605267)
    assert service.metrics["vqc"]["roc_auc"] == pytest.approx(0.676)


def test_stage_module_documentation_marks_scope_control_complete() -> None:
    document = (ROOT / "research/stage_module_decision.md").read_text()
    assert "Disease Stage: COMPLETE — RESPONSIBLE SCOPE CONTROL" in document
    assert "No stage values are produced" in document
    assert "does not implement KDIGO rules" in document
