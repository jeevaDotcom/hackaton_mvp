from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from qiskit_machine_learning.kernels import FidelityQuantumKernel
from sklearn.model_selection import RepeatedStratifiedKFold, train_test_split

from scripts.run_phase2 import LOCKED_JSON, LOCKED_PREDICTIONS, evaluate_locked_once
from src.phase1.data import FEATURES, TARGET
from src.phase1.modeling import EXPERIMENT_SEED, OUTER_REPEATS, OUTER_SPLITS, binary_metrics
from src.phase2.benchmark import (
    CLINICAL_SIGNATURES,
    FEATURE_MAP_CONFIGS,
    build_feature_map,
    circuit_resources,
    evaluate_qsvc,
    make_quantum_kernel,
    prepare_fold,
)


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def frame() -> pd.DataFrame:
    value = pd.read_csv(ROOT / "data/processed/ckd_clean.csv", dtype={"row_id": str})
    value[TARGET] = value[TARGET].astype(int)
    return value.set_index("row_id")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fixed_feature_signatures_match_phase1_decision() -> None:
    assert CLINICAL_SIGNATURES == {
        8: ["hemo", "al", "dm", "sg", "pcv", "appet", "htn", "sc"],
        6: ["hemo", "al", "dm", "sg", "pcv", "appet"],
        4: ["hemo", "pcv", "rc", "sc"],
    }
    decision = json.loads((ROOT / "artifacts/development_decision.json").read_text())
    for budget, features in CLINICAL_SIGNATURES.items():
        assert decision["selected_budgets"][str(budget)]["features_frozen_from_complete_development_set"] == features


def test_phase2_uses_frozen_development_ids_and_cv_splits(frame: pd.DataFrame) -> None:
    split = json.loads((ROOT / "artifacts/splits.json").read_text())
    development = frame.loc[split["development_row_ids"]]
    locked = set(split["locked_test_row_ids"])
    assert set(development.index).isdisjoint(locked)
    cv = RepeatedStratifiedKFold(
        n_splits=OUTER_SPLITS, n_repeats=OUTER_REPEATS, random_state=EXPERIMENT_SEED
    )
    folds = list(cv.split(development, development[TARGET]))
    assert len(folds) == 10
    assert all(
        set(development.index[train]).isdisjoint(development.index[valid])
        and set(development.index[train]).isdisjoint(locked)
        and set(development.index[valid]).isdisjoint(locked)
        for train, valid in folds
    )


def test_quantum_preprocessing_fits_training_rows_only(frame: pd.DataFrame) -> None:
    split = json.loads((ROOT / "artifacts/splits.json").read_text())
    development = frame.loc[split["development_row_ids"]]
    train_ids, valid_ids = train_test_split(
        development.index.to_numpy(), test_size=0.2, stratify=development[TARGET], random_state=12
    )
    train, valid = development.loc[train_ids], development.loc[valid_ids]
    train_matrix, valid_matrix, audit, _ = prepare_fold(
        train, valid, representation="clinical", budget=8, seed=12
    )
    assert set(audit["preprocessor_fit_row_ids"]) == set(train.index)
    assert set(audit["preprocessor_fit_row_ids"]).isdisjoint(audit["validation_row_ids"])
    assert train_matrix.shape == (len(train), 8)
    assert valid_matrix.shape == (len(valid), 8)
    assert not np.isnan(train_matrix).any()
    assert not np.isnan(valid_matrix).any()


def test_pca_is_isolated_to_fold_training_rows(frame: pd.DataFrame) -> None:
    development = frame.iloc[:240]
    train, valid = development.iloc[:180], development.iloc[180:]
    train_matrix, valid_matrix, audit, pca_meta = prepare_fold(
        train, valid, representation="pca", budget=6, seed=3
    )
    assert pca_meta["pca_fit_n"] == len(train)
    assert audit["pca_fit_n"] == len(train)
    assert train_matrix.shape == (180, 6)
    assert valid_matrix.shape == (60, 6)


@pytest.mark.parametrize("budget", [4, 6, 8])
@pytest.mark.parametrize("config", list(FEATURE_MAP_CONFIGS))
def test_circuit_and_qubit_count(config: str, budget: int) -> None:
    resources = circuit_resources(config, budget)
    circuit = build_feature_map(config, budget)
    assert resources["qubit_count"] == budget
    assert resources["parameter_count"] == budget
    assert circuit.num_qubits == budget
    assert resources["circuit_depth"] > 0
    assert resources["gate_count"] > 0


def test_kernel_dimensions_and_diagonal() -> None:
    values = np.array([[0.1, 0.2], [0.2, 0.1], [2.8, 3.0], [3.0, 2.8]])
    kernel, _ = make_quantum_kernel("zz_reps1", 2, seed=7)
    matrix = kernel.evaluate(values)
    cross = kernel.evaluate(values[:2], values[2:])
    assert matrix.shape == (4, 4)
    assert cross.shape == (2, 2)
    assert np.allclose(np.diag(matrix), 1.0)
    assert np.allclose(matrix, matrix.T)


def test_fast_exact_kernel_matches_stock_fidelity_quantum_kernel() -> None:
    values = np.array([[0.1, 0.2], [0.2, 0.1], [2.8, 3.0]])
    stock = FidelityQuantumKernel(feature_map=build_feature_map("zz_reps1", 2)).evaluate(values)
    accelerated, _ = make_quantum_kernel("zz_reps1", 2, seed=7)
    observed = accelerated.evaluate(values)
    assert np.allclose(observed, stock, atol=1e-9)


def test_exact_simulator_is_deterministic() -> None:
    values = np.array([[0.1, 0.2], [0.2, 0.1], [2.8, 3.0], [3.0, 2.8]])
    first, _ = make_quantum_kernel("zz_reps1", 2, seed=1)
    second, _ = make_quantum_kernel("zz_reps1", 2, seed=999)
    assert np.allclose(first.evaluate(values), second.evaluate(values), atol=1e-12)


def test_finite_shot_seed_handling() -> None:
    values = np.array([[0.1, 0.2], [0.2, 0.1], [1.1, 0.9], [2.8, 3.0]])
    first, _ = make_quantum_kernel("zz_reps1", 2, shots=64, seed=33)
    second, _ = make_quantum_kernel("zz_reps1", 2, shots=64, seed=33)
    third, _ = make_quantum_kernel("zz_reps1", 2, shots=64, seed=34)
    first_matrix = first.evaluate(values)
    assert np.array_equal(first_matrix, second.evaluate(values))
    assert not np.array_equal(first_matrix, third.evaluate(values))


def test_quantum_metric_path_matches_shared_metric_implementation() -> None:
    train = np.array([[0.0, 0.1], [0.1, 0.0], [2.9, 3.0], [3.0, 2.9], [0.2, 0.2], [2.8, 2.8]])
    y = np.array([0, 0, 1, 1, 0, 1])
    result = evaluate_qsvc(train, y, train, y, config_name="z_reps1", seed=4)
    expected = binary_metrics(y, result["prediction"], result["score"])
    for metric in list(expected):
        assert result[metric] == pytest.approx(expected[metric])


def test_locked_test_guard_precedes_any_loading() -> None:
    source = inspect.getsource(evaluate_locked_once)
    guard_position = source.index("if LOCKED_JSON.exists()")
    frame_load_position = source.index("frame = load_frame()")
    assert guard_position < frame_load_position
    if LOCKED_JSON.exists():
        before = (file_hash(LOCKED_JSON), file_hash(LOCKED_PREDICTIONS))
        evaluate_locked_once()
        after = (file_hash(LOCKED_JSON), file_hash(LOCKED_PREDICTIONS))
        assert after == before
