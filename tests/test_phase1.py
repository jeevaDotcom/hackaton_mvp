from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.phase1.data import (
    CATEGORICAL_FEATURES,
    FEATURES,
    NUMERIC_FEATURES,
    TARGET,
    load_official_arff,
    make_locked_split,
)
from src.phase1.modeling import (
    binary_metrics,
    make_pipeline,
    make_preprocessor,
    rank_source_features,
)


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/chronic_kidney_disease.arff"


@pytest.fixture(scope="module")
def frame() -> pd.DataFrame:
    return load_official_arff(RAW).frame.set_index("row_id")


def test_dataset_schema_and_target_cleanup(frame: pd.DataFrame) -> None:
    assert frame.shape == (400, 25)
    assert list(frame.columns) == FEATURES + [TARGET]
    assert frame[TARGET].value_counts().to_dict() == {1: 250, 0: 150}
    assert set(frame[TARGET].unique()) == {0, 1}


def test_unknown_target_is_rejected(tmp_path: Path) -> None:
    values = [
        "45", "80", "1.020", "1", "0", "normal", "normal", "notpresent", "notpresent",
        "110", "40", "1.0", "140", "4.2", "13", "42", "7000", "5.0", "no", "no",
        "no", "good", "no", "no", "unknown_label",
    ]
    path = tmp_path / "invalid_target.arff"
    path.write_text("@relation test\n@data\n" + ",".join(values) + "\n")
    with pytest.raises(ValueError, match="unexpected target label"):
        load_official_arff(path)


def test_explicit_raw_repairs_are_stable() -> None:
    parsed = load_official_arff(RAW)
    repairs = parsed.provenance["column_repairs"]
    assert [item["row_id"] for item in repairs] == ["ckd-0070", "ckd-0073", "ckd-0370"]
    assert parsed.provenance["total_missing_predictor_cells"] == 1012
    assert parsed.provenance["rows_with_missing_predictors"] == 242


def test_split_ids_are_reproducible_and_disjoint(frame: pd.DataFrame) -> None:
    first = make_locked_split(frame.reset_index())
    second = make_locked_split(frame.reset_index())
    assert first == second
    development = set(first["development_row_ids"])
    locked = set(first["locked_test_row_ids"])
    assert len(development) == 320
    assert len(locked) == 80
    assert development.isdisjoint(locked)
    assert development | locked == set(frame.index)


def test_saved_split_matches_deterministic_split(frame: pd.DataFrame) -> None:
    split_path = ROOT / "artifacts/splits.json"
    if not split_path.exists():
        pytest.skip("prepare stage has not generated artifacts/splits.json yet")
    assert json.loads(split_path.read_text()) == make_locked_split(frame.reset_index())


def test_preprocessor_fits_training_statistics_only_and_removes_missing() -> None:
    train = pd.DataFrame({"age": [1.0, 2.0, np.nan, 3.0], "rbc": ["normal", None, "abnormal", "normal"]})
    test = pd.DataFrame({"age": [1000.0, np.nan], "rbc": ["abnormal", None]})
    preprocessor = make_preprocessor(["age", "rbc"], scale=True)
    transformed_train = preprocessor.fit_transform(train, np.array([0, 0, 1, 1]))
    transformed_test = preprocessor.transform(test)
    numeric_imputer = preprocessor.named_transformers_["numeric"].named_steps["imputer"]
    assert numeric_imputer.statistics_[0] == pytest.approx(2.0)
    assert not np.isnan(transformed_train).any()
    assert not np.isnan(transformed_test).any()


def test_full_preprocessing_has_no_missing_values(frame: pd.DataFrame) -> None:
    split = make_locked_split(frame.reset_index())
    train = frame.loc[split["development_row_ids"], FEATURES]
    test = frame.loc[split["locked_test_row_ids"], FEATURES]
    preprocessor = make_preprocessor(FEATURES, scale=True)
    train_t = preprocessor.fit_transform(train)
    test_t = preprocessor.transform(test)
    assert train_t.shape[0] == 320
    assert test_t.shape[0] == 80
    assert not np.isnan(train_t).any()
    assert not np.isnan(test_t).any()


@pytest.mark.parametrize("method", ["mutual_information", "wrapper_rfe", "permutation_importance"])
def test_feature_selection_fits_only_supplied_training_rows(frame: pd.DataFrame, method: str) -> None:
    split = make_locked_split(frame.reset_index())
    train_ids = split["development_row_ids"]
    excluded_ids = set(split["locked_test_row_ids"])
    ranking = rank_source_features(
        frame.loc[train_ids, FEATURES],
        frame.loc[train_ids, TARGET],
        method,
        seed=123,
    )
    assert set(ranking.fit_row_ids) == set(train_ids)
    assert set(ranking.fit_row_ids).isdisjoint(excluded_ids)
    assert len(ranking.top(8)) == 8
    assert len(set(ranking.top(8))) == 8


def test_pca_is_fitted_on_training_rows_only(frame: pd.DataFrame) -> None:
    split = make_locked_split(frame.reset_index())
    train_ids = split["development_row_ids"]
    test_ids = split["locked_test_row_ids"]
    train = frame.loc[train_ids]
    test = frame.loc[test_ids]
    pipeline, _ = make_pipeline("logistic_regression", FEATURES, seed=7, pca_components=4)
    pipeline.fit(train[FEATURES], train[TARGET])
    transformed = pipeline.named_steps["preprocess"].transform(test[FEATURES])
    projected = pipeline.named_steps["pca"].transform(transformed)
    assert pipeline.named_steps["pca"].n_samples_ == len(train)
    assert projected.shape == (len(test), 4)
    assert not np.isnan(projected).any()


def test_metric_and_specificity_calculation() -> None:
    y_true = [0, 0, 0, 1, 1, 1]
    y_pred = [0, 1, 0, 1, 0, 1]
    y_score = [0.1, 0.8, 0.2, 0.9, 0.4, 0.7]
    metrics = binary_metrics(y_true, y_pred, y_score)
    assert metrics["tn"] == 2
    assert metrics["fp"] == 1
    assert metrics["fn"] == 1
    assert metrics["tp"] == 2
    assert metrics["specificity"] == pytest.approx(2 / 3)
    assert metrics["sensitivity"] == pytest.approx(2 / 3)
    assert 0 <= metrics["roc_auc"] <= 1


def test_ranking_reproducibility_with_fixed_seed(frame: pd.DataFrame) -> None:
    sample = frame.iloc[:200]
    first = rank_source_features(sample[FEATURES], sample[TARGET], "mutual_information", seed=99)
    second = rank_source_features(sample[FEATURES], sample[TARGET], "mutual_information", seed=99)
    pd.testing.assert_frame_equal(first.table, second.table)


def test_locked_artifacts_use_only_frozen_test_ids() -> None:
    split_path = ROOT / "artifacts/splits.json"
    predictions_path = ROOT / "artifacts/locked_test_predictions.csv"
    if not predictions_path.exists():
        pytest.skip("locked test has not been evaluated yet")
    split = json.loads(split_path.read_text())
    predictions = pd.read_csv(predictions_path, dtype={"row_id": str})
    assert set(predictions["row_id"]) == set(split["locked_test_row_ids"])
    assert set(predictions["row_id"]).isdisjoint(split["development_row_ids"])
    assert len(predictions) == 80


def test_phase1_outputs_are_structurally_complete() -> None:
    decision = ROOT / "research/phase1_decision.md"
    if not decision.exists():
        pytest.skip("final reports have not been generated yet")
    lines = [line for line in decision.read_text().splitlines() if line.strip()]
    assert len(lines) == 18
    assert all(line.startswith(f"{number}. ") for number, line in enumerate(lines, start=1))
    figures = sorted((ROOT / "reports/figures").glob("*.png"))
    assert len(figures) == 10
    assert all(path.stat().st_size > 0 for path in figures)
