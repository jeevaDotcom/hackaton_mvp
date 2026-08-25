from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedKFold, train_test_split

from src.phase1.data import TARGET, sha256
from src.phase1.modeling import EXPERIMENT_SEED
from src.phase2.benchmark import CLINICAL_SIGNATURES
from src.phase3.validation import (
    FROZEN_FEATURE_MAP,
    calibration_metrics,
    inject_missingness,
    load_bd_kdd,
    load_cleveland,
    load_pima,
    perturb_numeric,
)


ROOT = Path(__file__).resolve().parents[1]


def test_phase3_freeze_matches_phase2_choice() -> None:
    choice = json.loads((ROOT / "artifacts/quantum_development_choice.json").read_text())
    assert choice["feature_map_config"] == FROZEN_FEATURE_MAP == "z_reps1"
    assert CLINICAL_SIGNATURES[8] == ["hemo", "al", "dm", "sg", "pcv", "appet", "htn", "sc"]
    assert CLINICAL_SIGNATURES[6] == ["hemo", "al", "dm", "sg", "pcv", "appet"]


def test_external_dataset_loaders_and_target_mappings() -> None:
    bd = load_bd_kdd(ROOT / "data/external/raw/BD-KDD_Dataset.csv")
    heart = load_cleveland(ROOT / "data/external/raw/heart_disease/processed.cleveland.data")
    pima = load_pima(ROOT / "data/external/raw/openml_37_pima_diabetes.arff")
    assert bd.shape == (988, 9) and bd.target.value_counts().to_dict() == {1: 507, 0: 481}
    assert heart.shape == (303, 14) and heart.target.value_counts().to_dict() == {0: 164, 1: 139}
    assert pima.shape == (768, 9) and pima.target.value_counts().to_dict() == {0: 500, 1: 268}
    assert set(bd.dm.unique()) == {"yes", "no"}
    assert pima[["plas", "pres", "skin", "insu", "mass"]].isna().any().all()


def test_missingness_is_reproducible_and_does_not_mutate_input() -> None:
    source = pd.DataFrame({"a": range(10), "b": range(10, 20), "untouched": range(20, 30)})
    original = source.copy()
    first, count = inject_missingness(source, ["a", "b"], 0.20, 123)
    second, count_again = inject_missingness(source, ["a", "b"], 0.20, 123)
    pd.testing.assert_frame_equal(source, original)
    pd.testing.assert_frame_equal(first, second)
    assert count == count_again == 4
    assert int(first[["a", "b"]].isna().sum().sum()) == 4
    assert first.untouched.equals(original.untouched)


def test_numeric_perturbation_leaves_categories_and_missing_values_alone() -> None:
    frame = pd.DataFrame({
        "hemo": [10.0, np.nan, 12.0], "al": [1.0, 2.0, 3.0], "sg": [1.01, 1.02, 1.03],
        "pcv": [30.0, 35.0, 40.0], "sc": [1.0, 2.0, 3.0], "dm": ["no", "yes", "no"],
    })
    changed = perturb_numeric(frame, frame, 0.1, 42)
    assert changed.dm.equals(frame.dm)
    assert np.isnan(changed.loc[1, "hemo"])
    assert not np.allclose(changed.al, frame.al)


def test_perturbation_is_reproducible() -> None:
    frame = pd.DataFrame({
        "hemo": [10.0, 11.0, 12.0], "al": [1.0, 2.0, 3.0], "sg": [1.01, 1.02, 1.03],
        "pcv": [30.0, 35.0, 40.0], "sc": [1.0, 2.0, 3.0],
    })
    pd.testing.assert_frame_equal(perturb_numeric(frame, frame, 0.05, 99), perturb_numeric(frame, frame, 0.05, 99))


def test_calibration_metrics_are_finite() -> None:
    result = calibration_metrics(np.array([0, 0, 1, 1]), np.array([0.1, 0.3, 0.7, 0.9]))
    assert set(result) == {"brier", "log_loss", "ece_10_bin"}
    assert all(np.isfinite(list(result.values())))


def _development() -> pd.DataFrame:
    frame = pd.read_csv(ROOT / "data/processed/ckd_clean.csv", dtype={"row_id": str}).set_index("row_id")
    split = json.loads((ROOT / "artifacts/splits.json").read_text())
    return frame.loc[split["development_row_ids"]]


def test_repeated_cv_partitions_are_reproducible() -> None:
    development = _development()
    splitter_a = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=EXPERIMENT_SEED)
    splitter_b = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=EXPERIMENT_SEED)
    splits_a = [(train.tolist(), valid.tolist()) for train, valid in splitter_a.split(development, development[TARGET])]
    splits_b = [(train.tolist(), valid.tolist()) for train, valid in splitter_b.split(development, development[TARGET])]
    assert splits_a == splits_b and len(splits_a) == 50


def test_prevalence_resampling_is_reproducible_and_hits_target() -> None:
    source = pd.DataFrame({"target": np.repeat([0, 1], 50), "score": np.linspace(-2, 2, 100)})
    def sample(seed: int) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        positive, negative = source[source.target == 1], source[source.target == 0]
        return pd.concat([positive.iloc[rng.choice(50, 70, replace=True)], negative.iloc[rng.choice(50, 30, replace=True)]]).reset_index(drop=True)
    first, second = sample(7), sample(7)
    pd.testing.assert_frame_equal(first, second)
    assert first.target.mean() == 0.70


def test_calibration_partitions_are_disjoint_from_outer_validation() -> None:
    development = _development()
    outer = StratifiedKFold(n_splits=5, shuffle=True, random_state=EXPERIMENT_SEED)
    for fold, (outer_train_pos, valid_pos) in enumerate(outer.split(development, development[TARGET]), start=1):
        outer_train, valid = development.iloc[outer_train_pos], development.iloc[valid_pos]
        proper, calibrate = train_test_split(outer_train, test_size=0.25, stratify=outer_train[TARGET], random_state=EXPERIMENT_SEED + fold)
        assert set(proper.index).isdisjoint(calibrate.index)
        assert set(proper.index).isdisjoint(valid.index)
        assert set(calibrate.index).isdisjoint(valid.index)
        assert set(proper.index) | set(calibrate.index) == set(outer_train.index)


def test_claim_values_match_phase3_summary() -> None:
    summary = pd.read_csv(ROOT / "artifacts/phase3/reference_cv_summary.csv")
    qsvc = summary[(summary.budget == 8) & (summary.model == "qsvc")].iloc[0]
    results = (ROOT / "research/phase3_results.md").read_text()
    assert f"sensitivity {qsvc.sensitivity_mean:.3f}" in results
    assert f"ROC-AUC {qsvc.roc_auc_mean:.3f}" in results


def test_final_model_manifest_and_bundles_are_consistent() -> None:
    manifest = json.loads((ROOT / "artifacts/final_model_manifest.json").read_text())
    assert manifest["output_contract"]["probability_permitted"] is False
    assert manifest["feature_signatures"]["8"] == CLINICAL_SIGNATURES[8]
    assert manifest["classifiers"]["qsvc"]["feature_map_config"] == FROZEN_FEATURE_MAP
    assert manifest["primary_freeze"]["input_budget"] == 8
    assert manifest["display_metrics"]["qsvc_8"]["source_artifact"] == "artifacts/phase3/reference_cv_summary.csv"
    development = _development()
    for entry in manifest["models"]:
        path = ROOT / entry["path"]
        assert sha256(path) == entry["sha256"]
        bundle = joblib.load(path)
        assert bundle["features"] == CLINICAL_SIGNATURES[int(entry["budget"])]
        matrix = bundle["preprocessor"].transform(development[bundle["features"]].head(3))
        assert len(bundle["model"].predict(matrix)) == 3
