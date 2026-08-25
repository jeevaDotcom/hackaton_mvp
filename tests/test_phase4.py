from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from src.phase1.data import sha256
from src.results_repository import DATASETS, ResultsRepository


ROOT = Path(__file__).resolve().parents[1]


def repo() -> ResultsRepository:
    return ResultsRepository(ROOT)


def test_no_patient_screening_or_illustrative_metrics_in_app() -> None:
    source = (ROOT / "app.py").read_text().lower()
    forbidden = [
        "patient assessment", "risk percentage", "83% risk", "75% fewer tests",
        "illustrative targets", "clinical recommendation", "risk cascade",
        "patientinputs", "riskresult", "assess_risk",
    ]
    assert all(phrase not in source for phrase in forbidden)
    assert "number_input(" not in source
    assert "select_slider(" not in source


def test_prohibited_claim_strings_are_absent_or_explicitly_negated() -> None:
    sources = "\n".join((ROOT / path).read_text().lower() for path in ["app.py", "src/results_repository.py"])
    strictly_forbidden = [
        "diagnosis result", "clinical recommendation", "cost saving", "quantum superiority",
        "83% risk", "75% fewer tests", "hardware-ready", "quantum powered diagnosis",
    ]
    assert all(phrase not in sources for phrase in strictly_forbidden)
    for line in sources.splitlines():
        if "quantum advantage" in line:
            assert "no observed advantage" in line or "no quantum" in line or "not supported" in line


def test_no_patient_risk_percentages() -> None:
    source = (ROOT / "app.py").read_text()
    suspicious = re.findall(r"(?:risk|probability)[^\n]{0,40}\d+%", source, flags=re.IGNORECASE)
    assert suspicious == []


def test_artifact_values_match_ui_repository() -> None:
    value = repo()
    raw = pd.read_csv(ROOT / "artifacts/phase3/reference_cv_summary.csv")
    row = raw[(raw.budget == 8) & (raw.model == "qsvc")].iloc[0]
    assert value.headline_values()["qsvc_sensitivity"] == row.sensitivity_mean == 0.985
    external = pd.read_csv(ROOT / "artifacts/phase3/external_ckd_metrics.csv")
    qsvc = external[external.model == "qsvc"].iloc[0]
    assert value.headline_values()["external_roc_auc"] == qsvc.roc_auc


def test_claim_registry_consistency() -> None:
    value = repo()
    assert value.validate_claim_registry() == []
    registry = json.loads((ROOT / "artifacts/claim_registry.json").read_text())
    ids = [claim["claim_id"] for claim in registry["claims"]]
    assert len(ids) == len(set(ids))
    assert any(not claim["allowed"] for claim in registry["claims"])


def test_final_model_manifest_loads_and_hashes_match() -> None:
    value = repo()
    assert value.manifest["primary_freeze"]["input_budget"] == 8
    for model in value.manifest["models"]:
        path = ROOT / model["path"]
        assert path.exists()
        assert sha256(path) == model["sha256"]


def test_external_validation_metrics_are_frozen() -> None:
    external = repo().external.set_index("model")
    assert external.loc["qsvc", "sensitivity"] > 0.99
    assert external.loc["qsvc", "specificity"] < 0.02
    assert 0.50 < external.loc["qsvc", "roc_auc"] < 0.55


def test_dataset_provenance_is_precise() -> None:
    assert "Karaikudi" in DATASETS["ckd"]["population"]
    assert "Dhaka" in DATASETS["external"]["population"]
    assert "Phoenix" in DATASETS["diabetes"]["population"]
    assert "not an Indian" in repo().evidence_report_markdown()


def test_circuit_metadata_and_rendered_artifact() -> None:
    value = repo()
    qsvc = next(item for item in value.manifest["models"] if item["model"] == "qsvc" and item["budget"] == 8)
    resources = qsvc["quantum_resources"]
    assert resources["feature_map"] == "ZFeatureMap"
    assert resources["entanglement"] == "none"
    assert resources["qubit_count"] == 8 and resources["circuit_depth"] == 2
    circuit = value.circuit_text()
    assert "x[0]" in circuit and "x[7]" in circuit
    assert "■" not in circuit


def test_evidence_labels_are_controlled() -> None:
    matrix = repo().evidence_matrix()
    allowed = {"SUPPORTED", "NEUTRAL", "NOT SUPPORTED", "INCONCLUSIVE", "TRANSPORTABILITY FAILURE"}
    assert set(matrix["Evidence verdict"]).issubset(allowed)
    assert len(matrix) == 10


def test_experiment_replay_outputs_are_frozen_lookups() -> None:
    value = repo()
    for representation in ("clinical", "pca"):
        for budget in (8, 6):
            for model in ("RBF SVM", "QSVC"):
                result = value.replay(representation, budget, model)
                assert result.source_artifact == "artifacts/quantum_cv_summary.csv"
                assert 0 <= result.sensitivity <= 1
                assert 0 <= result.roc_auc <= 1
                assert result.qubits == (budget if model == "QSVC" else 0)


def test_evidence_summary_is_downloadable_markdown_content() -> None:
    report = repo().evidence_report_markdown()
    assert report.startswith("# Q-CARE Evidence Summary")
    assert "## External transportability" in report
    assert "Research prototype only" in report
