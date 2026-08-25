from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.results_repository import ResultsRepository


ROOT = Path(__file__).resolve().parents[1]
CORE_WORDING = (
    "External transport failure reflected both target/cohort differences and changed "
    "feature–target relationships; therefore the experiment demonstrates transportability "
    "risk but cannot isolate pure conditional shift."
)


@pytest.fixture(scope="module")
def repository() -> ResultsRepository:
    return ResultsRepository(ROOT)


def test_external_auc_intervals_are_frozen(repository: ResultsRepository) -> None:
    values = repository.headline_values()
    assert values["external_classical_roc_auc"] == pytest.approx(0.5105651851213981)
    assert values["external_classical_ci95_low"] == pytest.approx(0.4750038955660258)
    assert values["external_classical_ci95_high"] == pytest.approx(0.5455950374589428)
    assert values["external_roc_auc"] == pytest.approx(0.5253806378066733)
    assert values["external_qsvc_ci95_low"] == pytest.approx(0.48911291810700097)
    assert values["external_qsvc_ci95_high"] == pytest.approx(0.5605685681129469)


def test_paired_external_difference_is_frozen(repository: ResultsRepository) -> None:
    values = repository.headline_values()
    assert values["external_paired_auc_delta"] == pytest.approx(0.014815452685275177)
    assert values["external_paired_delta_ci95_low"] == pytest.approx(-0.029205263524790095)
    assert values["external_paired_delta_ci95_high"] == pytest.approx(0.058134967010706584)


def test_feature_transportability_values_are_signed(repository: ResultsRepository) -> None:
    values = repository.feature_transportability_table().set_index(["Dataset", "feature"])
    expected_uci = {
        "hemo": 0.0312329793, "al": 0.8708133971, "dm": 0.774,
        "sg": 0.0786637931, "pcv": 0.0475522120, "appet": 0.664,
        "htn": 0.794, "sc": 0.9226745871,
    }
    expected_bd = {
        "hemo": 0.4944190891, "al": 0.4981239774, "dm": 0.5022655792,
        "sg": 0.5170871828, "pcv": 0.4708386129, "appet": 0.5152993230,
        "htn": 0.5053041207, "sc": 0.5182353496,
    }
    for feature, expected in expected_uci.items():
        assert values.loc[("UCI", feature), "Signed AUC"] == pytest.approx(expected)
    for feature, expected in expected_bd.items():
        assert values.loc[("BD-KDD", feature), "Signed AUC"] == pytest.approx(expected)
    assert all(values.loc[("UCI", feature), "Signed AUC"] < 0.5 for feature in ("hemo", "sg", "pcv"))


def test_creatinine_medians_are_frozen(repository: ResultsRepository) -> None:
    medians = repository.creatinine_median_table().set_index("Label")
    assert medians.loc["CKD", "UCI median (mg/dL)"] == pytest.approx(2.25)
    assert medians.loc["non-CKD", "UCI median (mg/dL)"] == pytest.approx(0.90)
    assert medians.loc["CKD", "BD-KDD median (mg/dL)"] == pytest.approx(7.71)
    assert medians.loc["non-CKD", "BD-KDD median (mg/dL)"] == pytest.approx(7.10)


def test_claim_registry_freezes_transport_interpretation(repository: ResultsRepository) -> None:
    assert repository.validate_claim_registry() == []
    registry = json.loads((ROOT / "artifacts/claim_registry.json").read_text())
    claims = {claim["claim_id"]: claim for claim in registry["claims"]}
    external = claims["CLAIM_EXTERNAL_TRANSPORT"]
    assert external["allowed"] is True
    assert "Target comparability with UCI CKD was only partial" in external["text"]
    assert "no external classical-vs-quantum superiority interpretation" in external["scope"]
    assert claims["CLAIM_EXTERNAL_QSVC_SUPERIORITY"]["allowed"] is False


def test_final_facing_sources_use_controlled_external_wording() -> None:
    sources = [
        ROOT / "app.py",
        ROOT / "src/results_repository.py",
        ROOT / "README.md",
        ROOT / "submission/five_minute_pitch.md",
        ROOT / "submission/judge_questions.md",
        ROOT / "submission/novelty_statement.md",
    ]
    combined = "\n".join(path.read_text() for path in sources)
    assert CORE_WORDING in combined
    forbidden = [
        "QSVC collapsed externally",
        "quantum failed under external shift",
        "quantum-specific external failure",
        "pure conditional shift caused failure",
        "successful external validation",
        "clinically validated external cohort",
    ]
    assert all(phrase.lower() not in combined.lower() for phrase in forbidden)


def test_dashboard_contains_required_transportability_explanations() -> None:
    source = (ROOT / "app.py").read_text()
    assert "Target comparability" in source and "PARTIAL" in source
    assert "All eight internally predictive UCI features flattened toward chance-level discrimination in BD-KDD." in source
    assert "Values far below 0.5 can still represent strong discrimination in the opposite direction" in source
    assert "Serum creatinine strongly separated CKD/non-CKD labels in UCI" in source
    assert "Neither model retained meaningful label discrimination under the BD-KDD cross-cohort stress test." in source


def test_screenshot_validation_records_phase3d_metrics() -> None:
    validation = (ROOT / "submission/screenshot_validation.md").read_text()
    for value in ("0.511", "0.475-0.546", "0.525", "0.489-0.561", "PARTIAL", "2.25", "0.90", "7.71", "7.10"):
        assert value in validation
