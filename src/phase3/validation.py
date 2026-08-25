from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from qiskit_machine_learning.algorithms import QSVC
from scipy import stats
from scipy.io import arff
from sklearn.feature_selection import mutual_info_classif
from sklearn.impute import SimpleImputer
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from src.phase1.data import TARGET, sha256
from src.phase1.modeling import EXPERIMENT_SEED, binary_metrics, make_preprocessor
from src.phase2.benchmark import CLASSIFIER_C, CLINICAL_SIGNATURES, make_quantum_kernel


FROZEN_FEATURE_MAP = "z_reps1"
NUMERIC_CKD = ["hemo", "al", "sg", "pcv", "sc"]


def json_dump(path: str | Path, payload: Any) -> None:
    def clean(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): clean(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [clean(item) for item in value]
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.floating,)):
            return None if not np.isfinite(value) else float(value)
        if isinstance(value, float) and not np.isfinite(value):
            return None
        return value

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(clean(payload), indent=2, sort_keys=True) + "\n")


def file_hashes(paths: Iterable[str | Path]) -> dict[str, str]:
    return {str(Path(path)): sha256(Path(path)) for path in paths}


@dataclass
class FittedPair:
    features: list[str]
    preprocessor: Any
    classical: SVC
    qsvc: QSVC
    fit_seconds: dict[str, float]


def fit_ckd_pair(train: pd.DataFrame, budget: int, seed: int) -> FittedPair:
    features = list(CLINICAL_SIGNATURES[budget])
    preprocessor = make_preprocessor(features, scale=True)
    matrix = np.asarray(preprocessor.fit_transform(train[features], train[TARGET]), dtype=float)
    y = train[TARGET].to_numpy(dtype=int)

    classical = SVC(C=CLASSIFIER_C, kernel="rbf", gamma="scale", random_state=seed)
    started = time.perf_counter()
    classical.fit(matrix, y)
    classical_seconds = time.perf_counter() - started

    kernel, _ = make_quantum_kernel(FROZEN_FEATURE_MAP, matrix.shape[1], seed=seed)
    qsvc = QSVC(quantum_kernel=kernel, C=CLASSIFIER_C)
    started = time.perf_counter()
    qsvc.fit(matrix, y)
    qsvc_seconds = time.perf_counter() - started
    return FittedPair(
        features=features,
        preprocessor=preprocessor,
        classical=classical,
        qsvc=qsvc,
        fit_seconds={"classical_rbf_svm": classical_seconds, "qsvc": qsvc_seconds},
    )


def evaluate_pair(pair: FittedPair, frame: pd.DataFrame) -> tuple[list[dict[str, Any]], dict[str, dict[str, np.ndarray]]]:
    matrix = np.asarray(pair.preprocessor.transform(frame[pair.features]), dtype=float)
    y = frame[TARGET].to_numpy(dtype=int)
    records: list[dict[str, Any]] = []
    arrays: dict[str, dict[str, np.ndarray]] = {}
    for name, estimator in (("classical_rbf_svm", pair.classical), ("qsvc", pair.qsvc)):
        started = time.perf_counter()
        score = np.asarray(estimator.decision_function(matrix), dtype=float)
        predict_seconds = time.perf_counter() - started
        prediction = (score >= 0.0).astype(int)
        records.append({"model": name, **binary_metrics(y, prediction, score), "prediction_seconds": predict_seconds})
        arrays[name] = {"score": score, "prediction": prediction}
    return records, arrays


def mean_ci(values: Iterable[float], *, bounded: bool = True) -> tuple[float, float, float, float]:
    array = np.asarray(list(values), dtype=float)
    mean = float(np.mean(array))
    std = float(np.std(array, ddof=1)) if len(array) > 1 else 0.0
    margin = float(stats.t.ppf(0.975, len(array) - 1) * std / math.sqrt(len(array))) if len(array) > 1 else 0.0
    low, high = mean - margin, mean + margin
    if bounded:
        low, high = max(0.0, low), min(1.0, high)
    return mean, std, low, high


def summarize_cv(results: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    metrics = ["accuracy", "sensitivity", "specificity", "precision", "f1", "roc_auc", "pr_auc"]
    rows: list[dict[str, Any]] = []
    for keys, group in results.groupby(groups, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(groups, keys, strict=True))
        row["assessments"] = len(group)
        for metric in metrics:
            mean, std, low, high = mean_ci(group[metric])
            row.update({f"{metric}_mean": mean, f"{metric}_std": std, f"{metric}_ci95_low": low, f"{metric}_ci95_high": high})
        if "fit_seconds" in group:
            row["fit_seconds_mean"] = float(group["fit_seconds"].mean())
        rows.append(row)
    return pd.DataFrame(rows)


def paired_delta_summary(results: pd.DataFrame, id_columns: list[str], group_columns: list[str]) -> pd.DataFrame:
    metrics = ["sensitivity", "specificity", "roc_auc", "f1"]
    rows: list[dict[str, Any]] = []
    rng = np.random.default_rng(EXPERIMENT_SEED)
    for keys, group in results.groupby(group_columns, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        base = dict(zip(group_columns, keys, strict=True))
        left = group[group.model == "classical_rbf_svm"].set_index(id_columns)
        right = group[group.model == "qsvc"].set_index(id_columns)
        common = left.index.intersection(right.index)
        for metric in metrics:
            delta = right.loc[common, metric].to_numpy() - left.loc[common, metric].to_numpy()
            boot = np.mean(rng.choice(delta, size=(4000, len(delta)), replace=True), axis=1)
            try:
                p_value = float(stats.wilcoxon(delta).pvalue) if np.any(~np.isclose(delta, 0)) else math.nan
            except ValueError:
                p_value = math.nan
            rows.append({
                **base,
                "metric": metric,
                "pairs": len(delta),
                "mean_delta_qsvc_minus_classical": float(delta.mean()),
                "bootstrap_ci95_low": float(np.quantile(boot, 0.025)),
                "bootstrap_ci95_high": float(np.quantile(boot, 0.975)),
                "wilcoxon_p_value": p_value,
            })
    return pd.DataFrame(rows)


def inject_missingness(frame: pd.DataFrame, features: list[str], fraction: float, seed: int) -> tuple[pd.DataFrame, int]:
    result = frame.copy()
    if fraction <= 0:
        return result, 0
    rng = np.random.default_rng(seed)
    observed = np.argwhere(~result[features].isna().to_numpy())
    count = int(round(fraction * len(observed)))
    selected = observed[rng.choice(len(observed), size=count, replace=False)]
    for row, column in selected:
        result.iat[row, result.columns.get_loc(features[column])] = np.nan
    return result, count


def perturb_numeric(frame: pd.DataFrame, train: pd.DataFrame, scale_fraction: float, seed: int) -> pd.DataFrame:
    result = frame.copy()
    rng = np.random.default_rng(seed)
    for feature in NUMERIC_CKD:
        sd = float(train[feature].std(skipna=True))
        mask = result[feature].notna()
        result.loc[mask, feature] = result.loc[mask, feature] + rng.normal(0.0, scale_fraction * sd, int(mask.sum()))
        if feature in {"hemo", "al", "pcv", "sc"}:
            result.loc[mask, feature] = result.loc[mask, feature].clip(lower=0)
    return result


def expected_calibration_error(y: np.ndarray, probability: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0, 1, bins + 1)
    total = 0.0
    for low, high in zip(edges[:-1], edges[1:], strict=True):
        mask = (probability >= low) & (probability < high if high < 1 else probability <= high)
        if mask.any():
            total += mask.mean() * abs(float(y[mask].mean()) - float(probability[mask].mean()))
    return float(total)


def calibration_metrics(y: np.ndarray, probability: np.ndarray) -> dict[str, float]:
    clipped = np.clip(probability, 1e-7, 1 - 1e-7)
    return {
        "brier": float(brier_score_loss(y, clipped)),
        "log_loss": float(log_loss(y, clipped, labels=[0, 1])),
        "ece_10_bin": expected_calibration_error(y, clipped),
    }


def load_bd_kdd(path: str | Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    mapping = {"Hemo": "hemo", "Al": "al", "Dm": "dm", "Sg": "sg", "Pcv": "pcv", "Appet": "appet", "Htn": "htn", "Sc": "sc", "Class": TARGET}
    frame = raw[list(mapping)].rename(columns=mapping).copy()
    frame["dm"] = frame["dm"].map({0: "no", 1: "yes"})
    frame["htn"] = frame["htn"].map({0: "no", 1: "yes"})
    frame["appet"] = frame["appet"].map({0: "poor", 1: "good"})
    frame[TARGET] = frame[TARGET].astype(int)
    frame.index = [f"bd-kdd-{index + 1:04d}" for index in range(len(frame))]
    return frame


HEART_COLUMNS = ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal", "num"]


def load_cleveland(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path, names=HEART_COLUMNS, na_values="?")
    for column in HEART_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    frame[TARGET] = (frame.pop("num") > 0).astype(int)
    frame.index = [f"cleveland-{index + 1:03d}" for index in range(len(frame))]
    return frame


def load_pima(path: str | Path) -> pd.DataFrame:
    data, _ = arff.loadarff(path)
    frame = pd.DataFrame(data)
    frame[TARGET] = frame.pop("class").map({b"tested_negative": 0, b"tested_positive": 1}).astype(int)
    for column in ["plas", "pres", "skin", "insu", "mass"]:
        frame[column] = frame[column].replace(0, np.nan)
    frame.index = [f"pima-{index + 1:03d}" for index in range(len(frame))]
    return frame


def numeric_preprocessor() -> Pipeline:
    return Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])


def rank_numeric_features(train: pd.DataFrame, features: list[str], seed: int) -> list[str]:
    matrix = numeric_preprocessor().fit_transform(train[features])
    score = mutual_info_classif(matrix, train[TARGET], random_state=seed)
    return [feature for _, feature in sorted(zip(score, features, strict=True), key=lambda item: (-item[0], item[1]))]


def evaluate_numeric_models(
    train: pd.DataFrame,
    valid: pd.DataFrame,
    features: list[str],
    seed: int,
    *,
    include_qsvc: bool = True,
) -> list[dict[str, Any]]:
    preprocessor = numeric_preprocessor()
    x_train = np.asarray(preprocessor.fit_transform(train[features]), dtype=float)
    x_valid = np.asarray(preprocessor.transform(valid[features]), dtype=float)
    y_train = train[TARGET].to_numpy(dtype=int)
    y_valid = valid[TARGET].to_numpy(dtype=int)
    models: list[tuple[str, Any]] = [("classical_rbf_svm", SVC(C=CLASSIFIER_C, kernel="rbf", gamma="scale", random_state=seed))]
    if include_qsvc:
        kernel, _ = make_quantum_kernel(FROZEN_FEATURE_MAP, len(features), seed=seed)
        models.append(("qsvc", QSVC(quantum_kernel=kernel, C=CLASSIFIER_C)))
    records = []
    for name, model in models:
        started = time.perf_counter()
        model.fit(x_train, y_train)
        fit_seconds = time.perf_counter() - started
        score = np.asarray(model.decision_function(x_valid), dtype=float)
        prediction = (score >= 0).astype(int)
        records.append({"model": name, "fit_seconds": fit_seconds, **binary_metrics(y_valid, prediction, score)})
    return records


def stable_hash_of_json(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
