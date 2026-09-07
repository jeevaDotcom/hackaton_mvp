from __future__ import annotations

import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.data_health import analyse_data_health
from src.live_vqc import LiveVQCService
from src.results_repository import ResultsRepository


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def service() -> LiveVQCService:
    return LiveVQCService(ROOT)


@pytest.fixture(scope="module")
def repo() -> ResultsRepository:
    return ResultsRepository(ROOT)


def test_single_page_renders_without_navigation_or_exception() -> None:
    source = (ROOT / "app.py").read_text()
    assert "workstation_page(ROOT, repo)" in source
    assert 'st.radio(\n        "Workspace"' not in source
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
    assert len(app.exception) == 0
    assert [item.label for item in app.expander] == [
        "Data health check",
        "Feature engineering",
        "Classical / quantum benchmark",
        "Actual quantum circuits",
        "Robustness",
        "Dataset compatibility & transportability",
        "Q-CARE model evidence report",
    ]


def test_patient_entry_executes_frozen_three_model_assessment() -> None:
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
    analyse = [button for button in app.button if button.label == "ANALYSE PROFILE"]
    assert len(analyse) == 1
    analyse[0].click().run(timeout=30)
    assert len(app.exception) == 0
    assert any("2 OF 3 AGREE" in item.value for item in app.markdown)
    assert any("0.509" in item.value for item in app.markdown)


def test_judge_hero_grouped_inputs_and_model_mode_render() -> None:
    source = (ROOT / "src/workstation_page.py").read_text()
    required = [
        "Hybrid Quantum-Classical Healthcare Research Platform",
        "Compare classical and quantum models on the same biomedical inputs",
        "Blood markers",
        "Urine markers",
        "Clinical factors",
        '"Compare All", "Single Model"',
        '"INPUT", "Profile, report or CSV"',
        '"TRUST", "Evidence boundary"',
    ]
    assert all(copy in source for copy in required)
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
    assert len(app.exception) == 0
    modes = [control for control in app.segmented_control if control.label == "MODEL MODE"]
    assert len(modes) == 1
    assert modes[0].value == "Compare All"


def test_single_model_mode_runs_selected_frozen_model() -> None:
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
    mode = [control for control in app.segmented_control if control.label == "MODEL MODE"][0]
    mode.set_value("Single Model").run(timeout=30)
    selected = [control for control in app.selectbox if control.label == "Frozen model"][0]
    selected.set_value("QSVC").run(timeout=30)
    [button for button in app.button if button.label == "ANALYSE PROFILE"][0].click().run(timeout=30)
    assert len(app.exception) == 0
    consensus = [item.value for item in app.markdown if item.value.startswith('<div class="consensus-table">')]
    assert len(consensus) == 1
    assert "QSVC" in consensus[0]
    assert "RBF SVM" not in consensus[0]
    assert ">VQC<" not in consensus[0]
    assert any("SINGLE MODEL" in item.value for item in app.markdown)


def test_vqc_score_status_and_no_performance_inflation(service: LiveVQCService) -> None:
    score = service.vqc_score(service.presets["mixed"]["profile"])
    metrics = service.metrics
    assert score == pytest.approx(0.5094535749605267)
    assert metrics["performance_decision"] == "WEAK — DISPLAY WITH CAUTION"
    assert metrics["vqc"]["sensitivity"] == pytest.approx(0.64)
    assert metrics["vqc"]["specificity"] == pytest.approx(0.5666666666666667)
    assert metrics["vqc"]["f1"] == pytest.approx(0.6736842105263158)
    assert metrics["vqc"]["roc_auc"] == pytest.approx(0.676)
    assert metrics["vqc"]["roc_auc"] < metrics["rbf_svm_existing_comparator"]["roc_auc"]
    assert metrics["vqc"]["roc_auc"] < metrics["qsvc_existing_comparator"]["roc_auc"]


def test_qsvc_svm_vqc_agreement_is_same_profile(service: LiveVQCService) -> None:
    result = service.model_comparison(service.presets["mixed"]["profile"])
    assert result["agreement"] == "2 OF 3 AGREE"
    assert {item.model: item.predicted_class for item in result["decisions"]} == {"VQC": 1, "QSVC": 0, "RBF SVM": 0}


def test_uploaded_csv_data_health_ready_path(service: LiveVQCService) -> None:
    frame = service.reference_records.dropna().copy()
    classes = frame.groupby("target", group_keys=False).head(8)
    result = analyse_data_health(classes, "target", service.observed_ranges)
    assert result.status == "READY"
    assert result.required_coverage == 8
    assert result.target_classes == 2
    assert result.can_evaluate_frozen_ckd_models is True


def test_incompatible_uploaded_dataset_blocks_evaluation(service: LiveVQCService) -> None:
    frame = service.reference_records.drop(columns=["sc"]).dropna().head(20)
    result = analyse_data_health(frame, "target", service.observed_ranges)
    assert result.status == "INCOMPATIBLE"
    assert "sc" in result.missing_required
    assert result.can_evaluate_frozen_ckd_models is False


def test_external_confidence_intervals_remain_frozen(repo: ResultsRepository) -> None:
    values = repo.headline_values()
    assert values["external_classical_roc_auc"] == pytest.approx(0.5105651851213981)
    assert values["external_classical_ci95_low"] == pytest.approx(0.4750038955660258)
    assert values["external_classical_ci95_high"] == pytest.approx(0.5455950374589428)
    assert values["external_roc_auc"] == pytest.approx(0.5253806378066733)
    assert values["external_qsvc_ci95_low"] == pytest.approx(0.48911291810700097)
    assert values["external_qsvc_ci95_high"] == pytest.approx(0.5605685681129469)


def test_feature_transportability_values_are_artifact_backed(repo: ResultsRepository) -> None:
    frame = repo.feature_transportability_table()
    assert set(frame["feature"]) == set(repo.primary_features)
    bd = frame[frame.Dataset == "BD-KDD"]
    assert len(bd) == 8
    assert bd["Signed AUC"].between(0.470, 0.519).all()


def test_feature_efficiency_chart_values_are_frozen_and_matched(repo: ResultsRepository) -> None:
    frame = repo.feature_efficiency_table()
    assert set(frame["Representation"]) == {"24 features", "8 features"}
    assert set(frame["Metric"]) == {"Sensitivity", "Specificity", "F1", "ROC-AUC"}
    pivot = frame.pivot(index="Metric", columns="Representation", values="Value")
    assert pivot.loc["Sensitivity", "24 features"] == pytest.approx(0.985)
    assert pivot.loc["Sensitivity", "8 features"] == pytest.approx(0.995)
    assert pivot.loc["Specificity", "24 features"] == pytest.approx(1.0)
    assert pivot.loc["Specificity", "8 features"] == pytest.approx(0.9958333333333333)
    assert pivot.loc["F1", "24 features"] == pytest.approx(0.9923401493021746)
    assert pivot.loc["F1", "8 features"] == pytest.approx(0.996201329534663)
    assert pivot.loc["ROC-AUC", "24 features"] == pytest.approx(1.0)
    assert pivot.loc["ROC-AUC", "8 features"] == pytest.approx(1.0)


def test_judge_visuals_use_only_existing_evidence_artifacts(repo: ResultsRepository, service: LiveVQCService) -> None:
    source = (ROOT / "src/workstation_page.py").read_text()
    assert "artifacts/quantum/kernels/clinical_8_z_reps1.npz" in source
    assert (ROOT / "artifacts/quantum/kernels/clinical_8_z_reps1.npz").exists()
    assert (ROOT / "artifacts/live_vqc/training_trace.csv").exists()
    assert repo.runtime_ratio(8) == pytest.approx(464.11648514474587)
    assert service.metrics["training_runtime_seconds"] == pytest.approx(34.57021299999906)
    assert service.metadata["optimizer_evaluations"] == 40
    assert "VQC holdout metrics and repeated-CV estimates are not interchangeable" in source
    assert "No quantum speed advantage" in source


def test_claim_registry_consistency_is_preserved(repo: ResultsRepository) -> None:
    assert repo.validate_claim_registry() == []


def test_single_page_copy_has_no_diagnostic_or_directive_language() -> None:
    source = (ROOT / "src/workstation_page.py").read_text().lower()
    forbidden = [
        "patient has ckd", "you have ckd", "confirmed diagnosis", "diagnosis result",
        "prescribe medication", "admit patient", "refer to nephrology", "treatment recommendation",
    ]
    assert all(phrase not in source for phrase in forbidden)
    assert "must not be interpreted as diagnosis" in source
    assert "not a clinical diagnostic system" in source


def test_single_page_has_no_fake_risk_percentage() -> None:
    source = (ROOT / "src/workstation_page.py").read_text()
    assert re.findall(r"(?:risk|probability)[^\n]{0,40}\d+%", source, flags=re.IGNORECASE) == []
    assert "not a calibrated disease probability" in source.lower()


def test_page_interactions_cannot_retrain_models() -> None:
    source = "\n".join((ROOT / path).read_text() for path in ["app.py", "src/workstation_page.py", "src/data_health.py"])
    assert ".fit(" not in source
    assert "train_live_vqc" not in source
    assert "hyperparameter" not in source.lower()
