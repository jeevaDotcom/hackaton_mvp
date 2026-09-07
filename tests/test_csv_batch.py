from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.csv_batch import (
    FEATURE_ORDER,
    MAX_BATCH_ROWS,
    batch_size_error,
    build_batch_results,
    export_results,
    filter_results,
    result_columns,
    suggest_column_mapping,
    summarize_results,
    validate_mapping,
)
from src.live_vqc import LiveVQCService


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def service() -> LiveVQCService:
    return LiveVQCService(ROOT)


def profile_frame(service: LiveVQCService) -> pd.DataFrame:
    return pd.DataFrame([
        service.presets["ckd_like"]["profile"],
        service.presets["non_ckd_like"]["profile"],
    ]).astype(object)


def test_canonical_and_alias_mapping() -> None:
    mapping = suggest_column_mapping([
        "HGB", "Albumin", "Diabetes Mellitus", "Urine Specific Gravity",
        "HCT", "Appetite", "HTN", "Creatinine",
    ])
    assert mapping["hemo"].suggested_column == "HGB"
    assert mapping["pcv"].suggested_column == "HCT"
    assert mapping["sc"].suggested_column == "Creatinine"
    assert all(item.status == "MAPPED" for item in mapping.values())


def test_serum_albumin_is_ambiguous_and_not_auto_mapped() -> None:
    mapping = suggest_column_mapping(["Serum Albumin", "Serum Alb", "HGB"])
    assert mapping["al"].status == "AMBIGUOUS"
    assert mapping["al"].suggested_column is None


def test_missing_and_duplicate_mapping_are_blocked() -> None:
    columns = FEATURE_ORDER.copy()
    assert "Albumin is not mapped" in validate_mapping({feature: None for feature in FEATURE_ORDER}, columns)
    mapping = {feature: feature for feature in FEATURE_ORDER}
    mapping["al"] = "hemo"
    assert any("assigned to multiple features" in error for error in validate_mapping(mapping, columns))


def test_row_validation_is_independent(service: LiveVQCService) -> None:
    frame = profile_frame(service)
    frame.loc[0, "sc"] = "not-a-number"
    frame.loc[1, "dm"] = "unknown2"
    mapping = {feature: feature for feature in FEATURE_ORDER}
    results = build_batch_results(frame, mapping, service)
    assert list(results.validation_status) == ["INVALID", "INVALID"]
    assert "Invalid Serum creatinine" in results.loc[0, "validation_errors"]
    assert "Diabetes mellitus value" in results.loc[1, "validation_errors"]


def test_missing_per_row_value_does_not_block_valid_rows(service: LiveVQCService) -> None:
    frame = profile_frame(service)
    frame.loc[0, "sc"] = None
    mapping = {feature: feature for feature in FEATURE_ORDER}
    results = build_batch_results(frame, mapping, service)
    assert results.loc[0, "validation_status"] == "INVALID"
    assert results.loc[1, "validation_status"] == "VALID"
    assert pd.isna(results.loc[0, "vqc_prediction"])
    assert pd.notna(results.loc[1, "vqc_prediction"])


def test_three_frozen_batch_model_paths_match_single_profile(service: LiveVQCService) -> None:
    profiles = [service.presets["ckd_like"]["profile"], service.presets["mixed"]["profile"]]
    outputs = service.batch_model_outputs(profiles)
    for profile, output in zip(profiles, outputs, strict=True):
        assert output["vqc_score"] == pytest.approx(service.vqc_score(profile))
        assert output["vqc_prediction"] == service.vqc_decision(profile).predicted_class
        assert output["qsvc_prediction"] == service._qsvc_decision(profile).predicted_class  # noqa: SLF001
        assert output["rbf_svm_prediction"] == service._comparator_decision(service.classical_bundle, "RBF SVM", profile).predicted_class  # noqa: SLF001


def test_consensus_and_summary_counts(service: LiveVQCService) -> None:
    frame = profile_frame(service)
    results = build_batch_results(frame, {feature: feature for feature in FEATURE_ORDER}, service)
    summary = summarize_results(results)
    assert summary["total_rows"] == 2
    assert summary["valid_rows"] == 2
    assert summary["invalid_rows"] == 0
    assert set(results.model_agreement) <= {"3 OF 3 AGREE", "2 OF 3 AGREE", "DISAGREEMENT"}
    assert summary["three_of_three"] + summary["two_of_three"] + summary["disagreement"] == 2


def test_filtering_does_not_change_source_results(service: LiveVQCService) -> None:
    results = build_batch_results(profile_frame(service), {feature: feature for feature in FEATURE_ORDER}, service)
    filtered = filter_results(results, validation="Valid", rbf_svm="CKD-like")
    assert len(filtered) <= len(results)
    assert set(results.row_number) == {1, 2}
    assert set(results.columns) == set(result_columns())


def test_export_contains_only_public_result_columns(service: LiveVQCService) -> None:
    results = build_batch_results(profile_frame(service), {feature: feature for feature in FEATURE_ORDER}, service)
    exported = pd.read_csv(pd.io.common.BytesIO(export_results(results)))
    assert list(exported.columns) == result_columns()
    assert "support_vectors" not in " ".join(exported.columns).lower()
    assert "weights" not in " ".join(exported.columns).lower()


def test_sample_batch_and_max_row_guard() -> None:
    sample = pd.read_csv(ROOT / "artifacts/batch_demo/qcare_batch_demo.csv")
    assert 10 <= len(sample) <= 20
    assert "unknown2" in sample["Appetite"].values
    assert batch_size_error(MAX_BATCH_ROWS) is None
    assert batch_size_error(MAX_BATCH_ROWS + 1) is not None


def test_batch_runtime_has_no_training_or_native_qiskit_execution() -> None:
    source = (ROOT / "src/csv_batch.py").read_text() + (ROOT / "src/live_vqc.py").read_text()
    assert ".fit(" not in source
    assert "qiskit_machine_learning" not in source.lower()
    assert "from qiskit" not in source.lower()
