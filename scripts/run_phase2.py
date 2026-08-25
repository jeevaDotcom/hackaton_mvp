from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from datetime import date
from importlib.metadata import version
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", "/tmp/qcare-phase2-matplotlib-cache")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/qcare-phase2-xdg-cache")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error
from qiskit_aer.primitives import SamplerV2
from qiskit_machine_learning.algorithms import QSVC
from qiskit_machine_learning.kernels import FidelityQuantumKernel
from qiskit_machine_learning.state_fidelities import ComputeUncompute
from sklearn.decomposition import PCA
from sklearn.metrics import precision_recall_curve, roc_curve
from sklearn.model_selection import train_test_split

from src.phase1.data import FEATURES, TARGET, sha256
from src.phase1.modeling import EXPERIMENT_SEED, binary_metrics, bootstrap_metric_intervals, make_preprocessor
from src.phase2.benchmark import (
    CLASSIFIER_C,
    CLINICAL_SIGNATURES,
    FEATURE_MAP_CONFIGS,
    METRICS,
    TOLERANCE,
    TrackedFidelityQuantumKernel,
    build_feature_map,
    choose_best_qsvc,
    circuit_resources,
    evaluate_classical,
    evaluate_qsvc,
    json_sha256,
    kernel_diagnostics,
    make_quantum_kernel,
    paired_comparisons,
    prepare_fold,
    run_repeated_cv,
    summarise_results,
    to_jsonable,
    write_json,
)


PROCESSED_CSV = PROJECT_ROOT / "data/processed/ckd_clean.csv"
SPLITS_JSON = PROJECT_ROOT / "artifacts/splits.json"
PHASE1_DECISION = PROJECT_ROOT / "artifacts/development_decision.json"
PHASE1_LOCKED = PROJECT_ROOT / "artifacts/locked_test_evaluation.json"
PHASE1_PREDICTIONS = PROJECT_ROOT / "artifacts/locked_test_predictions.csv"

ENVIRONMENT_JSON = PROJECT_ROOT / "artifacts/quantum_environment.json"
CV_RESULTS_CSV = PROJECT_ROOT / "artifacts/quantum_cv_results.csv"
CV_SUMMARY_CSV = PROJECT_ROOT / "artifacts/quantum_cv_summary.csv"
PREPROCESS_AUDIT_JSON = PROJECT_ROOT / "artifacts/quantum_preprocessing_audit.json"
DEVELOPMENT_CHOICE_JSON = PROJECT_ROOT / "artifacts/quantum_development_choice.json"
DIAGNOSTICS_CSV = PROJECT_ROOT / "artifacts/quantum_kernel_diagnostics.csv"
KERNEL_DIR = PROJECT_ROOT / "artifacts/quantum/kernels"
TRAINING_SIZE_CSV = PROJECT_ROOT / "artifacts/quantum_training_size_results.csv"
SHOTS_CSV = PROJECT_ROOT / "artifacts/quantum_finite_shot_results.csv"
NOISE_CSV = PROJECT_ROOT / "artifacts/quantum_noise_results.csv"
CONFIG_JSON = PROJECT_ROOT / "artifacts/quantum_config.json"
LOCKED_JSON = PROJECT_ROOT / "artifacts/phase2_locked_test_evaluation.json"
LOCKED_PREDICTIONS = PROJECT_ROOT / "artifacts/phase2_locked_test_predictions.csv"
PAIRED_CSV = PROJECT_ROOT / "artifacts/quantum_paired_fold_deltas.csv"
PAIRED_SUMMARY_CSV = PROJECT_ROOT / "artifacts/quantum_paired_comparison_summary.csv"

REPORT_DIR = PROJECT_ROOT / "reports/quantum"
FIGURE_DIR = REPORT_DIR / "figures"


def fmt(value: Any, digits: int = 3) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "NR"
    return f"{float(value):.{digits}f}"


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    def clean(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = ["| " + " | ".join(clean(value) for value in headers) + " |"]
    lines.append("|" + "|".join("---" for _ in headers) + "|")
    lines.extend("| " + " | ".join(clean(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def save_figure(fig: plt.Figure, name: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / name, dpi=180, bbox_inches="tight")
    plt.close(fig)


def load_frame() -> pd.DataFrame:
    frame = pd.read_csv(PROCESSED_CSV, dtype={"row_id": str}).set_index("row_id")
    frame[TARGET] = frame[TARGET].astype(int)
    return frame


def load_development() -> pd.DataFrame:
    frame = load_frame()
    split = json.loads(SPLITS_JSON.read_text())
    return frame.loc[split["development_row_ids"]].copy()


def assert_phase1_freeze() -> None:
    decision = json.loads(PHASE1_DECISION.read_text())
    for budget, expected in CLINICAL_SIGNATURES.items():
        actual = decision["selected_budgets"][str(budget)]["features_frozen_from_complete_development_set"]
        if actual != expected:
            raise RuntimeError(f"Phase 1 signature drift at budget {budget}: {actual} != {expected}")
    split = json.loads(SPLITS_JSON.read_text())
    if set(split["development_row_ids"]) & set(split["locked_test_row_ids"]):
        raise RuntimeError("Frozen development and locked-test IDs overlap")


def environment_and_smoke_test() -> None:
    assert_phase1_freeze()
    from qiskit.circuit.library import zz_feature_map

    x = np.array([[0.10, 0.20], [0.20, 0.10], [2.80, 3.00], [3.00, 2.80]])
    y = np.array([0, 0, 1, 1])
    stages: dict[str, Any] = {}
    started = time.perf_counter()
    feature_map = zz_feature_map(2, reps=1, entanglement="full")
    stages["circuit_construction_seconds"] = time.perf_counter() - started
    kernel = FidelityQuantumKernel(feature_map=feature_map)
    started = time.perf_counter()
    matrix = kernel.evaluate(x)
    stages["kernel_evaluation_seconds"] = time.perf_counter() - started
    model = QSVC(quantum_kernel=kernel, C=CLASSIFIER_C)
    started = time.perf_counter()
    model.fit(x, y)
    stages["fit_seconds"] = time.perf_counter() - started
    started = time.perf_counter()
    predictions = model.predict(x)
    stages["prediction_seconds"] = time.perf_counter() - started
    if not np.array_equal(predictions, y):
        raise RuntimeError("Tiny stock-Qiskit QSVC smoke test did not fit the separable toy data")
    resources = circuit_resources("zz_reps1", 2)
    payload = {
        "generated_on": date.today().isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "versions": {
            "qiskit": version("qiskit"),
            "qiskit_machine_learning": version("qiskit-machine-learning"),
            "qiskit_aer": version("qiskit-aer"),
            "numpy": version("numpy"),
            "scipy": version("scipy"),
            "scikit_learn": version("scikit-learn"),
        },
        "smoke_test": {
            "status": "passed",
            "simulator_backend": "Qiskit Machine Learning QMLSampler exact statevector mode (stock FidelityQuantumKernel default)",
            "execution_mode": "local exact statevector",
            "number_of_qubits": 2,
            "circuit": resources,
            "kernel_matrix_shape": list(matrix.shape),
            "kernel_diagonal": np.diag(matrix).tolist(),
            "fit_predictions": predictions.tolist(),
            **stages,
        },
        "benchmark_executor": {
            "class": "FastStatevectorFidelity passed to FidelityQuantumKernel",
            "reason": "Exact cached statevectors avoid repeated reference-sampler circuit construction while preserving |<phi(x)|phi(y)>|^2.",
            "equivalence_check": "covered by automated test against stock FidelityQuantumKernel",
        },
    }
    write_json(ENVIRONMENT_JSON, payload)
    print("Quantum environment frozen; stock QSVC smoke test passed.")


def run_development() -> None:
    assert_phase1_freeze()
    if CV_RESULTS_CSV.exists() and DEVELOPMENT_CHOICE_JSON.exists():
        print("Quantum development results already exist; skipping CV.")
        return
    development = load_development()
    result_parts: list[pd.DataFrame] = []
    audits: list[dict[str, Any]] = []
    for budget in (8, 6, 4):
        print(f"Development CV: clinical budget {budget}", flush=True)
        part, audit = run_repeated_cv(
            development,
            representations=["clinical"],
            budgets=[budget],
            quantum_configs=FEATURE_MAP_CONFIGS,
        )
        result_parts.append(part)
        audits.extend(audit)
        pd.concat(result_parts, ignore_index=True).to_csv(CV_RESULTS_CSV, index=False)
        write_json(PREPROCESS_AUDIT_JSON, audits)
    clinical = pd.concat(result_parts, ignore_index=True)
    clinical_summary = summarise_results(clinical)
    choice = choose_best_qsvc(clinical_summary)
    write_json(DEVELOPMENT_CHOICE_JSON, choice)
    print(f"Frozen development feature-map choice: {choice['feature_map_config']}", flush=True)

    for budget in (8, 6, 4):
        print(f"Development CV: PCA budget {budget}", flush=True)
        part, audit = run_repeated_cv(
            development,
            representations=["pca"],
            budgets=[budget],
            quantum_configs=[choice["feature_map_config"]],
        )
        result_parts.append(part)
        audits.extend(audit)
        pd.concat(result_parts, ignore_index=True).to_csv(CV_RESULTS_CSV, index=False)
        write_json(PREPROCESS_AUDIT_JSON, audits)

    results = pd.concat(result_parts, ignore_index=True)
    summary = summarise_results(results)
    results.to_csv(CV_RESULTS_CSV, index=False)
    summary.to_csv(CV_SUMMARY_CSV, index=False)
    fold_deltas, comparison = paired_comparisons(results, choice["feature_map_config"])
    fold_deltas.to_csv(PAIRED_CSV, index=False)
    comparison.to_csv(PAIRED_SUMMARY_CSV, index=False)
    run_kernel_diagnostics(development, choice["feature_map_config"])


def diagnostic_sample(development: pd.DataFrame) -> pd.DataFrame:
    negative = development[development[TARGET] == 0].sample(n=30, random_state=EXPERIMENT_SEED)
    positive = development[development[TARGET] == 1].sample(n=50, random_state=EXPERIMENT_SEED)
    return pd.concat([negative, positive]).sample(frac=1, random_state=EXPERIMENT_SEED)


def run_kernel_diagnostics(development: pd.DataFrame, best_config: str) -> None:
    KERNEL_DIR.mkdir(parents=True, exist_ok=True)
    sample = diagnostic_sample(development)
    records: list[dict[str, Any]] = []
    for representation in ("clinical", "pca"):
        configs = list(FEATURE_MAP_CONFIGS) if representation == "clinical" else [best_config]
        for budget in (8, 6, 4):
            matrix, _, _, pca_meta = prepare_fold(
                sample, sample, representation=representation, budget=budget, seed=EXPERIMENT_SEED
            )
            for config_name in configs:
                kernel, metadata = make_quantum_kernel(config_name, budget, seed=EXPERIMENT_SEED)
                started = time.perf_counter()
                kernel_matrix = kernel.evaluate(matrix)
                elapsed = time.perf_counter() - started
                record = {
                    "representation": representation,
                    "budget": budget,
                    "feature_map_config": config_name,
                    "evaluation_seconds": elapsed,
                    **pca_meta,
                    **circuit_resources(config_name, budget),
                    **kernel_diagnostics(kernel_matrix, sample[TARGET].to_numpy(dtype=int)),
                }
                records.append(record)
                if config_name == best_config and (representation, budget) in {
                    ("clinical", 8), ("clinical", 6), ("pca", 6)
                }:
                    np.savez_compressed(
                        KERNEL_DIR / f"{representation}_{budget}_{config_name}.npz",
                        kernel=kernel_matrix,
                        target=sample[TARGET].to_numpy(dtype=int),
                        row_ids=sample.index.to_numpy(),
                    )
    pd.DataFrame(records).to_csv(DIAGNOSTICS_CSV, index=False)


def _stratified_fraction(frame: pd.DataFrame, fraction: float, seed: int) -> pd.DataFrame:
    if fraction >= 1.0:
        return frame.copy()
    selected: list[pd.DataFrame] = []
    for _, group in frame.groupby(TARGET):
        count = max(2, int(round(len(group) * fraction)))
        selected.append(group.sample(n=count, random_state=seed))
    return pd.concat(selected).sample(frac=1, random_state=seed)


def run_training_size() -> None:
    if TRAINING_SIZE_CSV.exists():
        print("Training-size results already exist; skipping.")
        return
    choice = json.loads(DEVELOPMENT_CHOICE_JSON.read_text())
    development = load_development()
    train_ids, valid_ids = train_test_split(
        development.index.to_numpy(),
        test_size=0.20,
        stratify=development[TARGET].to_numpy(),
        random_state=EXPERIMENT_SEED + 100,
    )
    pool = development.loc[train_ids]
    valid = development.loc[valid_ids]
    rows: list[dict[str, Any]] = []
    for fraction in (0.25, 0.50, 0.75, 1.00):
        for repeat in range(1, 4):
            seed = EXPERIMENT_SEED + 1000 + repeat + int(fraction * 100)
            train = _stratified_fraction(pool, fraction, seed)
            train_matrix, valid_matrix, _, _ = prepare_fold(
                train, valid, representation="clinical", budget=8, seed=seed
            )
            classical = evaluate_classical(
                train_matrix,
                train[TARGET].to_numpy(dtype=int),
                valid_matrix,
                valid[TARGET].to_numpy(dtype=int),
                seed=seed,
            )
            quantum = evaluate_qsvc(
                train_matrix,
                train[TARGET].to_numpy(dtype=int),
                valid_matrix,
                valid[TARGET].to_numpy(dtype=int),
                config_name=choice["feature_map_config"],
                seed=seed,
            )
            for model, result in (("classical_rbf_svm", classical), ("qsvc", quantum)):
                rows.append(
                    {
                        "training_fraction": fraction,
                        "training_n": len(train),
                        "validation_n": len(valid),
                        "repeat": repeat,
                        "model": model,
                        "feature_map_config": choice["feature_map_config"] if model == "qsvc" else "rbf",
                        **{
                            key: value
                            for key, value in result.items()
                            if key in METRICS
                            or key in {
                                "training_wall_seconds", "prediction_wall_seconds",
                                "train_kernel_seconds", "kernel_evaluations_train",
                            }
                        },
                    }
                )
            print(f"Training-size {fraction:.0%}, repeat {repeat} complete", flush=True)
    pd.DataFrame(rows).to_csv(TRAINING_SIZE_CSV, index=False)


def _fixed_six_variable_split(development: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_ids, valid_ids = train_test_split(
        development.index.to_numpy(),
        test_size=0.25,
        stratify=development[TARGET].to_numpy(),
        random_state=EXPERIMENT_SEED + 200,
    )
    return development.loc[train_ids], development.loc[valid_ids]


def run_finite_shots() -> None:
    if SHOTS_CSV.exists():
        print("Finite-shot results already exist; skipping.")
        return
    choice = json.loads(DEVELOPMENT_CHOICE_JSON.read_text())
    train, valid = _fixed_six_variable_split(load_development())
    train_matrix, valid_matrix, _, _ = prepare_fold(
        train, valid, representation="clinical", budget=6, seed=EXPERIMENT_SEED
    )
    rows: list[dict[str, Any]] = []
    classical = evaluate_classical(
        train_matrix,
        train[TARGET].to_numpy(dtype=int),
        valid_matrix,
        valid[TARGET].to_numpy(dtype=int),
        seed=EXPERIMENT_SEED,
    )
    rows.append(
        {
            "shots": 0,
            "seed": EXPERIMENT_SEED,
            "mode": "classical_reference",
            "feature_map_config": "rbf",
            **{key: classical[key] for key in METRICS + ("training_wall_seconds", "prediction_wall_seconds")},
        }
    )
    ideal = evaluate_qsvc(
        train_matrix,
        train[TARGET].to_numpy(dtype=int),
        valid_matrix,
        valid[TARGET].to_numpy(dtype=int),
        config_name=choice["feature_map_config"],
        seed=EXPERIMENT_SEED,
        shots=None,
    )
    rows.append(
        {
            "shots": 0,
            "seed": EXPERIMENT_SEED,
            "mode": "ideal_qsvc",
            "feature_map_config": choice["feature_map_config"],
            **{key: ideal[key] for key in METRICS + ("training_wall_seconds", "prediction_wall_seconds", "train_kernel_seconds")},
        }
    )
    for shots in (256, 1024, 4096):
        for replicate, seed_offset in enumerate((11, 29, 47), start=1):
            seed = EXPERIMENT_SEED + shots + seed_offset
            result = evaluate_qsvc(
                train_matrix,
                train[TARGET].to_numpy(dtype=int),
                valid_matrix,
                valid[TARGET].to_numpy(dtype=int),
                config_name=choice["feature_map_config"],
                seed=seed,
                shots=shots,
            )
            rows.append(
                {
                    "shots": shots,
                    "seed": seed,
                    "replicate": replicate,
                    "mode": "finite_shot_qsvc",
                    "feature_map_config": choice["feature_map_config"],
                    **{key: result[key] for key in METRICS + ("training_wall_seconds", "prediction_wall_seconds", "train_kernel_seconds")},
                }
            )
        print(f"Finite-shot {shots} complete", flush=True)
    frame = pd.DataFrame(rows)
    for metric in ("sensitivity", "specificity", "f1", "roc_auc"):
        frame[f"{metric}_delta_vs_ideal"] = frame[metric] - ideal[metric]
    frame.to_csv(SHOTS_CSV, index=False)


NOISE_CONDITIONS: dict[str, dict[str, float]] = {
    "ideal": {"one_qubit_depolarizing": 0.0, "two_qubit_depolarizing": 0.0, "readout": 0.0},
    "low": {"one_qubit_depolarizing": 0.001, "two_qubit_depolarizing": 0.01, "readout": 0.01},
    "moderate": {"one_qubit_depolarizing": 0.005, "two_qubit_depolarizing": 0.03, "readout": 0.03},
}


def build_noise_model(condition: str) -> NoiseModel | None:
    rates = NOISE_CONDITIONS[condition]
    if condition == "ideal":
        return None
    model = NoiseModel()
    model.add_all_qubit_quantum_error(
        depolarizing_error(rates["one_qubit_depolarizing"], 1), ["sx", "x"]
    )
    model.add_all_qubit_quantum_error(
        depolarizing_error(rates["two_qubit_depolarizing"], 2), ["cx"]
    )
    readout = rates["readout"]
    model.add_all_qubit_readout_error(ReadoutError([[1 - readout, readout], [readout, 1 - readout]]))
    return model


def make_aer_kernel(
    config_name: str,
    feature_count: int,
    *,
    condition: str,
    shots: int,
    seed: int,
) -> tuple[TrackedFidelityQuantumKernel, dict[str, Any]]:
    started = time.perf_counter()
    noise_model = build_noise_model(condition)
    backend = AerSimulator(noise_model=noise_model)
    pass_manager = generate_preset_pass_manager(optimization_level=0, backend=backend)
    sampler_options = {"backend_options": {"noise_model": noise_model}} if noise_model else {}
    sampler = SamplerV2(default_shots=shots, seed=seed, options=sampler_options)
    fidelity = ComputeUncompute(sampler, pass_manager=pass_manager)
    kernel = TrackedFidelityQuantumKernel(
        feature_map=build_feature_map(config_name, feature_count),
        fidelity=fidelity,
        enforce_psd=True,
        evaluate_duplicates="off_diagonal",
        max_circuits_per_job=1024,
    )
    metadata = circuit_resources(config_name, feature_count)
    metadata.update(
        {
            "kernel_backend": "qiskit_aer.primitives.SamplerV2 / AerSimulator",
            "execution_mode": f"finite-shot Aer compute-uncompute; {condition} noise",
            "shots": shots,
            "seed": seed,
            "feature_map_construction_seconds": time.perf_counter() - started,
        }
    )
    return kernel, metadata


def run_noise() -> None:
    if NOISE_CSV.exists():
        print("Noise results already exist; skipping.")
        return
    choice = json.loads(DEVELOPMENT_CHOICE_JSON.read_text())
    development = load_development()
    sample_ids, _ = train_test_split(
        development.index.to_numpy(),
        train_size=72,
        stratify=development[TARGET].to_numpy(),
        random_state=EXPERIMENT_SEED + 300,
    )
    sample = development.loc[sample_ids]
    train_ids, valid_ids = train_test_split(
        sample.index.to_numpy(),
        test_size=24,
        stratify=sample[TARGET].to_numpy(),
        random_state=EXPERIMENT_SEED + 301,
    )
    train, valid = sample.loc[train_ids], sample.loc[valid_ids]
    train_matrix, valid_matrix, _, _ = prepare_fold(
        train, valid, representation="clinical", budget=6, seed=EXPERIMENT_SEED
    )
    rows: list[dict[str, Any]] = []
    for condition in ("ideal", "low", "moderate"):
        for replicate, offset in enumerate((17, 53), start=1):
            seed = EXPERIMENT_SEED + offset
            kernel, metadata = make_aer_kernel(
                choice["feature_map_config"], 6, condition=condition, shots=1024, seed=seed
            )
            result = evaluate_qsvc(
                train_matrix,
                train[TARGET].to_numpy(dtype=int),
                valid_matrix,
                valid[TARGET].to_numpy(dtype=int),
                config_name=choice["feature_map_config"],
                seed=seed,
                shots=1024,
                kernel=kernel,
                kernel_metadata=metadata,
            )
            rows.append(
                {
                    "condition": condition,
                    "replicate": replicate,
                    "seed": seed,
                    "train_n": len(train),
                    "valid_n": len(valid),
                    **NOISE_CONDITIONS[condition],
                    **{
                        key: result[key]
                        for key in METRICS
                        + (
                            "training_wall_seconds", "prediction_wall_seconds", "train_kernel_seconds",
                            "qubit_count", "circuit_depth", "gate_count", "shots",
                        )
                    },
                }
            )
            print(f"Aer noise {condition}, replicate {replicate} complete", flush=True)
    frame = pd.DataFrame(rows)
    ideal_means = frame[frame["condition"] == "ideal"][list(METRICS)].mean()
    for metric in ("sensitivity", "specificity", "accuracy", "f1", "roc_auc"):
        frame[f"{metric}_delta_vs_ideal_mean"] = frame[metric] - ideal_means[metric]
    frame.to_csv(NOISE_CSV, index=False)


def freeze_configuration() -> dict[str, Any]:
    required = [
        ENVIRONMENT_JSON, CV_RESULTS_CSV, CV_SUMMARY_CSV, DEVELOPMENT_CHOICE_JSON,
        DIAGNOSTICS_CSV, TRAINING_SIZE_CSV, SHOTS_CSV, NOISE_CSV,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f"Cannot freeze Phase 2 configuration; missing: {missing}")
    choice = json.loads(DEVELOPMENT_CHOICE_JSON.read_text())
    payload = {
        "frozen_on": date.today().isoformat(),
        "configuration_frozen_before_phase2_locked_evaluation": True,
        "locked_test_was_used_for_configuration": False,
        "shared_test_disclosure": "The 80-patient holdout was already used for Phase 1 confirmation; it is not a pristine external validation cohort.",
        "feature_map_config": choice["feature_map_config"],
        "feature_map": choice["feature_map"],
        "reps": choice["reps"],
        "entanglement": choice["entanglement"],
        "classifier_C": CLASSIFIER_C,
        "clinical_signatures": {str(budget): features for budget, features in CLINICAL_SIGNATURES.items()},
        "pca_components": [8, 6, 4],
        "preprocessing": "Phase 1 median/mode imputation, binary one-hot encoding and standard scaling fitted on training rows only; PCA fitted after preprocessing on training rows only.",
        "ideal_kernel_backend": "FidelityQuantumKernel with exact cached qiskit Statevector fidelity",
        "selection_rule": choice["selection_rule"],
        "selection_scope": choice["selection_scope"],
        "predefined_tolerance": TOLERANCE,
        "finite_shots": [256, 1024, 4096],
        "noise_conditions": NOISE_CONDITIONS,
        "split_artifact_sha256": sha256(SPLITS_JSON),
        "environment_artifact_sha256": sha256(ENVIRONMENT_JSON),
        "development_cv_sha256": sha256(CV_RESULTS_CSV),
        "development_choice_sha256": sha256(DEVELOPMENT_CHOICE_JSON),
    }
    if CONFIG_JSON.exists():
        existing = json.loads(CONFIG_JSON.read_text())
        stable_keys = [
            "feature_map_config", "feature_map", "reps", "entanglement", "classifier_C",
            "clinical_signatures", "pca_components", "preprocessing", "selection_rule",
            "split_artifact_sha256", "development_cv_sha256", "development_choice_sha256",
        ]
        if any(existing.get(key) != payload.get(key) for key in stable_keys):
            raise RuntimeError("Existing frozen quantum configuration differs from current development evidence")
        return existing
    if LOCKED_JSON.exists():
        raise RuntimeError("A locked evaluation exists without a frozen configuration; refusing to proceed")
    write_json(CONFIG_JSON, payload)
    return payload


def _fit_qsvc_final(
    development: pd.DataFrame,
    locked: pd.DataFrame,
    *,
    representation: str,
    budget: int,
    config_name: str,
    seed: int,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    train_matrix, test_matrix, audit, pca_meta = prepare_fold(
        development, locked, representation=representation, budget=budget, seed=seed
    )
    result = evaluate_qsvc(
        train_matrix,
        development[TARGET].to_numpy(dtype=int),
        test_matrix,
        locked[TARGET].to_numpy(dtype=int),
        config_name=config_name,
        seed=seed,
    )
    predictions = np.asarray(result.pop("prediction"), dtype=int)
    scores = np.asarray(result.pop("score"), dtype=float)
    result.pop("gate_counts", None)
    result["bootstrap_intervals"] = bootstrap_metric_intervals(
        locked[TARGET].to_numpy(dtype=int), predictions, scores, seed=seed, n_bootstrap=2000
    )
    result["representation"] = representation
    result["budget"] = budget
    result["preprocessing_fit_n"] = len(audit["preprocessor_fit_row_ids"])
    result.update(pca_meta)
    return result, predictions, scores


def evaluate_locked_once() -> tuple[dict[str, Any], pd.DataFrame]:
    if LOCKED_JSON.exists():
        return json.loads(LOCKED_JSON.read_text()), pd.read_csv(LOCKED_PREDICTIONS)
    config = freeze_configuration()
    config_hash_before = sha256(CONFIG_JSON)
    split = json.loads(SPLITS_JSON.read_text())
    if sha256(SPLITS_JSON) != config["split_artifact_sha256"]:
        raise RuntimeError("Frozen split changed after the quantum configuration was frozen")
    frame = load_frame()
    development = frame.loc[split["development_row_ids"]].copy()
    locked = frame.loc[split["locked_test_row_ids"]].copy()
    if len(locked) != 80:
        raise RuntimeError("Expected the frozen 80-patient shared test")

    phase1_eval = json.loads(PHASE1_LOCKED.read_text())
    phase1_predictions = pd.read_csv(PHASE1_PREDICTIONS, dtype={"row_id": str}).set_index("row_id")
    if set(phase1_predictions.index) != set(locked.index):
        raise RuntimeError("Phase 1 locked predictions do not match the frozen shared-test IDs")

    evaluation: dict[str, Any] = {
        "evaluated_on": date.today().isoformat(),
        "policy": "QSVC configurations were frozen from development-only evidence and evaluated once on the shared Phase 1 holdout.",
        "shared_test_disclosure": config["shared_test_disclosure"],
        "test_n": len(locked),
        "target_distribution": {
            "not_ckd": int((locked[TARGET] == 0).sum()),
            "ckd": int((locked[TARGET] == 1).sum()),
        },
        "frozen_config_sha256": config_hash_before,
        "models": {},
    }
    output = pd.DataFrame({"row_id": locked.index, "target": locked[TARGET].to_numpy(dtype=int)})

    for budget in (8, 6):
        classical_name = f"selected_{budget}"
        classical = phase1_eval["models"][classical_name]
        evaluation["models"][f"classical_{budget}_clinical"] = {
            "source": "reused Phase 1 one-time locked evaluation; not re-evaluated",
            "model": "classical_rbf_svm",
            "representation": "clinical",
            "budget": budget,
            "features": CLINICAL_SIGNATURES[budget],
            "metrics": classical["metrics"],
            "bootstrap_intervals": classical["bootstrap_intervals"],
        }
        output[f"classical_{budget}_prediction"] = phase1_predictions.loc[locked.index, f"{classical_name}_prediction"].to_numpy()
        output[f"classical_{budget}_score"] = phase1_predictions.loc[locked.index, f"{classical_name}_score"].to_numpy()
        result, predictions, scores = _fit_qsvc_final(
            development,
            locked,
            representation="clinical",
            budget=budget,
            config_name=config["feature_map_config"],
            seed=EXPERIMENT_SEED + budget,
        )
        intervals = result.pop("bootstrap_intervals")
        evaluation["models"][f"qsvc_{budget}_clinical"] = {
            "model": "qsvc",
            "feature_map_config": config["feature_map_config"],
            "features": CLINICAL_SIGNATURES[budget],
            "metrics": {key: result[key] for key in METRICS + ("tn", "fp", "fn", "tp")},
            "bootstrap_intervals": intervals,
            "resources": {key: value for key, value in result.items() if key not in METRICS + ("tn", "fp", "fn", "tp")},
        }
        output[f"qsvc_{budget}_prediction"] = predictions
        output[f"qsvc_{budget}_score"] = scores

    pca_classical = phase1_eval["models"]["best_pca_control"]
    evaluation["models"]["classical_6_pca"] = {
        "source": "reused Phase 1 one-time locked evaluation; not re-evaluated",
        "model": pca_classical["model"],
        "representation": "pca",
        "budget": 6,
        "metrics": pca_classical["metrics"],
        "bootstrap_intervals": pca_classical["bootstrap_intervals"],
    }
    output["classical_6_pca_prediction"] = phase1_predictions.loc[locked.index, "best_pca_control_prediction"].to_numpy()
    output["classical_6_pca_score"] = phase1_predictions.loc[locked.index, "best_pca_control_score"].to_numpy()
    result, predictions, scores = _fit_qsvc_final(
        development,
        locked,
        representation="pca",
        budget=6,
        config_name=config["feature_map_config"],
        seed=EXPERIMENT_SEED + 600,
    )
    intervals = result.pop("bootstrap_intervals")
    evaluation["models"]["qsvc_6_pca"] = {
        "model": "qsvc",
        "feature_map_config": config["feature_map_config"],
        "metrics": {key: result[key] for key in METRICS + ("tn", "fp", "fn", "tp")},
        "bootstrap_intervals": intervals,
        "resources": {key: value for key, value in result.items() if key not in METRICS + ("tn", "fp", "fn", "tp")},
    }
    output["qsvc_6_pca_prediction"] = predictions
    output["qsvc_6_pca_score"] = scores

    if sha256(CONFIG_JSON) != config_hash_before:
        raise RuntimeError("Frozen quantum configuration changed during locked evaluation")
    output.to_csv(LOCKED_PREDICTIONS, index=False)
    write_json(LOCKED_JSON, evaluation)
    return evaluation, output


def _metric_row(summary: pd.DataFrame, representation: str, budget: int, model: str, config: str) -> pd.Series:
    matches = summary[
        (summary["representation"] == representation)
        & (summary["budget"] == budget)
        & (summary["model"] == model)
        & (summary["feature_map_config"] == config)
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one summary row for {representation}/{budget}/{model}/{config}")
    return matches.iloc[0]


def build_resource_comparison(summary: pd.DataFrame, best_config: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in summary.iterrows():
        classical = _metric_row(summary, row["representation"], int(row["budget"]), "classical_rbf_svm", "rbf")
        runtime_ratio = float(row["training_wall_seconds_mean"] / max(classical["training_wall_seconds_mean"], 1e-12))
        is_quantum = row["model"] == "qsvc"
        rows.append(
            {
                "representation": row["representation"],
                "budget": int(row["budget"]),
                "model": row["model"],
                "feature_map_config": row["feature_map_config"],
                "qubits": int(row.get("qubit_count", 0)),
                "circuit_depth": int(row.get("circuit_depth", 0)),
                "feature_map_reps": int(row.get("reps", 0)),
                "kernel_backend": row.get("kernel_backend", ""),
                "execution_mode": row.get("execution_mode", ""),
                "training_wall_seconds_mean": float(row["training_wall_seconds_mean"]),
                "prediction_wall_seconds_mean": float(row["prediction_wall_seconds_mean"]),
                "kernel_construction_wall_seconds_mean": float(row["train_kernel_seconds_mean"]),
                "model_fit_seconds_mean": float(row["model_fit_seconds_mean"]),
                "kernel_matrix_rows_mean": 256 if is_quantum else 0,
                "kernel_matrix_columns_mean": 256 if is_quantum else 0,
                "inference_kernel_rows_mean": 64 if is_quantum else 0,
                "inference_kernel_columns_mean": 256 if is_quantum else 0,
                "kernel_evaluations_train_mean": float(row["kernel_evaluations_train_mean"]),
                "kernel_evaluations_inference_mean": float(row["kernel_evaluations_inference_mean"]),
                "runtime_ratio_vs_classical": runtime_ratio,
                "is_frozen_qsvc": bool(row["model"] == "qsvc" and row["feature_map_config"] == best_config),
            }
        )
    return pd.DataFrame(rows)


def build_utility_table(
    summary: pd.DataFrame,
    paired: pd.DataFrame,
    training_size: pd.DataFrame,
    shots: pd.DataFrame,
    noise: pd.DataFrame,
    best_config: str,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    small = training_size[training_size["training_fraction"] <= 0.50]
    small_pivot = small.groupby(["training_fraction", "model"])[["sensitivity", "roc_auc"]].mean().unstack("model")
    small_sens_delta = float(
        (small_pivot["sensitivity"]["qsvc"] - small_pivot["sensitivity"]["classical_rbf_svm"]).mean()
    )
    small_auc_delta = float(
        (small_pivot["roc_auc"]["qsvc"] - small_pivot["roc_auc"]["classical_rbf_svm"]).mean()
    )
    ideal_shot = shots[shots["mode"] == "ideal_qsvc"].iloc[0]
    finite = shots[shots["mode"] == "finite_shot_qsvc"]
    finite_sensitivity_delta = float(finite["sensitivity"].mean() - ideal_shot["sensitivity"])
    moderate = noise[noise["condition"] == "moderate"]
    noise_sensitivity_delta = float(moderate["sensitivity_delta_vs_ideal_mean"].mean())
    noise_f1_delta = float(moderate["f1_delta_vs_ideal_mean"].mean())

    for representation in ("clinical", "pca"):
        for budget in (8, 6, 4):
            classical = _metric_row(summary, representation, budget, "classical_rbf_svm", "rbf")
            quantum = _metric_row(summary, representation, budget, "qsvc", best_config)
            deltas = {
                metric: float(quantum[f"{metric}_mean"] - classical[f"{metric}_mean"])
                for metric in ("sensitivity", "specificity", "roc_auc", "f1")
            }
            primary_deltas = list(deltas.values())
            paired_rows = paired[(paired["representation"] == representation) & (paired["budget"] == budget)]
            predictive_supported = any(
                row["bootstrap_ci95_low"] > 0 for _, row in paired_rows.iterrows()
            )
            if predictive_supported:
                predictive_label = "SUPPORTED"
            elif min(primary_deltas) < -TOLERANCE:
                predictive_label = "NOT SUPPORTED"
            else:
                predictive_label = "NEUTRAL"

            if representation == "clinical":
                q8 = _metric_row(summary, "clinical", 8, "qsvc", best_config)
                budget_drop = float(quantum["sensitivity_mean"] - q8["sensitivity_mean"])
                feature_label = "SUPPORTED" if budget < 8 and budget_drop >= -TOLERANCE else ("NEUTRAL" if budget == 8 else "NOT SUPPORTED")
            else:
                budget_drop = np.nan
                feature_label = "INCONCLUSIVE"
            runtime_ratio = float(
                quantum["training_wall_seconds_mean"] / max(classical["training_wall_seconds_mean"], 1e-12)
            )
            rows.append(
                {
                    "representation": representation,
                    "budget": budget,
                    "sensitivity_delta_vs_classical": deltas["sensitivity"],
                    "specificity_delta_vs_classical": deltas["specificity"],
                    "roc_auc_delta_vs_classical": deltas["roc_auc"],
                    "f1_delta_vs_classical": deltas["f1"],
                    "input_dimensions": budget,
                    "qubits": int(quantum["qubit_count"]),
                    "circuit_depth": int(quantum["circuit_depth"]),
                    "runtime_ratio_vs_classical": runtime_ratio,
                    "finite_shot_sensitivity_delta": finite_sensitivity_delta if (representation, budget) == ("clinical", 6) else np.nan,
                    "moderate_noise_sensitivity_delta": noise_sensitivity_delta if (representation, budget) == ("clinical", 6) else np.nan,
                    "moderate_noise_f1_delta": noise_f1_delta if (representation, budget) == ("clinical", 6) else np.nan,
                    "qsvc_sensitivity_cv_std": float(quantum["sensitivity_std"]),
                    "training_size_25_50_sensitivity_delta": small_sens_delta if (representation, budget) == ("clinical", 8) else np.nan,
                    "training_size_25_50_roc_auc_delta": small_auc_delta if (representation, budget) == ("clinical", 8) else np.nan,
                    "predictive_utility": predictive_label,
                    "feature_budget_utility": feature_label,
                    "small_sample_utility": (
                        "SUPPORTED" if small_sens_delta > 0 and small_auc_delta > 0
                        else "NOT SUPPORTED" if small_sens_delta < -TOLERANCE or small_auc_delta < -TOLERANCE
                        else "NEUTRAL"
                    ) if (representation, budget) == ("clinical", 8) else "INCONCLUSIVE",
                    "runtime_utility": "SUPPORTED" if runtime_ratio < 1 else "NOT SUPPORTED",
                    "noise_robustness": (
                        "SUPPORTED" if min(noise_sensitivity_delta, noise_f1_delta) >= -TOLERANCE
                        else "NOT SUPPORTED"
                    ) if (representation, budget) == ("clinical", 6) else "INCONCLUSIVE",
                    "meets_0_05_tolerance": bool(min(primary_deltas) >= -TOLERANCE),
                }
            )
    return pd.DataFrame(rows)


def write_kernel_report(diagnostics: pd.DataFrame, best_config: str) -> None:
    rows = []
    for _, row in diagnostics.sort_values(["representation", "budget", "feature_map_config"]).iterrows():
        rows.append(
            [
                row["representation"], int(row["budget"]), row["feature_map_config"],
                f"{int(row['kernel_rows'])}×{int(row['kernel_columns'])}",
                fmt(row["diagonal_mean"]), fmt(row["off_diagonal_mean"]),
                fmt(row["within_ckd_similarity"]), fmt(row["within_not_ckd_similarity"]),
                fmt(row["between_class_similarity"]), fmt(row["kernel_target_alignment"]),
                f"{row['condition_number_positive_spectrum']:.2e}", int(row["effective_rank"]),
            ]
        )
    best = diagnostics[
        (diagnostics["representation"] == "clinical")
        & (diagnostics["budget"] == 8)
        & (diagnostics["feature_map_config"] == best_config)
    ].iloc[0]
    separation = float(
        min(best["within_ckd_similarity"], best["within_not_ckd_similarity"])
        - best["between_class_similarity"]
    )
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "kernel_diagnostics.md").write_text(
        "# Quantum-kernel diagnostics\n\n"
        "Diagnostics use a fixed, stratified 80-patient sample from development data only. "
        "Kernels are exact statevector fidelities; the reported positive-spectrum condition number excludes eigenvalues ≤1e-10.\n\n"
        + markdown_table(
            ["Representation", "Budget", "Map", "Shape", "Diag mean", "Offdiag mean", "Within CKD", "Within non-CKD", "Between", "Centered KTA", "Condition", "Rank"],
            rows,
        )
        + "\n\n"
        f"For the frozen `{best_config}` eight-clinical-variable kernel, the weaker within-class minus between-class similarity gap is {separation:+.3f}. "
        f"Centered kernel-target alignment is {best['kernel_target_alignment']:.3f}. The matrix has effective rank {int(best['effective_rank'])}/{int(best['kernel_rows'])} and positive-spectrum condition number {best['condition_number_positive_spectrum']:.2e}. "
        "These diagnostics describe separability and numerical structure; they do not establish quantum advantage.\n"
    )


def write_resource_report(resources: pd.DataFrame) -> None:
    resources.to_csv(REPORT_DIR / "resource_comparison.csv", index=False)
    rows = []
    for _, row in resources.sort_values(["representation", "budget", "model", "feature_map_config"]).iterrows():
        rows.append(
            [
                row["representation"], int(row["budget"]), row["model"], row["feature_map_config"],
                int(row["qubits"]), int(row["circuit_depth"]), int(row["feature_map_reps"]),
                (f"{int(row['kernel_matrix_rows_mean'])}×{int(row['kernel_matrix_columns_mean'])}" if row["model"] == "qsvc" else "NR"),
                (f"{int(row['inference_kernel_rows_mean'])}×{int(row['inference_kernel_columns_mean'])}" if row["model"] == "qsvc" else "NR"),
                fmt(row["training_wall_seconds_mean"], 4), fmt(row["prediction_wall_seconds_mean"], 4),
                fmt(row["kernel_construction_wall_seconds_mean"], 4),
                int(round(row["kernel_evaluations_train_mean"])),
                int(round(row["kernel_evaluations_inference_mean"])),
                fmt(row["runtime_ratio_vs_classical"], 1),
            ]
        )
    (REPORT_DIR / "resource_comparison.md").write_text(
        "# Classical and quantum resource comparison\n\n"
        "Wall times were measured locally and include no cloud queue time. QSVC training wall time includes quantum-kernel construction; model-fit time after kernel construction is retained in the CSV. "
        "Ideal CV used exact cached statevectors. Aer finite-shot/noise timings are reported separately in the Phase 2 results.\n\n"
        + markdown_table(
            ["Representation", "Budget", "Model", "Map", "Qubits", "Depth", "Reps", "Train K shape", "Infer K shape", "Train s", "Predict s", "Kernel s", "Train evals", "Infer evals", "Train ratio"],
            rows,
        )
        + "\n"
    )


def write_utility_report(utility: pd.DataFrame) -> None:
    rows = []
    for _, row in utility.sort_values(["representation", "budget"], ascending=[True, False]).iterrows():
        rows.append(
            [
                row["representation"], int(row["budget"]), fmt(row["sensitivity_delta_vs_classical"]),
                fmt(row["specificity_delta_vs_classical"]), fmt(row["roc_auc_delta_vs_classical"]),
                fmt(row["f1_delta_vs_classical"]), int(row["qubits"]), int(row["circuit_depth"]),
                fmt(row["runtime_ratio_vs_classical"], 1), row["predictive_utility"],
                row["feature_budget_utility"], row["small_sample_utility"],
                row["runtime_utility"], row["noise_robustness"],
            ]
        )
    (REPORT_DIR / "utility_evidence.md").write_text(
        "# Transparent quantum-utility evidence\n\n"
        "No weighted composite score is calculated. Labels follow disclosed rules: predictive utility is SUPPORTED only when a paired bootstrap interval is wholly positive, NOT SUPPORTED when any primary mean degradation exceeds 0.05, and otherwise NEUTRAL. Runtime is SUPPORTED only below parity. Unmeasured representation-specific robustness is INCONCLUSIVE.\n\n"
        + markdown_table(
            ["Representation", "Budget", "Δ sens", "Δ spec", "Δ AUC", "Δ F1", "Qubits", "Depth", "Runtime ×", "Predictive", "Feature budget", "Small sample", "Runtime", "Noise"],
            rows,
        )
        + "\n\nA single Quantum Utility Score is not justified: the evidence dimensions have different meanings, scales and uncertainty, and weighting them would conceal rather than clarify trade-offs.\n"
    )


def generate_figures(
    summary: pd.DataFrame,
    paired_folds: pd.DataFrame,
    training_size: pd.DataFrame,
    shots: pd.DataFrame,
    noise: pd.DataFrame,
    utility: pd.DataFrame,
    best_config: str,
) -> None:
    clinical = summary[(summary["representation"] == "clinical")]
    frozen = clinical[
        ((clinical["model"] == "classical_rbf_svm") & (clinical["feature_map_config"] == "rbf"))
        | ((clinical["model"] == "qsvc") & (clinical["feature_map_config"] == best_config))
    ].copy()
    frozen["label"] = frozen["model"].map({"classical_rbf_svm": "Classical RBF SVM", "qsvc": "QSVC"})
    for metric, filename, title in [
        ("sensitivity_mean", "01_classical_vs_qsvc_sensitivity.png", "Classical vs QSVC sensitivity"),
        ("roc_auc_mean", "02_classical_vs_qsvc_roc_auc.png", "Classical vs QSVC ROC-AUC"),
    ]:
        fig, ax = plt.subplots(figsize=(7.2, 4.7))
        for label, group in frozen.groupby("label"):
            group = group.sort_values("budget")
            ax.plot(group["budget"], group[metric], marker="o", linewidth=2, label=label)
        ax.set(xticks=[4, 6, 8], xlabel="Clinical-variable budget", ylabel=metric.replace("_mean", "").replace("_", " ").title(), title=title)
        ax.set_ylim(max(0.0, frozen[metric].min() - 0.08), 1.015)
        ax.legend()
        save_figure(fig, filename)

    compare = summary[
        ((summary["model"] == "classical_rbf_svm") & (summary["feature_map_config"] == "rbf"))
        | ((summary["model"] == "qsvc") & (summary["feature_map_config"] == best_config))
    ].copy()
    fig, ax = plt.subplots(figsize=(8, 5))
    styles = {("clinical", "classical_rbf_svm"): "o-", ("clinical", "qsvc"): "s-", ("pca", "classical_rbf_svm"): "o--", ("pca", "qsvc"): "s--"}
    for (representation, model), group in compare.groupby(["representation", "model"]):
        group = group.sort_values("budget")
        ax.plot(group["budget"], group["sensitivity_mean"], styles[(representation, model)], label=f"{representation} / {model.replace('_', ' ')}")
    ax.set(xticks=[4, 6, 8], xlabel="Input dimension", ylabel="Mean sensitivity", title="Selected clinical variables vs fold-fitted PCA")
    ax.legend(fontsize=8)
    save_figure(fig, "03_selected_vs_pca.png")

    fig, ax = plt.subplots(figsize=(7.2, 4.7))
    for label, group in frozen.groupby("label"):
        group = group.sort_values("budget")
        ax.plot(group["budget"], group["training_wall_seconds_mean"], marker="o", label=label)
    ax.set(yscale="log", xticks=[4, 6, 8], xlabel="Features / qubits", ylabel="Mean training wall time (s, log scale)", title="Runtime vs feature/qubit count")
    ax.legend()
    save_figure(fig, "04_runtime_vs_feature_count.png")

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for config in FEATURE_MAP_CONFIGS:
        values = [circuit_resources(config, budget)["circuit_depth"] for budget in (4, 6, 8)]
        ax.plot((4, 6, 8), values, marker="o", label=config)
    ax.set(xticks=[4, 6, 8], xlabel="Qubits / feature count", ylabel="Logical circuit depth", title="Feature-map depth vs qubit count")
    ax.legend()
    save_figure(fig, "05_circuit_depth_vs_feature_count.png")

    kernel_payload = np.load(KERNEL_DIR / f"clinical_8_{best_config}.npz")
    matrix = kernel_payload["kernel"]
    labels = kernel_payload["target"]
    order = np.argsort(labels)
    ordered = matrix[np.ix_(order, order)]
    fig, ax = plt.subplots(figsize=(6.2, 5.4))
    image = ax.imshow(ordered, cmap="viridis", vmin=0, vmax=1, aspect="auto")
    ax.axhline(int(np.sum(labels == 0)) - 0.5, color="white", linewidth=1)
    ax.axvline(int(np.sum(labels == 0)) - 0.5, color="white", linewidth=1)
    ax.set(title=f"Eight-variable {best_config} kernel", xlabel="Development sample (class ordered)", ylabel="Development sample (class ordered)")
    fig.colorbar(image, ax=ax, label="Fidelity")
    save_figure(fig, "06_kernel_heatmap.png")

    within = []
    between = []
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            (within if labels[i] == labels[j] else between).append(matrix[i, j])
    fig, ax = plt.subplots(figsize=(7.2, 4.7))
    ax.hist(within, bins=30, alpha=0.65, density=True, label="Within class")
    ax.hist(between, bins=30, alpha=0.65, density=True, label="Between class")
    ax.set(xlabel="Off-diagonal quantum-kernel similarity", ylabel="Density", title="Kernel similarity distribution")
    ax.legend()
    save_figure(fig, "07_kernel_similarity_distribution.png")

    size_summary = training_size.groupby(["training_fraction", "model"])[["sensitivity", "roc_auc"]].agg(["mean", "std"])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharex=True)
    for model, label in (("classical_rbf_svm", "Classical RBF SVM"), ("qsvc", "QSVC")):
        group = training_size[training_size["model"] == model].groupby("training_fraction")
        for ax, metric in zip(axes, ("sensitivity", "roc_auc"), strict=True):
            means = group[metric].mean()
            stds = group[metric].std().fillna(0)
            ax.errorbar(means.index * 100, means, yerr=stds, marker="o", capsize=3, label=label)
            ax.set(xlabel="Training-pool fraction (%)", ylabel=metric.replace("_", " ").title(), title=metric.replace("_", " ").title())
    axes[0].legend()
    fig.suptitle("Development-only training-size robustness")
    save_figure(fig, "08_performance_vs_training_size.png")

    finite = shots[shots["mode"].isin(["ideal_qsvc", "finite_shot_qsvc"])].copy()
    finite["shot_label"] = finite["shots"].replace({0: 1})
    shot_summary = finite.groupby("shots")[["sensitivity", "specificity", "f1"]].agg(["mean", "std"])
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    for metric in ("sensitivity", "specificity", "f1"):
        means = shot_summary[(metric, "mean")]
        stds = shot_summary[(metric, "std")].fillna(0)
        x = [128 if value == 0 else value for value in means.index]
        ax.errorbar(x, means, yerr=stds, marker="o", capsize=3, label=metric)
    ax.set(xscale="log", xticks=[128, 256, 1024, 4096], xticklabels=["ideal", "256", "1024", "4096"], xlabel="Shots", ylabel="Metric", title="Six-variable finite-shot robustness")
    ax.legend()
    save_figure(fig, "09_performance_vs_shots.png")

    noise_order = ["ideal", "low", "moderate"]
    noise_summary = noise.groupby("condition")[["sensitivity", "specificity", "f1", "roc_auc"]].mean().reindex(noise_order)
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    for metric in noise_summary.columns:
        ax.plot(noise_order, noise_summary[metric], marker="o", label=metric)
    ax.set(xlabel="Aer noise condition", ylabel="Mean metric", title="Six-variable noise degradation")
    ax.legend()
    save_figure(fig, "10_noise_degradation.png")

    plot_deltas = paired_folds[(paired_folds["representation"] == "clinical") & (paired_folds["budget"].isin([8, 6, 4]))]
    fig, ax = plt.subplots(figsize=(9, 5))
    positions, labels_out, values = [], [], []
    position = 1
    for budget in (8, 6, 4):
        for metric in ("sensitivity", "specificity", "roc_auc", "f1"):
            subset = plot_deltas[(plot_deltas["budget"] == budget) & (plot_deltas["metric"] == metric)]["delta_qsvc_minus_classical"]
            positions.append(position); labels_out.append(f"{budget}\n{metric[:4]}"); values.append(subset.to_numpy()); position += 1
        position += 0.7
    ax.boxplot(values, positions=positions, widths=0.6, showmeans=True)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axhline(-TOLERANCE, color="firebrick", linestyle="--", linewidth=1, label="−0.05 tolerance")
    ax.set_xticks(positions, labels_out, fontsize=8)
    ax.set(ylabel="Paired fold delta (QSVC − classical)", title="Paired clinical-fold deltas")
    ax.legend()
    save_figure(fig, "11_paired_fold_deltas.png")

    evidence_columns = ["predictive_utility", "feature_budget_utility", "small_sample_utility", "runtime_utility", "noise_robustness"]
    label_to_value = {"NOT SUPPORTED": 0, "INCONCLUSIVE": 1, "NEUTRAL": 2, "SUPPORTED": 3}
    matrix_values = np.array([[label_to_value[row[column]] for column in evidence_columns] for _, row in utility.iterrows()])
    fig, ax = plt.subplots(figsize=(9, 5.2))
    image = ax.imshow(matrix_values, cmap=matplotlib.colors.ListedColormap(["#b94a48", "#bdbdbd", "#4c78a8", "#2a9d6f"]), vmin=-0.5, vmax=3.5, aspect="auto")
    for i, (_, row) in enumerate(utility.iterrows()):
        for j, column in enumerate(evidence_columns):
            ax.text(j, i, row[column].replace("NOT SUPPORTED", "NOT\nSUPPORTED"), ha="center", va="center", fontsize=7, color="white" if row[column] in {"SUPPORTED", "NOT SUPPORTED"} else "black")
    ax.set_xticks(range(len(evidence_columns)), [value.replace("_", " ").title() for value in evidence_columns], rotation=20, ha="right")
    ax.set_yticks(range(len(utility)), [f"{row.representation} {int(row.budget)}" for _, row in utility.iterrows()])
    ax.set(title="Quantum utility evidence matrix")
    save_figure(fig, "12_quantum_utility_evidence_matrix.png")


def write_phase2_reports(evaluation: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(CV_SUMMARY_CSV)
    results = pd.read_csv(CV_RESULTS_CSV)
    diagnostics = pd.read_csv(DIAGNOSTICS_CSV)
    paired_folds = pd.read_csv(PAIRED_CSV)
    paired = pd.read_csv(PAIRED_SUMMARY_CSV)
    training_size = pd.read_csv(TRAINING_SIZE_CSV)
    shots = pd.read_csv(SHOTS_CSV)
    noise = pd.read_csv(NOISE_CSV)
    config = json.loads(CONFIG_JSON.read_text())
    best_config = config["feature_map_config"]

    resources = build_resource_comparison(summary, best_config)
    utility = build_utility_table(summary, paired, training_size, shots, noise, best_config)
    write_resource_report(resources)
    write_kernel_report(diagnostics, best_config)
    write_utility_report(utility)
    generate_figures(summary, paired_folds, training_size, shots, noise, utility, best_config)

    comparison_rows: list[list[Any]] = []
    for representation in ("clinical", "pca"):
        for budget in (8, 6, 4):
            classical = _metric_row(summary, representation, budget, "classical_rbf_svm", "rbf")
            quantum = _metric_row(summary, representation, budget, "qsvc", best_config)
            comparison_rows.append(
                [
                    representation, budget,
                    fmt(classical["sensitivity_mean"]), fmt(quantum["sensitivity_mean"]), fmt(quantum["sensitivity_mean"] - classical["sensitivity_mean"]),
                    fmt(classical["specificity_mean"]), fmt(quantum["specificity_mean"]),
                    fmt(classical["roc_auc_mean"]), fmt(quantum["roc_auc_mean"]), fmt(quantum["roc_auc_mean"] - classical["roc_auc_mean"]),
                    fmt(classical["f1_mean"]), fmt(quantum["f1_mean"]),
                    bool(utility[(utility["representation"] == representation) & (utility["budget"] == budget)]["meets_0_05_tolerance"].iloc[0]),
                ]
            )
    map_rows = []
    for config_name in FEATURE_MAP_CONFIGS:
        row = _metric_row(summary, "clinical", 8, "qsvc", config_name)
        map_rows.append([config_name, int(row["qubit_count"]), int(row["circuit_depth"]), int(row["gate_count"]), fmt(row["sensitivity_mean"]), fmt(row["specificity_mean"]), fmt(row["roc_auc_mean"]), fmt(row["f1_mean"]), fmt(row["training_wall_seconds_mean"], 4)])

    training_rows = []
    grouped_size = training_size.groupby(["training_fraction", "model"])
    for (fraction, model), group in grouped_size:
        training_rows.append([f"{fraction:.0%}", model, int(round(group["training_n"].mean())), fmt(group["sensitivity"].mean()), fmt(group["sensitivity"].std()), fmt(group["roc_auc"].mean()), fmt(group["roc_auc"].std()), fmt(group["training_wall_seconds"].mean(), 4)])
    shot_rows = []
    for (mode, shot_count), group in shots.groupby(["mode", "shots"]):
        shot_rows.append([mode, "ideal" if shot_count == 0 else int(shot_count), len(group), fmt(group["sensitivity"].mean()), fmt(group["sensitivity"].std()), fmt(group["specificity"].mean()), fmt(group["f1"].mean()), fmt(group["roc_auc"].mean()), fmt(group["training_wall_seconds"].mean(), 4)])
    noise_rows = []
    for condition, group in noise.groupby("condition"):
        noise_rows.append([condition, int(group["shots"].iloc[0]), fmt(group["sensitivity"].mean()), fmt(group["specificity"].mean()), fmt(group["accuracy"].mean()), fmt(group["f1"].mean()), fmt(group["roc_auc"].mean()), fmt(group["sensitivity_delta_vs_ideal_mean"].mean()), fmt(group["training_wall_seconds"].mean(), 3)])
    locked_rows = []
    for name, model in evaluation["models"].items():
        metrics = model["metrics"]
        representation = model.get("representation", model.get("resources", {}).get("representation", "NR"))
        budget = model.get("budget", model.get("resources", {}).get("budget", "NR"))
        locked_rows.append([name, model["model"], representation, budget, fmt(metrics["accuracy"]), fmt(metrics["sensitivity"]), fmt(metrics["specificity"]), fmt(metrics["f1"]), fmt(metrics["roc_auc"]), f"TN={metrics['tn']}, FP={metrics['fp']}, FN={metrics['fn']}, TP={metrics['tp']}"])

    (PROJECT_ROOT / "research/phase2_results.md").write_text(
        "# Phase 2 fair quantum benchmark results\n\n"
        "All architecture choice, robustness analysis and PCA fitting used development data only. The fixed 0.05 margin is an experimental tolerance, not a formal clinical non-inferiority threshold. No quantum-advantage claim is made.\n\n"
        f"## Frozen model\n\nQSVC used `FidelityQuantumKernel`, `{best_config}`, C={CLASSIFIER_C}, exact cached statevector fidelity for ideal development runs, and the Phase 1 preprocessing fitted within each training fold.\n\n"
        "## Predefined feature-map screen on eight clinical variables\n\n"
        + markdown_table(["Map", "Qubits", "Depth", "Gates", "Sensitivity", "Specificity", "ROC-AUC", "F1", "Train s"], map_rows)
        + "\n\n## Identical-fold classical versus frozen QSVC comparison\n\n"
        + markdown_table(["Representation", "Budget", "Classical sens", "QSVC sens", "Δ sens", "Classical spec", "QSVC spec", "Classical AUC", "QSVC AUC", "Δ AUC", "Classical F1", "QSVC F1", "All primary deltas ≥−0.05"], comparison_rows)
        + "\n\nPaired fold-level bootstrap intervals and Wilcoxon tests are in `artifacts/quantum_paired_comparison_summary.csv`. P-values are descriptive because ten repeated-CV assessments are neither a large sample nor independent patient cohorts.\n\n"
        "## Development-only training-size robustness\n\n"
        + markdown_table(["Train fraction", "Model", "Train n", "Sensitivity mean", "Sensitivity SD", "ROC-AUC mean", "ROC-AUC SD", "Train s"], training_rows)
        + "\n\n## Finite-shot experiment (six clinical variables)\n\n"
        + markdown_table(["Mode", "Shots", "Runs", "Sensitivity", "Sensitivity SD", "Specificity", "F1", "ROC-AUC", "Train s"], shot_rows)
        + "\n\nFinite-shot values use seeded binomial sampling of the exact compute-uncompute all-zero probability; a stock Qiskit path is checked in tests. This isolates shot noise without conflating it with gate noise.\n\n"
        "## Aer noise experiment (six clinical variables)\n\n"
        + markdown_table(["Condition", "Shots", "Sensitivity", "Specificity", "Accuracy", "F1", "ROC-AUC", "Δ sensitivity", "Train s"], noise_rows)
        + "\n\nLow and moderate conditions are synthetic device-inspired Aer models, not calibration snapshots from a named IBM device. They apply 1q/2q depolarizing and symmetric readout errors recorded in `artifacts/quantum_config.json`.\n\n"
        "## Shared locked-test evaluation\n\n"
        + evaluation["shared_test_disclosure"] + "\n\n"
        + markdown_table(["Configuration", "Model", "Representation", "Budget", "Accuracy", "Sensitivity", "Specificity", "F1", "ROC-AUC", "Confusion"], locked_rows)
        + "\n\nBootstrap intervals (2,000 class-stratified resamples) are stored in the machine-readable evaluation artifact. No quantum configuration was changed after these results were observed.\n\n"
        "## Interpretation\n\n"
        "The comparison asks whether QSVC is competitive at equal dimension and what it costs. Near-ceiling classical performance leaves almost no room for a defensible predictive advantage claim. Kernel structure, runtime, finite-shot behavior and noise sensitivity therefore carry equal interpretive weight. This remains a small, single-site engineering benchmark rather than clinical validation.\n"
    )

    write_decision(summary, paired, training_size, shots, noise, diagnostics, resources, utility, evaluation, config)


def write_decision(
    summary: pd.DataFrame,
    paired: pd.DataFrame,
    training_size: pd.DataFrame,
    shots: pd.DataFrame,
    noise: pd.DataFrame,
    diagnostics: pd.DataFrame,
    resources: pd.DataFrame,
    utility: pd.DataFrame,
    evaluation: dict[str, Any],
    config: dict[str, Any],
) -> None:
    best = config["feature_map_config"]
    c8 = _metric_row(summary, "clinical", 8, "classical_rbf_svm", "rbf")
    q8 = _metric_row(summary, "clinical", 8, "qsvc", best)
    c6 = _metric_row(summary, "clinical", 6, "classical_rbf_svm", "rbf")
    q6 = _metric_row(summary, "clinical", 6, "qsvc", best)
    c4 = _metric_row(summary, "clinical", 4, "classical_rbf_svm", "rbf")
    q4 = _metric_row(summary, "clinical", 4, "qsvc", best)
    pca = {budget: _metric_row(summary, "pca", budget, "qsvc", best) for budget in (8, 6, 4)}
    tolerance8 = bool(utility[(utility["representation"] == "clinical") & (utility["budget"] == 8)]["meets_0_05_tolerance"].iloc[0])
    tolerance6 = bool(utility[(utility["representation"] == "clinical") & (utility["budget"] == 6)]["meets_0_05_tolerance"].iloc[0])
    ratio8 = float(q8["training_wall_seconds_mean"] / max(c8["training_wall_seconds_mean"], 1e-12))
    ratio6 = float(q6["training_wall_seconds_mean"] / max(c6["training_wall_seconds_mean"], 1e-12))
    res8 = circuit_resources(best, 8)
    res6 = circuit_resources(best, 6)
    small = training_size[training_size["training_fraction"] <= 0.50].groupby("model")[["sensitivity", "roc_auc"]].mean()
    small_sens_delta = float(small.loc["qsvc", "sensitivity"] - small.loc["classical_rbf_svm", "sensitivity"])
    small_auc_delta = float(small.loc["qsvc", "roc_auc"] - small.loc["classical_rbf_svm", "roc_auc"])
    ideal_shot = shots[shots["mode"] == "ideal_qsvc"].iloc[0]
    finite = shots[shots["mode"] == "finite_shot_qsvc"]
    finite_sens_delta = float(finite["sensitivity"].mean() - ideal_shot["sensitivity"])
    finite_f1_delta = float(finite["f1"].mean() - ideal_shot["f1"])
    moderate = noise[noise["condition"] == "moderate"]
    noise_sens_delta = float(moderate["sensitivity_delta_vs_ideal_mean"].mean())
    noise_f1_delta = float(moderate["f1_delta_vs_ideal_mean"].mean())
    diag = diagnostics[(diagnostics["representation"] == "clinical") & (diagnostics["budget"] == 8) & (diagnostics["feature_map_config"] == best)].iloc[0]
    positive = utility.sort_values("sensitivity_delta_vs_classical", ascending=False).iloc[0]
    negative = utility.sort_values("sensitivity_delta_vs_classical", ascending=True).iloc[0]
    claim_survives = tolerance8 and tolerance6
    locked_q8 = evaluation["models"]["qsvc_8_clinical"]["metrics"]
    locked_c8 = evaluation["models"]["classical_8_clinical"]["metrics"]
    locked_q6 = evaluation["models"]["qsvc_6_clinical"]["metrics"]
    locked_c6 = evaluation["models"]["classical_6_clinical"]["metrics"]
    headline = (
        "At fixed low-dimensional clinical inputs, an exact-simulator QSVC was tested as a transparent competitiveness-and-cost benchmark against a near-ceiling RBF SVM."
    )
    lines = [
        f"1. **Best QSVC configuration:** `{best}` with the frozen eight-variable clinical signature, C={CLASSIFIER_C}, exact statevector fidelity and full development-only repeated CV.",
        f"2. **Best feature-map configuration:** {config['feature_map']} with reps={config['reps']} and entanglement={config['entanglement']}; it first passed the joint 0.05 development tolerance across sensitivity, specificity, ROC-AUC and F1, then won the predefined lexicographic ranking.",
        f"3. **8-variable QSVC sensitivity:** {q8['sensitivity_mean']:.3f} in repeated development CV; shared-test sensitivity {locked_q8['sensitivity']:.3f}.",
        f"4. **8-variable classical sensitivity:** {c8['sensitivity_mean']:.3f} in identical-fold development CV; reused Phase 1 shared-test sensitivity {locked_c8['sensitivity']:.3f}.",
        f"5. **8-variable QSVC ROC-AUC:** {q8['roc_auc_mean']:.3f} in development CV; shared-test ROC-AUC {locked_q8['roc_auc']:.3f}.",
        f"6. **8-variable classical ROC-AUC:** {c8['roc_auc_mean']:.3f} in development CV; reused Phase 1 shared-test ROC-AUC {locked_c8['roc_auc']:.3f}.",
        f"7. **8-variable 0.05 tolerance:** {'met' if tolerance8 else 'not met'} across mean sensitivity, specificity, ROC-AUC and F1 deltas; this is an experimental tolerance, not clinical non-inferiority.",
        f"8. **6-variable answers:** QSVC sensitivity {q6['sensitivity_mean']:.3f} and ROC-AUC {q6['roc_auc_mean']:.3f}; classical sensitivity {c6['sensitivity_mean']:.3f} and ROC-AUC {c6['roc_auc_mean']:.3f}; tolerance {'met' if tolerance6 else 'not met'}; shared-test sensitivities QSVC/classical {locked_q6['sensitivity']:.3f}/{locked_c6['sensitivity']:.3f}.",
        f"9. **4-variable stress test:** QSVC sensitivity {q4['sensitivity_mean']:.3f}, specificity {q4['specificity_mean']:.3f}, ROC-AUC {q4['roc_auc_mean']:.3f}; classical sensitivity {c4['sensitivity_mean']:.3f}; this representation remains a stress test and is not promoted.",
        f"10. **Selected-feature vs PCA quantum result:** QSVC clinical/PCA sensitivity was {q8['sensitivity_mean']:.3f}/{pca[8]['sensitivity_mean']:.3f} at 8, {q6['sensitivity_mean']:.3f}/{pca[6]['sensitivity_mean']:.3f} at 6, and {q4['sensitivity_mean']:.3f}/{pca[4]['sensitivity_mean']:.3f} at 4 dimensions.",
        f"11. **Quantum vs classical runtime ratio:** mean training ratios were {ratio8:.1f}× at 8 clinical variables and {ratio6:.1f}× at 6; ideal local statevector acceleration and classical CPU timing make these machine-specific lower-bound simulator ratios.",
        f"12. **8-qubit vs 6-qubit resource difference:** depth {res8['circuit_depth']} vs {res6['circuit_depth']} ({res8['circuit_depth']-res6['circuit_depth']:+d}), gates {res8['gate_count']} vs {res6['gate_count']} ({res8['gate_count']-res6['gate_count']:+d}), and qubits 8 vs 6.",
        f"13. **Training-size robustness:** over the 25% and 50% development-training conditions, QSVC minus classical mean sensitivity was {small_sens_delta:+.3f} and ROC-AUC was {small_auc_delta:+.3f}; no small-sample advantage is inferred without external repetition.",
        f"14. **Finite-shot conclusion:** across 256/1024/4096 shots and three seeds, mean sensitivity/F1 deltas from ideal were {finite_sens_delta:+.3f}/{finite_f1_delta:+.3f}; shot count did not create a reliable predictive improvement.",
        f"15. **Noise conclusion:** under the synthetic moderate Aer condition, mean sensitivity/F1 degradation from the noiseless finite-shot reference was {noise_sens_delta:+.3f}/{noise_f1_delta:+.3f}; these are simulator robustness results, not hardware validation.",
        f"16. **Kernel diagnostic conclusion:** the frozen 8-variable kernel had centered alignment {diag['kernel_target_alignment']:.3f}, effective rank {int(diag['effective_rank'])}/{int(diag['kernel_rows'])}, positive-spectrum condition number {diag['condition_number_positive_spectrum']:.2e}, and between-class similarity {diag['between_class_similarity']:.3f}.",
        f"17. **Measurable QSVC benefit:** the most favorable mean sensitivity delta was {positive['sensitivity_delta_vs_classical']:+.3f} for {positive['representation']} at {int(positive['budget'])} dimensions; it is treated as {positive['predictive_utility']} rather than quantum advantage.",
        f"18. **Measurable QSVC disadvantage:** the least favorable sensitivity delta was {negative['sensitivity_delta_vs_classical']:+.3f} for {negative['representation']} at {int(negative['budget'])} dimensions, and every frozen QSVC representation had runtime utility labeled NOT SUPPORTED.",
        f"19. **Feature-efficient QML claim:** {'survives only as a competitiveness claim at the fixed 8/6 budgets' if claim_survives else 'does not survive the predefined 8/6 competitiveness tolerance'}; it does not support accuracy superiority or quantum advantage.",
        "20. **Quantum Utility Score:** not justified; predictive, dimensional, runtime, finite-shot and noise evidence should remain separate because any weighting would be arbitrary and cosmetic.",
        "21. **VQC decision:** **NO-GO** for this phase; the QSVC evidence does not identify a limitation that variational training would clearly resolve, while adding optimization variance and cost would not strengthen the central claim.",
        f"22. **Recommended hackathon headline:** {headline}",
        "23. **Claims we must NOT make:** quantum advantage, clinical non-inferiority, hardware readiness, diagnostic deployment readiness, causal biomarker discovery, external validity, or superiority derived from this single 400-row dataset.",
        "24. **Phase 3 recommendation:** proceed with an evidence-first comparison interface and external/shift validation planning using the frozen classical and QSVC artifacts; keep VQC out unless a separately preregistered scientific question emerges.",
    ]
    (PROJECT_ROOT / "research/phase2_decision.md").write_text("\n".join(lines) + "\n")


def finalize() -> None:
    freeze_configuration()
    evaluation, _ = evaluate_locked_once()
    write_phase2_reports(evaluation)
    print("PHASE 2 COMPLETE")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the guarded Phase 2 QSVC benchmark")
    parser.add_argument(
        "stage",
        choices=["environment", "develop", "training-size", "shots", "noise", "finalize", "all"],
        nargs="?",
        default="all",
    )
    args = parser.parse_args()
    if args.stage in {"environment", "all"}:
        environment_and_smoke_test()
    if args.stage in {"develop", "all"}:
        run_development()
    if args.stage in {"training-size", "all"}:
        run_training_size()
    if args.stage in {"shots", "all"}:
        run_finite_shots()
    if args.stage in {"noise", "all"}:
        run_noise()
    if args.stage in {"finalize", "all"}:
        finalize()


if __name__ == "__main__":
    main()
