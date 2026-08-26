from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

from src.live_vqc import LiveVQCService


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FEATURES = ["hemo", "al", "dm", "sg", "pcv", "appet", "htn", "sc"]


@pytest.fixture(scope="module")
def service() -> LiveVQCService:
    return LiveVQCService(ROOT)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_vqc_artifacts_load_and_hashes_match(service: LiveVQCService) -> None:
    metadata = service.metadata
    for key in ("model", "weights", "preprocessor"):
        path = ROOT / metadata[f"{key}_path"]
        assert path.exists()
        assert sha256(path) == metadata[f"{key}_sha256"]
    assert service.weights.shape == (16,)


def test_live_feature_order_is_frozen(service: LiveVQCService) -> None:
    assert service.feature_order == EXPECTED_FEATURES
    assert service.metadata["qubits"] == len(EXPECTED_FEATURES) == 8
    assert service.classical_bundle["features"] == EXPECTED_FEATURES
    assert service.qsvc_bundle["features"] == EXPECTED_FEATURES


def test_preprocessing_is_consistent_with_persisted_artifact(service: LiveVQCService) -> None:
    profile = service.presets["ckd_like"]["profile"]
    expected = np.asarray(
        joblib.load(ROOT / service.metadata["preprocessor_path"]).transform(pd.DataFrame([profile])[EXPECTED_FEATURES]),
        dtype=float,
    )
    assert np.allclose(service.transform_profile(profile), expected)


def test_categorical_encoding_changes_only_expected_binary_dimension(service: LiveVQCService) -> None:
    base = dict(service.presets["non_ckd_like"]["profile"])
    toggled = dict(base)
    toggled["dm"] = "yes" if base["dm"] == "no" else "no"
    difference = service.transform_profile(toggled) - service.transform_profile(base)
    assert np.count_nonzero(np.abs(difference) > 1e-12) == 1
    with pytest.raises(ValueError, match="Unsupported category"):
        service.transform_profile({**base, "dm": "unknown"})


def test_prediction_execution_is_bounded_and_reproducible(service: LiveVQCService) -> None:
    profile = service.presets["mixed"]["profile"]
    first = service.vqc_score(profile)
    second = service.vqc_score(profile)
    assert 0.0 <= first <= 1.0
    assert first == second
    assert service.vqc_decision(profile).display in {
        "Pattern closer to CKD class",
        "Pattern closer to non-CKD class",
    }


def test_live_score_uses_worker_safe_frozen_circuit_execution(service: LiveVQCService) -> None:
    source = (ROOT / "src/live_vqc.py").read_text()
    assert "from_dill" not in source
    assert "qiskit_machine_learning" not in source
    assert service.vqc_score(service.presets["mixed"]["profile"]) == pytest.approx(0.5094535749605267)


def test_similar_record_search_is_anonymised(service: LiveVQCService) -> None:
    matches = service.similar_records(service.presets["ckd_like"]["profile"])
    assert 3 <= len(matches) <= 5
    assert list(matches["Rank"]) == list(range(1, len(matches) + 1))
    assert "Recorded dataset class" in matches
    assert not any("id" in column.lower() for column in matches.columns)


def test_local_perturbation_explanation_is_ranked(service: LiveVQCService) -> None:
    factors = service.perturbation_explanation(service.presets["ckd_like"]["profile"])
    assert len(factors) == 5
    assert factors["Absolute score change"].is_monotonic_decreasing
    assert set(factors["Model influence"]).issubset({"strong influence", "moderate influence", "subtle influence", "minimal"})
    assert not factors["Feature"].str.contains("cause", case=False).any()


def test_demo_presets_are_actual_complete_reference_records(service: LiveVQCService) -> None:
    reference = service.reference_records[EXPECTED_FEATURES]
    assert set(service.presets) == {"ckd_like", "non_ckd_like", "mixed"}
    for preset in service.presets.values():
        profile = preset["profile"]
        mask = np.ones(len(reference), dtype=bool)
        for feature in EXPECTED_FEATURES:
            if feature in {"dm", "appet", "htn"}:
                mask &= reference[feature].astype(str).to_numpy() == str(profile[feature])
            else:
                mask &= np.isclose(reference[feature].astype(float).to_numpy(), float(profile[feature]), equal_nan=False)
        assert mask.any(), preset["label"]


def test_model_comparison_agreement_logic(service: LiveVQCService) -> None:
    mixed = service.model_comparison(service.presets["mixed"]["profile"])
    assert mixed["agreement"] == "2 OF 3 AGREE"
    assert [decision.model for decision in mixed["decisions"]] == ["VQC", "QSVC", "RBF SVM"]
    ckd = service.model_comparison(service.presets["ckd_like"]["profile"])
    assert ckd["agreement"] == "ALL AGREE"


def test_live_copy_has_research_boundaries_and_no_directive_language() -> None:
    source = (ROOT / "src/live_vqc_page.py").read_text().lower()
    required = [
        "research prototype",
        "experimental model classification",
        "model score — not a calibrated disease probability",
        "clinical review required",
        "not clinical precedents",
    ]
    assert all(phrase in source for phrase in required)
    forbidden = [
        "confirmed diagnosis",
        "you have ckd",
        "patient has ckd",
        "prescribe medication",
        "admit patient",
        "refer to nephrology",
    ]
    assert all(phrase not in source for phrase in forbidden)


def test_streamlit_inference_path_cannot_retrain_vqc() -> None:
    inference_source = (ROOT / "src/live_vqc.py").read_text()
    page_source = (ROOT / "src/live_vqc_page.py").read_text()
    app_source = (ROOT / "app.py").read_text()
    assert ".fit(" not in inference_source
    assert ".fit(" not in page_source
    assert "train_live_vqc" not in app_source
    assert "scripts/train_live_vqc.py" not in page_source


def test_frozen_metrics_and_performance_decision(service: LiveVQCService) -> None:
    metrics = service.metrics
    assert metrics["performance_decision"] == "WEAK — DISPLAY WITH CAUTION"
    assert metrics["vqc"]["sensitivity"] == pytest.approx(0.64)
    assert metrics["vqc"]["specificity"] == pytest.approx(0.5666666666666667)
    assert metrics["vqc"]["f1"] == pytest.approx(0.6736842105263158)
    assert metrics["vqc"]["roc_auc"] == pytest.approx(0.676)
    assert metrics["training_runtime_seconds"] == pytest.approx(34.57021299999906)


def test_live_architecture_is_genuinely_different_from_qsvc(service: LiveVQCService) -> None:
    architecture = service.metadata["architecture_difference"]
    assert "non-trainable" in architecture["QSVC"]
    assert "trainable parameterised quantum circuit" in architecture["VQC"]
    assert service.metadata["ansatz"] == "RealAmplitudes"
    assert service.metadata["optimizer"] == "COBYLA"
    assert service.metadata["optimizer_max_iterations"] == 40
