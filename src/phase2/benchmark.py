from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd
from qiskit.circuit import QuantumCircuit
from qiskit.circuit.library import z_feature_map, zz_feature_map
from qiskit.providers import Options
from qiskit.quantum_info import Statevector
from qiskit_machine_learning.algorithm_job import AlgorithmJob
from qiskit_machine_learning.algorithms import QSVC
from qiskit_machine_learning.kernels import FidelityQuantumKernel
from qiskit_machine_learning.state_fidelities import BaseStateFidelity, StateFidelityResult
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.svm import SVC

from src.phase1.data import FEATURES, TARGET
from src.phase1.modeling import EXPERIMENT_SEED, OUTER_REPEATS, OUTER_SPLITS, binary_metrics, make_preprocessor


CLINICAL_SIGNATURES: dict[int, list[str]] = {
    8: ["hemo", "al", "dm", "sg", "pcv", "appet", "htn", "sc"],
    6: ["hemo", "al", "dm", "sg", "pcv", "appet"],
    4: ["hemo", "pcv", "rc", "sc"],
}

FEATURE_MAP_CONFIGS: dict[str, dict[str, Any]] = {
    "zz_reps1": {"family": "ZZFeatureMap", "reps": 1, "entanglement": "full"},
    "zz_reps2": {"family": "ZZFeatureMap", "reps": 2, "entanglement": "full"},
    "z_reps1": {"family": "ZFeatureMap", "reps": 1, "entanglement": "none"},
}

CLASSIFIER_C = 0.5
TOLERANCE = 0.05
METRICS = ("accuracy", "sensitivity", "specificity", "precision", "f1", "roc_auc", "pr_auc")


def build_feature_map(config_name: str, feature_count: int) -> QuantumCircuit:
    config = FEATURE_MAP_CONFIGS[config_name]
    if config["family"] == "ZZFeatureMap":
        return zz_feature_map(
            feature_dimension=feature_count,
            reps=int(config["reps"]),
            entanglement=str(config["entanglement"]),
        )
    if config["family"] == "ZFeatureMap":
        return z_feature_map(feature_dimension=feature_count, reps=int(config["reps"]))
    raise ValueError(f"Unsupported feature-map family: {config['family']}")


def circuit_resources(config_name: str, feature_count: int) -> dict[str, Any]:
    circuit = build_feature_map(config_name, feature_count)
    decomposed = circuit.decompose()
    operations = {str(name): int(count) for name, count in decomposed.count_ops().items()}
    return {
        "feature_map_config": config_name,
        "feature_map": FEATURE_MAP_CONFIGS[config_name]["family"],
        "reps": int(FEATURE_MAP_CONFIGS[config_name]["reps"]),
        "entanglement": FEATURE_MAP_CONFIGS[config_name]["entanglement"],
        "feature_count": int(feature_count),
        "qubit_count": int(circuit.num_qubits),
        "parameter_count": int(circuit.num_parameters),
        "circuit_depth": int(decomposed.depth()),
        "gate_count": int(sum(operations.values())),
        "gate_counts": operations,
        "depth_definition": "logical depth after one decomposition of the library feature-map circuit",
    }


class FastStatevectorFidelity(BaseStateFidelity):
    """Exact state overlap with cached statevectors and optional finite-shot sampling.

    This is passed into :class:`FidelityQuantumKernel`; it changes execution cost,
    not the kernel definition. ``shots`` samples the compute-uncompute all-zero
    event as a binomial variate with probability equal to the exact fidelity.
    """

    def __init__(self, *, shots: int | None = None, seed: int | None = None) -> None:
        super().__init__()
        if shots is not None and shots <= 0:
            raise ValueError("shots must be a positive integer or None")
        self.shots = shots
        self.seed = seed
        self._rng = np.random.default_rng(seed)
        self._state_cache: dict[tuple[Any, tuple[float, ...]], np.ndarray] = {}

    def create_fidelity_circuit(self, circuit_1: QuantumCircuit, circuit_2: QuantumCircuit) -> QuantumCircuit:
        return circuit_1.compose(circuit_2.inverse())

    @staticmethod
    def _as_list(circuits: QuantumCircuit | Sequence[QuantumCircuit]) -> list[QuantumCircuit]:
        return [circuits] if isinstance(circuits, QuantumCircuit) else list(circuits)

    def _state(self, circuit: QuantumCircuit, values: Sequence[float]) -> np.ndarray:
        numeric = tuple(float(value) for value in values)
        # The fidelity executor is scoped to one kernel/feature-map instance, so
        # object identity is a safe cache discriminator and avoids recomputing a
        # structural circuit hash for every one of O(n²) fidelity pairs.
        key = (id(circuit), numeric)
        if key not in self._state_cache:
            bound = circuit.assign_parameters(numeric, inplace=False)
            self._state_cache[key] = np.asarray(Statevector.from_instruction(bound).data)
        return self._state_cache[key]

    def _run(
        self,
        circuits_1: QuantumCircuit | Sequence[QuantumCircuit],
        circuits_2: QuantumCircuit | Sequence[QuantumCircuit],
        values_1: Sequence[float] | Sequence[Sequence[float]] | None = None,
        values_2: Sequence[float] | Sequence[Sequence[float]] | None = None,
        **options: Any,
    ) -> AlgorithmJob:
        left_circuits = self._as_list(circuits_1)
        right_circuits = self._as_list(circuits_2)
        if len(left_circuits) != len(right_circuits):
            raise ValueError("Circuit lists must be the same length")
        left_values = list(self._preprocess_values(left_circuits, values_1))
        right_values = list(self._preprocess_values(right_circuits, values_2))

        def calculate() -> StateFidelityResult:
            raw: list[float] = []
            for left, right, left_value, right_value in zip(
                left_circuits, right_circuits, left_values, right_values, strict=True
            ):
                overlap = np.vdot(self._state(left, left_value), self._state(right, right_value))
                fidelity = float(np.clip(abs(overlap) ** 2, 0.0, 1.0))
                if self.shots is not None:
                    fidelity = float(self._rng.binomial(self.shots, fidelity) / self.shots)
                raw.append(fidelity)
            metadata = [
                {"shots": self.shots, "seed": self.seed, "executor": "cached_statevector"}
                for _ in raw
            ]
            return StateFidelityResult(
                fidelities=self._truncate_fidelities(raw),
                raw_fidelities=raw,
                metadata=metadata,
                options=Options(shots=self.shots, seed=self.seed),
            )

        return AlgorithmJob(calculate)


class TrackedFidelityQuantumKernel(FidelityQuantumKernel):
    """FidelityQuantumKernel with auditable evaluation counts and wall times."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.evaluation_log: list[dict[str, Any]] = []

    def evaluate(self, x_vec: np.ndarray, y_vec: np.ndarray | None = None) -> np.ndarray:
        x_array = np.asarray(x_vec)
        y_array = None if y_vec is None else np.asarray(y_vec)
        started = time.perf_counter()
        matrix = super().evaluate(x_array, y_array)
        elapsed = time.perf_counter() - started
        if y_array is None or (x_array.shape == y_array.shape and np.array_equal(x_array, y_array)):
            entries = len(x_array) * (len(x_array) - 1) // 2
            shape = [len(x_array), len(x_array)]
        else:
            entries = len(x_array) * len(y_array)
            shape = [len(x_array), len(y_array)]
        self.evaluation_log.append(
            {
                "shape": shape,
                "kernel_evaluations": int(entries),
                "wall_seconds": float(elapsed),
            }
        )
        return matrix


def make_quantum_kernel(
    config_name: str,
    feature_count: int,
    *,
    shots: int | None = None,
    seed: int = EXPERIMENT_SEED,
) -> tuple[TrackedFidelityQuantumKernel, dict[str, Any]]:
    started = time.perf_counter()
    feature_map = build_feature_map(config_name, feature_count)
    fidelity = FastStatevectorFidelity(shots=shots, seed=seed)
    kernel = TrackedFidelityQuantumKernel(
        feature_map=feature_map,
        fidelity=fidelity,
        enforce_psd=True,
        evaluate_duplicates="off_diagonal",
    )
    metadata = circuit_resources(config_name, feature_count)
    metadata.update(
        {
            "kernel_backend": "qiskit.quantum_info.Statevector (cached exact overlap)",
            "execution_mode": "ideal exact statevector" if shots is None else "finite-shot binomial sampling of exact compute-uncompute fidelity",
            "shots": shots,
            "seed": seed,
            "feature_map_construction_seconds": float(time.perf_counter() - started),
        }
    )
    return kernel, metadata


def prepare_fold(
    train: pd.DataFrame,
    valid: pd.DataFrame,
    *,
    representation: str,
    budget: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any], dict[str, Any]]:
    if representation == "clinical":
        columns = CLINICAL_SIGNATURES[budget]
    elif representation == "pca":
        columns = FEATURES
    else:
        raise ValueError(f"Unknown representation: {representation}")
    preprocessor = make_preprocessor(columns, scale=True)
    train_matrix = np.asarray(preprocessor.fit_transform(train[columns], train[TARGET]), dtype=float)
    valid_matrix = np.asarray(preprocessor.transform(valid[columns]), dtype=float)
    pca_meta: dict[str, Any] = {
        "pca_components": None,
        "pca_fit_n": None,
        "pca_explained_variance": None,
    }
    if representation == "pca":
        pca = PCA(n_components=budget, random_state=seed)
        train_matrix = pca.fit_transform(train_matrix)
        valid_matrix = pca.transform(valid_matrix)
        pca_meta = {
            "pca_components": budget,
            "pca_fit_n": int(pca.n_samples_),
            "pca_explained_variance": float(pca.explained_variance_ratio_.sum()),
        }
    if train_matrix.shape[1] != budget or valid_matrix.shape[1] != budget:
        raise RuntimeError(
            f"Expected {budget} transformed inputs for {representation}, got "
            f"{train_matrix.shape[1]} and {valid_matrix.shape[1]}"
        )
    audit = {
        "representation": representation,
        "budget": budget,
        "source_columns": columns,
        "preprocessor_fit_row_ids": [str(value) for value in train.index],
        "validation_row_ids": [str(value) for value in valid.index],
        **pca_meta,
    }
    return train_matrix, valid_matrix, audit, pca_meta


def evaluate_classical(
    train_matrix: np.ndarray,
    y_train: np.ndarray,
    valid_matrix: np.ndarray,
    y_valid: np.ndarray,
    *,
    seed: int,
) -> dict[str, Any]:
    estimator = SVC(C=CLASSIFIER_C, kernel="rbf", gamma="scale", random_state=seed)
    started = time.perf_counter()
    estimator.fit(train_matrix, y_train)
    train_seconds = time.perf_counter() - started
    started = time.perf_counter()
    scores = np.asarray(estimator.decision_function(valid_matrix), dtype=float)
    prediction_seconds = time.perf_counter() - started
    predictions = (scores >= 0.0).astype(int)
    return {
        **binary_metrics(y_valid, predictions, scores),
        "training_wall_seconds": float(train_seconds),
        "model_fit_seconds": float(train_seconds),
        "prediction_wall_seconds": float(prediction_seconds),
        "train_kernel_seconds": 0.0,
        "inference_kernel_seconds": 0.0,
        "kernel_evaluations_train": 0,
        "kernel_evaluations_inference": 0,
        "train_kernel_rows": int(len(train_matrix)),
        "train_kernel_columns": int(train_matrix.shape[1]),
        "prediction": predictions,
        "score": scores,
    }


def evaluate_qsvc(
    train_matrix: np.ndarray,
    y_train: np.ndarray,
    valid_matrix: np.ndarray,
    y_valid: np.ndarray,
    *,
    config_name: str,
    seed: int,
    shots: int | None = None,
    kernel: TrackedFidelityQuantumKernel | None = None,
    kernel_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if kernel is None:
        kernel, kernel_metadata = make_quantum_kernel(
            config_name, train_matrix.shape[1], shots=shots, seed=seed
        )
    if kernel_metadata is None:
        kernel_metadata = circuit_resources(config_name, train_matrix.shape[1])
    estimator = QSVC(quantum_kernel=kernel, C=CLASSIFIER_C)
    started = time.perf_counter()
    estimator.fit(train_matrix, y_train)
    training_wall = time.perf_counter() - started
    started = time.perf_counter()
    scores = np.asarray(estimator.decision_function(valid_matrix), dtype=float)
    prediction_wall = time.perf_counter() - started
    predictions = (scores >= 0.0).astype(int)
    if len(kernel.evaluation_log) < 2:
        raise RuntimeError("QSVC did not produce the expected train and inference kernel calls")
    train_log = kernel.evaluation_log[0]
    inference_log = kernel.evaluation_log[1]
    return {
        **binary_metrics(y_valid, predictions, scores),
        "training_wall_seconds": float(training_wall),
        "model_fit_seconds": float(max(0.0, training_wall - train_log["wall_seconds"])),
        "prediction_wall_seconds": float(prediction_wall),
        "train_kernel_seconds": float(train_log["wall_seconds"]),
        "inference_kernel_seconds": float(inference_log["wall_seconds"]),
        "kernel_evaluations_train": int(train_log["kernel_evaluations"]),
        "kernel_evaluations_inference": int(inference_log["kernel_evaluations"]),
        "train_kernel_rows": int(train_log["shape"][0]),
        "train_kernel_columns": int(train_log["shape"][1]),
        "inference_kernel_rows": int(inference_log["shape"][0]),
        "inference_kernel_columns": int(inference_log["shape"][1]),
        **kernel_metadata,
        "prediction": predictions,
        "score": scores,
    }


def _record_without_arrays(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key not in {"prediction", "score", "gate_counts"}}


def run_repeated_cv(
    development: pd.DataFrame,
    *,
    representations: Iterable[str],
    budgets: Iterable[int],
    quantum_configs: Iterable[str],
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    splitter = RepeatedStratifiedKFold(
        n_splits=OUTER_SPLITS,
        n_repeats=OUTER_REPEATS,
        random_state=EXPERIMENT_SEED,
    )
    records: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    y = development[TARGET].to_numpy(dtype=int)
    split_positions = list(splitter.split(development, y))
    for representation in representations:
        for budget in budgets:
            if representation == "clinical" and budget not in CLINICAL_SIGNATURES:
                continue
            for outer_index, (train_pos, valid_pos) in enumerate(split_positions):
                repeat = outer_index // OUTER_SPLITS + 1
                fold = outer_index % OUTER_SPLITS + 1
                seed = EXPERIMENT_SEED + outer_index
                train = development.iloc[train_pos]
                valid = development.iloc[valid_pos]
                train_matrix, valid_matrix, fold_audit, pca_meta = prepare_fold(
                    train, valid, representation=representation, budget=budget, seed=seed
                )
                fold_audit.update({"repeat": repeat, "fold": fold})
                audit.append(fold_audit)
                base = {
                    "repeat": repeat,
                    "fold": fold,
                    "representation": representation,
                    "budget": budget,
                    "train_n": int(len(train)),
                    "valid_n": int(len(valid)),
                    **pca_meta,
                }
                classical = evaluate_classical(
                    train_matrix,
                    train[TARGET].to_numpy(dtype=int),
                    valid_matrix,
                    valid[TARGET].to_numpy(dtype=int),
                    seed=seed,
                )
                records.append(
                    {
                        **base,
                        "model": "classical_rbf_svm",
                        "feature_map_config": "rbf",
                        "kernel_backend": "scikit-learn libsvm RBF",
                        "execution_mode": "classical CPU",
                        "qubit_count": 0,
                        "circuit_depth": 0,
                        "gate_count": 0,
                        "reps": 0,
                        "entanglement": "none",
                        "shots": None,
                        **_record_without_arrays(classical),
                    }
                )
                for config_name in quantum_configs:
                    quantum = evaluate_qsvc(
                        train_matrix,
                        train[TARGET].to_numpy(dtype=int),
                        valid_matrix,
                        valid[TARGET].to_numpy(dtype=int),
                        config_name=config_name,
                        seed=seed,
                    )
                    records.append(
                        {
                            **base,
                            "model": "qsvc",
                            **_record_without_arrays(quantum),
                        }
                    )
    return pd.DataFrame(records), audit


SUMMARY_METRICS = METRICS + (
    "training_wall_seconds",
    "model_fit_seconds",
    "prediction_wall_seconds",
    "train_kernel_seconds",
    "inference_kernel_seconds",
    "kernel_evaluations_train",
    "kernel_evaluations_inference",
)


def summarise_results(results: pd.DataFrame) -> pd.DataFrame:
    groups = ["representation", "budget", "model", "feature_map_config"]
    rows: list[dict[str, Any]] = []
    for keys, group in results.groupby(groups, dropna=False):
        row = dict(zip(groups, keys, strict=True))
        row["fold_assessments"] = int(len(group))
        for metric in SUMMARY_METRICS:
            values = group[metric].astype(float).to_numpy()
            row[f"{metric}_mean"] = float(np.mean(values))
            row[f"{metric}_std"] = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
        first = group.iloc[0]
        for column in [
            "qubit_count", "circuit_depth", "gate_count", "reps", "entanglement",
            "kernel_backend", "execution_mode", "shots", "pca_explained_variance",
        ]:
            if column in group:
                row[column] = first[column] if column != "pca_explained_variance" else float(group[column].mean())
        rows.append(row)
    return pd.DataFrame(rows).sort_values(groups, ignore_index=True)


def choose_best_qsvc(summary: pd.DataFrame) -> dict[str, Any]:
    candidates = summary[
        (summary["representation"] == "clinical")
        & (summary["budget"] == 8)
        & (summary["model"] == "qsvc")
    ].copy()
    if len(candidates) != len(FEATURE_MAP_CONFIGS):
        raise RuntimeError("All predefined 8-variable feature maps must be evaluated before selection")
    classical = summary[
        (summary["representation"] == "clinical")
        & (summary["budget"] == 8)
        & (summary["model"] == "classical_rbf_svm")
        & (summary["feature_map_config"] == "rbf")
    ].iloc[0]
    for metric in ("sensitivity", "specificity", "roc_auc", "f1"):
        candidates[f"{metric}_delta"] = candidates[f"{metric}_mean"] - classical[f"{metric}_mean"]
    candidates["meets_joint_tolerance"] = candidates[
        [f"{metric}_delta" for metric in ("sensitivity", "specificity", "roc_auc", "f1")]
    ].min(axis=1) >= -TOLERANCE
    eligible = candidates[candidates["meets_joint_tolerance"]]
    ranking_pool = eligible if not eligible.empty else candidates
    ranking_pool = ranking_pool.sort_values(
        [
            "sensitivity_mean", "roc_auc_mean", "f1_mean", "specificity_mean",
            "circuit_depth", "training_wall_seconds_mean",
        ],
        ascending=[False, False, False, False, True, True],
    )
    winner = ranking_pool.iloc[0]
    return {
        "selection_scope": "development data only; primary eight-variable clinical representation",
        "selection_rule": "first retain configurations whose sensitivity, specificity, ROC-AUC and F1 degradations are each <=0.05 versus the identical-fold classical SVM; then rank lexicographically by sensitivity, ROC-AUC, F1, specificity, lower depth and lower training wall time",
        "joint_tolerance_filter_had_eligible_configuration": bool(not eligible.empty),
        "feature_map_config": str(winner["feature_map_config"]),
        "feature_map": FEATURE_MAP_CONFIGS[str(winner["feature_map_config"])]["family"],
        "reps": int(winner["reps"]),
        "entanglement": str(winner["entanglement"]),
        "classifier_C": CLASSIFIER_C,
        "cv_sensitivity": float(winner["sensitivity_mean"]),
        "cv_specificity": float(winner["specificity_mean"]),
        "cv_roc_auc": float(winner["roc_auc_mean"]),
        "cv_f1": float(winner["f1_mean"]),
        "locked_test_was_used": False,
    }


def paired_comparisons(results: pd.DataFrame, best_config: str, *, n_bootstrap: int = 5000) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    rng = np.random.default_rng(EXPERIMENT_SEED)
    for representation in ("clinical", "pca"):
        for budget in (8, 6, 4):
            subset = results[(results["representation"] == representation) & (results["budget"] == budget)]
            classical = subset[subset["model"] == "classical_rbf_svm"].set_index(["repeat", "fold"])
            quantum = subset[(subset["model"] == "qsvc") & (subset["feature_map_config"] == best_config)].set_index(["repeat", "fold"])
            if classical.empty or quantum.empty:
                continue
            common = classical.index.intersection(quantum.index)
            for metric in ("sensitivity", "specificity", "roc_auc", "f1"):
                deltas = quantum.loc[common, metric].to_numpy() - classical.loc[common, metric].to_numpy()
                for (repeat, fold), delta in zip(common, deltas, strict=True):
                    rows.append(
                        {
                            "representation": representation,
                            "budget": budget,
                            "repeat": repeat,
                            "fold": fold,
                            "metric": metric,
                            "delta_qsvc_minus_classical": float(delta),
                        }
                    )
                boot = np.mean(rng.choice(deltas, size=(n_bootstrap, len(deltas)), replace=True), axis=1)
                nonzero = deltas[~np.isclose(deltas, 0.0)]
                if len(nonzero) >= 2:
                    try:
                        p_value = float(stats.wilcoxon(deltas, zero_method="wilcox").pvalue)
                    except ValueError:
                        p_value = math.nan
                else:
                    p_value = math.nan
                summaries.append(
                    {
                        "representation": representation,
                        "budget": budget,
                        "metric": metric,
                        "mean_delta": float(np.mean(deltas)),
                        "median_delta": float(np.median(deltas)),
                        "bootstrap_ci95_low": float(np.quantile(boot, 0.025)),
                        "bootstrap_ci95_high": float(np.quantile(boot, 0.975)),
                        "wilcoxon_p_value": p_value,
                        "fold_pairs": int(len(deltas)),
                    }
                )
    return pd.DataFrame(rows), pd.DataFrame(summaries)


def kernel_diagnostics(matrix: np.ndarray, labels: np.ndarray) -> dict[str, Any]:
    matrix = np.asarray(matrix, dtype=float)
    labels = np.asarray(labels, dtype=int)
    if matrix.shape != (len(labels), len(labels)):
        raise ValueError("Kernel matrix and labels are incompatible")
    sym = (matrix + matrix.T) / 2
    eigenvalues = np.linalg.eigvalsh(sym)
    positive = eigenvalues[eigenvalues > 1e-10]
    condition = float(eigenvalues.max() / positive.min()) if len(positive) else math.inf
    mask = ~np.eye(len(matrix), dtype=bool)
    off = matrix[mask]
    positive_mask = labels == 1
    negative_mask = labels == 0
    within_positive = matrix[np.ix_(positive_mask, positive_mask)]
    within_negative = matrix[np.ix_(negative_mask, negative_mask)]
    between = matrix[np.ix_(positive_mask, negative_mask)]

    def offdiag_mean(value: np.ndarray) -> float:
        return float(value[~np.eye(len(value), dtype=bool)].mean()) if len(value) > 1 else math.nan

    centered = sym - sym.mean(axis=0, keepdims=True) - sym.mean(axis=1, keepdims=True) + sym.mean()
    target = np.where(labels == 1, 1.0, -1.0)
    target_kernel = np.outer(target, target)
    target_centered = target_kernel - target_kernel.mean(axis=0, keepdims=True) - target_kernel.mean(axis=1, keepdims=True) + target_kernel.mean()
    denominator = np.linalg.norm(centered, "fro") * np.linalg.norm(target_centered, "fro")
    alignment = float(np.sum(centered * target_centered) / denominator) if denominator else math.nan
    return {
        "kernel_rows": int(matrix.shape[0]),
        "kernel_columns": int(matrix.shape[1]),
        "diagonal_mean": float(np.diag(matrix).mean()),
        "diagonal_std": float(np.diag(matrix).std()),
        "diagonal_max_abs_deviation_from_one": float(np.max(np.abs(np.diag(matrix) - 1.0))),
        "off_diagonal_mean": float(off.mean()),
        "off_diagonal_std": float(off.std()),
        "off_diagonal_q05": float(np.quantile(off, 0.05)),
        "off_diagonal_median": float(np.median(off)),
        "off_diagonal_q95": float(np.quantile(off, 0.95)),
        "within_ckd_similarity": offdiag_mean(within_positive),
        "within_not_ckd_similarity": offdiag_mean(within_negative),
        "between_class_similarity": float(between.mean()),
        "kernel_target_alignment": alignment,
        "minimum_eigenvalue": float(eigenvalues.min()),
        "effective_rank": int(np.sum(eigenvalues > 1e-10)),
        "condition_number_positive_spectrum": condition,
    }


def dataframe_sha256(frame: pd.DataFrame) -> str:
    payload = frame.to_csv(index=True, lineterminator="\n").encode()
    return hashlib.sha256(payload).hexdigest()


def json_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def write_json(path: str | Path, payload: Any) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(to_jsonable(payload), indent=2, sort_keys=True) + "\n")
