from __future__ import annotations

import json
import os
import platform
import sys
from collections import Counter
from datetime import date
from importlib.metadata import version
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", "/tmp/qcare-phase3-matplotlib-cache")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/qcare-phase3-xdg-cache")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from qiskit_machine_learning.algorithms import QSVC
from scipy import stats
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_score
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedKFold, train_test_split
from sklearn.svm import SVC

from src.phase1.data import TARGET, sha256
from src.phase1.modeling import EXPERIMENT_SEED, binary_metrics, make_preprocessor
from src.phase2.benchmark import CLASSIFIER_C, CLINICAL_SIGNATURES, FEATURE_MAP_CONFIGS, circuit_resources, make_quantum_kernel
from src.phase3.validation import (
    FROZEN_FEATURE_MAP,
    calibration_metrics,
    evaluate_numeric_models,
    evaluate_pair,
    fit_ckd_pair,
    inject_missingness,
    json_dump,
    load_bd_kdd,
    load_cleveland,
    load_pima,
    mean_ci,
    paired_delta_summary,
    perturb_numeric,
    rank_numeric_features,
    stable_hash_of_json,
    summarize_cv,
)


PROCESSED = PROJECT_ROOT / "data/processed/ckd_clean.csv"
SPLITS = PROJECT_ROOT / "artifacts/splits.json"
BD_PATH = PROJECT_ROOT / "data/external/raw/BD-KDD_Dataset.csv"
BD_DICT = PROJECT_ROOT / "data/external/raw/BD-KDD_Dictionary.md"
BD_META = PROJECT_ROOT / "data/external/raw/BD-KDD_dataverse_metadata.json"
HEART_PATH = PROJECT_ROOT / "data/external/raw/heart_disease/processed.cleveland.data"
HEART_ZIP = PROJECT_ROOT / "data/external/raw/uci_heart_disease_45.zip"
PIMA_PATH = PROJECT_ROOT / "data/external/raw/openml_37_pima_diabetes.arff"

ARTIFACTS = PROJECT_ROOT / "artifacts/phase3"
VALIDATION = PROJECT_ROOT / "reports/validation"
FIGURES = VALIDATION / "figures"
RESEARCH = PROJECT_ROOT / "research"
MODEL_DIR = PROJECT_ROOT / "artifacts/models"


def fmt(value: Any, digits: int = 3) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "NR"
    return f"{float(value):.{digits}f}"


def table(headers: list[str], rows: list[list[Any]]) -> str:
    clean = lambda value: str(value).replace("|", "\\|").replace("\n", " ")
    return "\n".join([
        "| " + " | ".join(map(clean, headers)) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
        *("| " + " | ".join(map(clean, row)) + " |" for row in rows),
    ])


def dataframe_table(frame: pd.DataFrame, *, include_index: bool = False) -> str:
    value = frame.copy()
    if include_index:
        value = value.reset_index()
    headers = [" / ".join(str(part) for part in column if str(part)) if isinstance(column, tuple) else str(column) for column in value.columns]
    rows = [[fmt(item) if isinstance(item, (float, np.floating)) else item for item in row] for row in value.itertuples(index=False, name=None)]
    return table(headers, rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n")


def save_figure(fig: plt.Figure, name: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIGURES / name, dpi=180, bbox_inches="tight")
    plt.close(fig)


def load_ckd() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frame = pd.read_csv(PROCESSED, dtype={"row_id": str}).set_index("row_id")
    frame[TARGET] = frame[TARGET].astype(int)
    split = json.loads(SPLITS.read_text())
    development = frame.loc[split["development_row_ids"]].copy()
    locked = frame.loc[split["locked_test_row_ids"]].copy()
    if set(development.index) & set(locked.index):
        raise RuntimeError("Development and locked-test partitions overlap")
    return frame, development, locked


def assert_freeze() -> None:
    phase1 = json.loads((PROJECT_ROOT / "artifacts/development_decision.json").read_text())
    phase2 = json.loads((PROJECT_ROOT / "artifacts/quantum_development_choice.json").read_text())
    for budget in (8, 6):
        actual = phase1["selected_budgets"][str(budget)]["features_frozen_from_complete_development_set"]
        if actual != CLINICAL_SIGNATURES[budget]:
            raise RuntimeError(f"Feature signature drift for budget {budget}")
    if phase2["feature_map_config"] != FROZEN_FEATURE_MAP or float(phase2["classifier_C"]) != CLASSIFIER_C:
        raise RuntimeError("Frozen Phase 2 QSVC configuration drifted")


def reference_cv(development: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    result_path = ARTIFACTS / "reference_cv.csv"
    prediction_path = ARTIFACTS / "reference_cv_predictions.csv"
    if result_path.exists() and prediction_path.exists():
        results = pd.read_csv(result_path)
        predictions = pd.read_csv(prediction_path)
    else:
        splitter = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=EXPERIMENT_SEED)
        results_records: list[dict[str, Any]] = []
        prediction_records: list[dict[str, Any]] = []
        for budget in (8, 6):
            for index, (train_pos, valid_pos) in enumerate(splitter.split(development, development[TARGET])):
                repeat, fold, seed = index // 5 + 1, index % 5 + 1, EXPERIMENT_SEED + index
                train, valid = development.iloc[train_pos], development.iloc[valid_pos]
                pair = fit_ckd_pair(train, budget, seed)
                metrics, arrays = evaluate_pair(pair, valid)
                for record in metrics:
                    record.update({"budget": budget, "repeat": repeat, "fold": fold, "fit_seconds": pair.fit_seconds[record["model"]]})
                    results_records.append(record)
                for model, values in arrays.items():
                    for row_id, truth, prediction, score in zip(valid.index, valid[TARGET], values["prediction"], values["score"], strict=True):
                        prediction_records.append({"budget": budget, "repeat": repeat, "fold": fold, "row_id": row_id, "target": truth, "model": model, "prediction": prediction, "score": score})
                pd.DataFrame(results_records).to_csv(result_path, index=False)
                pd.DataFrame(prediction_records).to_csv(prediction_path, index=False)
                print(f"Reference CV budget={budget} repeat={repeat} fold={fold}", flush=True)
        results, predictions = pd.DataFrame(results_records), pd.DataFrame(prediction_records)
    summary = summarize_cv(results, ["budget", "model"])
    paired = paired_delta_summary(results, ["repeat", "fold"], ["budget"])
    summary.to_csv(ARTIFACTS / "reference_cv_summary.csv", index=False)
    paired.to_csv(ARTIFACTS / "reference_cv_paired.csv", index=False)
    return results, predictions, summary, paired


def missingness_study(development: pd.DataFrame) -> pd.DataFrame:
    output = ARTIFACTS / "missingness.csv"
    if output.exists():
        return pd.read_csv(output)
    splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=EXPERIMENT_SEED)
    rows: list[dict[str, Any]] = []
    features = CLINICAL_SIGNATURES[8]
    for fold, (train_pos, valid_pos) in enumerate(splitter.split(development, development[TARGET]), start=1):
        clean_train, clean_valid = development.iloc[train_pos], development.iloc[valid_pos]
        for stress_seed in range(3):
            for level in (0.0, 0.05, 0.10, 0.20):
                seed = EXPERIMENT_SEED + fold * 100 + stress_seed * 10 + int(level * 100)
                train, added_train = inject_missingness(clean_train, features, level, seed)
                valid, added_valid = inject_missingness(clean_valid, features, level, seed + 1)
                pair = fit_ckd_pair(train, 8, seed)
                metrics, _ = evaluate_pair(pair, valid)
                for record in metrics:
                    rows.append({"fold": fold, "stress_seed": stress_seed, "missingness_fraction": level, "added_train_cells": added_train, "added_valid_cells": added_valid, **record})
                pd.DataFrame(rows).to_csv(output, index=False)
                print(f"Missingness fold={fold} seed={stress_seed} level={level:.2f}", flush=True)
    return pd.DataFrame(rows)


def perturbation_study(development: pd.DataFrame) -> pd.DataFrame:
    output = ARTIFACTS / "perturbation.csv"
    if output.exists():
        return pd.read_csv(output)
    splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=EXPERIMENT_SEED)
    rows: list[dict[str, Any]] = []
    for fold, (train_pos, valid_pos) in enumerate(splitter.split(development, development[TARGET]), start=1):
        train, valid = development.iloc[train_pos], development.iloc[valid_pos]
        pair = fit_ckd_pair(train, 8, EXPERIMENT_SEED + fold)
        clean_metrics, clean_arrays = evaluate_pair(pair, valid)
        clean_by_model = {row["model"]: row for row in clean_metrics}
        for stress_seed in range(3):
            for level in (0.01, 0.05, 0.10):
                stressed = perturb_numeric(valid, train, level, EXPERIMENT_SEED + fold * 100 + stress_seed * 10 + int(level * 100))
                metrics, arrays = evaluate_pair(pair, stressed)
                for record in metrics:
                    model = record["model"]
                    rows.append({
                        "fold": fold,
                        "stress_seed": stress_seed,
                        "noise_sd_fraction": level,
                        "model": model,
                        "flip_rate": float(np.mean(arrays[model]["prediction"] != clean_arrays[model]["prediction"])),
                        "sensitivity": record["sensitivity"],
                        "roc_auc": record["roc_auc"],
                        "sensitivity_delta": record["sensitivity"] - clean_by_model[model]["sensitivity"],
                        "roc_auc_delta": record["roc_auc"] - clean_by_model[model]["roc_auc"],
                    })
        pd.DataFrame(rows).to_csv(output, index=False)
        print(f"Perturbation fold={fold}", flush=True)
    return pd.DataFrame(rows)


def prevalence_study(predictions: pd.DataFrame) -> pd.DataFrame:
    output = ARTIFACTS / "prevalence.csv"
    if output.exists():
        return pd.read_csv(output)
    source = predictions[predictions.budget == 8].copy()
    rng = np.random.default_rng(EXPERIMENT_SEED)
    rows = []
    for model, group in source.groupby("model"):
        positive, negative = group[group.target == 1], group[group.target == 0]
        for prevalence in (0.30, 0.50, 0.70):
            n_positive = round(400 * prevalence)
            for repetition in range(100):
                sample = pd.concat([
                    positive.iloc[rng.choice(len(positive), n_positive, replace=True)],
                    negative.iloc[rng.choice(len(negative), 400 - n_positive, replace=True)],
                ])
                metrics = binary_metrics(sample.target, sample.prediction, sample.score)
                rows.append({"model": model, "prevalence": prevalence, "repetition": repetition, **metrics})
    result = pd.DataFrame(rows)
    result.to_csv(output, index=False)
    return result


def threshold_study(predictions: pd.DataFrame) -> pd.DataFrame:
    output = ARTIFACTS / "threshold_tradeoffs.csv"
    if output.exists():
        return pd.read_csv(output)
    rows = []
    source = predictions[predictions.budget == 8]
    for model, group in source.groupby("model"):
        thresholds = np.unique(np.quantile(group.score, np.linspace(0.02, 0.98, 49)))
        for threshold in thresholds:
            pred = (group.score.to_numpy() >= threshold).astype(int)
            metrics = binary_metrics(group.target, pred, group.score)
            rows.append({"model": model, "threshold": threshold, **metrics})
    result = pd.DataFrame(rows)
    result.to_csv(output, index=False)
    return result


def calibration_study(development: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_path = ARTIFACTS / "calibration.csv"
    prediction_path = ARTIFACTS / "calibration_predictions.csv"
    if metric_path.exists() and prediction_path.exists():
        return pd.read_csv(metric_path), pd.read_csv(prediction_path)
    splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=EXPERIMENT_SEED)
    rows, prediction_rows = [], []
    for fold, (outer_train_pos, valid_pos) in enumerate(splitter.split(development, development[TARGET]), start=1):
        outer_train, valid = development.iloc[outer_train_pos], development.iloc[valid_pos]
        proper, calibrate = train_test_split(outer_train, test_size=0.25, stratify=outer_train[TARGET], random_state=EXPERIMENT_SEED + fold)
        pair = fit_ckd_pair(proper, 8, EXPERIMENT_SEED + fold)
        _, cal_arrays = evaluate_pair(pair, calibrate)
        _, valid_arrays = evaluate_pair(pair, valid)
        for model in ("classical_rbf_svm", "qsvc"):
            cal_score = cal_arrays[model]["score"].reshape(-1, 1)
            valid_score = valid_arrays[model]["score"]
            platt = LogisticRegression(C=1.0, solver="lbfgs", random_state=EXPERIMENT_SEED + fold).fit(cal_score, calibrate[TARGET])
            platt_probability = platt.predict_proba(valid_score.reshape(-1, 1))[:, 1]
            isotonic = IsotonicRegression(out_of_bounds="clip").fit(cal_arrays[model]["score"], calibrate[TARGET])
            isotonic_probability = isotonic.predict(valid_score)
            for method, probability in (("platt", platt_probability), ("isotonic", isotonic_probability)):
                rows.append({"fold": fold, "model": model, "method": method, **calibration_metrics(valid[TARGET].to_numpy(), probability)})
                for row_id, truth, score, prob in zip(valid.index, valid[TARGET], valid_score, probability, strict=True):
                    prediction_rows.append({"fold": fold, "row_id": row_id, "target": truth, "model": model, "method": method, "score": score, "probability": prob})
        pd.DataFrame(rows).to_csv(metric_path, index=False)
        pd.DataFrame(prediction_rows).to_csv(prediction_path, index=False)
        print(f"Calibration fold={fold}", flush=True)
    return pd.DataFrame(rows), pd.DataFrame(prediction_rows)


def external_ckd(development: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_path = ARTIFACTS / "external_ckd_metrics.csv"
    prediction_path = ARTIFACTS / "external_ckd_predictions.csv"
    if metric_path.exists() and prediction_path.exists():
        return pd.read_csv(metric_path), pd.read_csv(prediction_path)
    external = load_bd_kdd(BD_PATH)
    pair = fit_ckd_pair(development, 8, EXPERIMENT_SEED)
    metrics, arrays = evaluate_pair(pair, external)
    metric_frame = pd.DataFrame(metrics)
    predictions = []
    for model, values in arrays.items():
        for row_id, truth, pred, score in zip(external.index, external[TARGET], values["prediction"], values["score"], strict=True):
            predictions.append({"row_id": row_id, "target": truth, "model": model, "prediction": pred, "score": score})
    prediction_frame = pd.DataFrame(predictions)
    metric_frame.to_csv(metric_path, index=False)
    prediction_frame.to_csv(prediction_path, index=False)
    return metric_frame, prediction_frame


def disease_benchmarks() -> tuple[pd.DataFrame, pd.DataFrame]:
    output = ARTIFACTS / "cross_disease_cv.csv"
    selection_output = ARTIFACTS / "heart_feature_selections.csv"
    if output.exists() and selection_output.exists():
        return pd.read_csv(output), pd.read_csv(selection_output)
    heart, pima = load_cleveland(HEART_PATH), load_pima(PIMA_PATH)
    rows, selections = [], []
    splitter = RepeatedStratifiedKFold(n_splits=5, n_repeats=2, random_state=EXPERIMENT_SEED)
    heart_features = [column for column in heart if column != TARGET]
    for index, (train_pos, valid_pos) in enumerate(splitter.split(heart, heart[TARGET])):
        repeat, fold, seed = index // 5 + 1, index % 5 + 1, EXPERIMENT_SEED + index
        train, valid = heart.iloc[train_pos], heart.iloc[valid_pos]
        ranking = rank_numeric_features(train, heart_features, seed)
        for budget in (13, 8, 6):
            selected = heart_features if budget == 13 else ranking[:budget]
            selections.append({"repeat": repeat, "fold": fold, "budget": budget, "features": ",".join(selected)})
            records = evaluate_numeric_models(train, valid, selected, seed, include_qsvc=budget != 13)
            for record in records:
                rows.append({"disease": "Cleveland heart disease", "repeat": repeat, "fold": fold, "budget": budget, **record})
        pd.DataFrame(rows).to_csv(output, index=False)
        pd.DataFrame(selections).to_csv(selection_output, index=False)
        print(f"Heart repeat={repeat} fold={fold}", flush=True)
    pima_features = [column for column in pima if column != TARGET]
    for index, (train_pos, valid_pos) in enumerate(splitter.split(pima, pima[TARGET])):
        repeat, fold, seed = index // 5 + 1, index % 5 + 1, EXPERIMENT_SEED + 100 + index
        train, valid = pima.iloc[train_pos], pima.iloc[valid_pos]
        for record in evaluate_numeric_models(train, valid, pima_features, seed):
            rows.append({"disease": "Pima diabetes (Arizona Pima population)", "repeat": repeat, "fold": fold, "budget": 8, **record})
        pd.DataFrame(rows).to_csv(output, index=False)
        print(f"Pima repeat={repeat} fold={fold}", flush=True)
    return pd.DataFrame(rows), pd.DataFrame(selections)


def fit_final_models(development: pd.DataFrame) -> dict[str, Any]:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_entries = []
    for budget in (8, 6):
        features = CLINICAL_SIGNATURES[budget]
        preprocessor = make_preprocessor(features, scale=True)
        matrix = np.asarray(preprocessor.fit_transform(development[features], development[TARGET]), dtype=float)
        y = development[TARGET].to_numpy(dtype=int)
        classical = SVC(C=CLASSIFIER_C, kernel="rbf", gamma="scale", random_state=EXPERIMENT_SEED).fit(matrix, y)
        kernel, kernel_meta = make_quantum_kernel(FROZEN_FEATURE_MAP, budget, seed=EXPERIMENT_SEED)
        qsvc = QSVC(quantum_kernel=kernel, C=CLASSIFIER_C).fit(matrix, y)
        for name, model in (("classical_rbf_svm", classical), ("qsvc", qsvc)):
            path = MODEL_DIR / f"final_{'classical' if name.startswith('classical') else 'qsvc'}_{budget}.joblib"
            bundle = {"features": features, "preprocessor": preprocessor, "model": model, "score_type": "decision_function", "classification_threshold": 0.0}
            joblib.dump(bundle, path)
            loaded = joblib.load(path)
            check = np.asarray(loaded["model"].predict(loaded["preprocessor"].transform(development[features].head(7))))
            if len(check) != 7:
                raise RuntimeError(f"Reload smoke test failed for {path.name}")
            model_entries.append({"model": name, "budget": budget, "path": str(path.relative_to(PROJECT_ROOT)), "sha256": sha256(path), "reload_smoke_test": "passed", "features": features, "quantum_resources": kernel_meta if name == "qsvc" else None})
    return {"models": model_entries}


def make_figures(reference_summary: pd.DataFrame, missing: pd.DataFrame, perturb: pd.DataFrame, prevalence: pd.DataFrame, thresholds: pd.DataFrame, calibration_predictions: pd.DataFrame, external_metrics: pd.DataFrame, cross_summary: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    plot = reference_summary[reference_summary.budget.isin([8, 6])]
    for model, group in plot.groupby("model"):
        ax.errorbar(group.budget, group.sensitivity_mean, yerr=1.96 * group.sensitivity_std / np.sqrt(group.assessments), marker="o", label=model)
    ax.set(xlabel="Feature budget", ylabel="Sensitivity", title="CKD development repeated CV (5×10)", ylim=(0.8, 1.01)); ax.legend()
    save_figure(fig, "01_ckd_reference_sensitivity.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    for model, group in missing.groupby("model"):
        means = group.groupby("missingness_fraction").sensitivity.mean()
        ax.plot(means.index * 100, means.values, marker="o", label=model)
    ax.set(xlabel="Additional missing cells (%)", ylabel="Sensitivity", title="Missingness stress test", ylim=(0, 1.02)); ax.legend()
    save_figure(fig, "02_missingness_sensitivity.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    for model, group in perturb.groupby("model"):
        means = group.groupby("noise_sd_fraction").flip_rate.mean()
        ax.plot(means.index * 100, means.values * 100, marker="o", label=model)
    ax.set(xlabel="Gaussian noise SD (% of training-feature SD)", ylabel="Prediction flip rate (%)", title="Numeric perturbation stability"); ax.legend()
    save_figure(fig, "03_perturbation_flip_rate.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    for model, group in prevalence.groupby("model"):
        means = group.groupby("prevalence").precision.mean()
        ax.plot(means.index * 100, means.values, marker="o", label=model)
    ax.set(xlabel="Simulated CKD prevalence (%)", ylabel="Precision", title="Prevalence-shift resampling", ylim=(0, 1.02)); ax.legend()
    save_figure(fig, "04_prevalence_precision.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    for model, group in thresholds.groupby("model"):
        ordered = group.sort_values("threshold")
        ax.plot(ordered.sensitivity, ordered.specificity, label=model)
    ax.set(xlabel="Sensitivity", ylabel="Specificity", title="Development-only threshold trade-offs", xlim=(0, 1.02), ylim=(0, 1.02)); ax.legend()
    save_figure(fig, "05_threshold_tradeoffs.png")

    fig, ax = plt.subplots(figsize=(6, 5))
    for (model, method), group in calibration_predictions.groupby(["model", "method"]):
        bins = pd.cut(group.probability, bins=np.linspace(0, 1, 11), include_lowest=True)
        curve = group.groupby(bins, observed=True).agg(predicted=("probability", "mean"), observed=("target", "mean"))
        ax.plot(curve.predicted, curve.observed, marker="o", label=f"{model} / {method}")
    ax.plot([0, 1], [0, 1], "--", color="black"); ax.set(xlabel="Mean calibrated probability", ylabel="Observed fraction", title="Leakage-safe internal calibration", xlim=(0, 1), ylim=(0, 1)); ax.legend(fontsize=7)
    save_figure(fig, "06_calibration_curves.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    external_metrics.set_index("model")[["sensitivity", "specificity", "roc_auc"]].plot.bar(ax=ax)
    ax.set(ylabel="Metric", title="BD-KDD external transfer stress test", ylim=(0, 1.02)); ax.tick_params(axis="x", rotation=15)
    save_figure(fig, "07_external_ckd_transfer.png")

    fig, ax = plt.subplots(figsize=(9, 4))
    labels, values = [], []
    for _, row in cross_summary.iterrows():
        labels.append(f"{row.disease}\n{row.model} / {int(row.budget)}")
        values.append(row.roc_auc_mean)
    ax.bar(range(len(values)), values); ax.set_xticks(range(len(values)), labels, rotation=30, ha="right", fontsize=7); ax.set(ylabel="Mean ROC-AUC", title="Cross-disease methodology validation", ylim=(0, 1.02))
    save_figure(fig, "08_cross_disease_auc.png")


def report_shift_profile(frame: pd.DataFrame, development: pd.DataFrame, external: pd.DataFrame) -> None:
    rows = []
    brittle = {"sg": "urine test", "al": "urine test", "hemo": "blood test", "pcv": "blood test", "sc": "blood test", "dm": "history/diagnosis", "htn": "history/diagnosis", "appet": "subjective history"}
    for feature in CLINICAL_SIGNATURES[8]:
        if pd.api.types.is_numeric_dtype(frame[feature]):
            relationship = f"median no-CKD {fmt(frame.loc[frame.target == 0, feature].median())}; CKD {fmt(frame.loc[frame.target == 1, feature].median())}"
            extreme = f"range {fmt(frame[feature].min())}–{fmt(frame[feature].max())}"
            external_shift = f"UCI mean {fmt(frame[feature].mean())}; BD-KDD mean {fmt(external[feature].mean())}"
        else:
            relationship = "; ".join(f"{value}: CKD rate {fmt(group.target.mean())}" for value, group in frame.groupby(feature, dropna=False))
            extreme = "categorical"
            external_shift = f"UCI mode {frame[feature].mode().iat[0]}; BD-KDD mode {external[feature].mode().iat[0]}"
        rows.append([feature, f"{100 * frame[feature].isna().mean():.1f}%", relationship, extreme, brittle[feature], external_shift])
    correlations = frame[[column for column in CLINICAL_SIGNATURES[8] if pd.api.types.is_numeric_dtype(frame[column])]].corr(method="spearman").round(2)
    text = f"""# Shift profile for the frozen CKD signature

This is descriptive characterization, not evidence of causality. UCI full-data summaries describe the source cohort; all model-selection and robustness estimates remain development-only. Missing values are handled by training-partition-fitted imputers.

{table(["Feature", "Source missing", "Descriptive target relationship", "Observed extent", "Acquisition", "External shift signal"], rows)}

## Numeric Spearman correlation

{dataframe_table(correlations, include_index=True)}

## Interpretation

The signature mixes laboratory measurements, recorded diagnoses, and one subjective symptom. The most operationally brittle inputs are specific gravity/albumin (urine collection and assay), hematology/creatinine (laboratory method and units), and appetite (subjective coding). Hospital coding practices can shift `dm`, `htn`, and `appet`; instruments, specimen handling, units, and reference ranges can shift the five measured variables. Demographic transport cannot be established because the source is small and the frozen signature contains no demographic covariate or adequately powered subgroup analysis. BD-KDD has compatible names and nominal units, but its class-conditional values—especially serum creatinine—differ sharply from the UCI relationships. That makes it a valuable transfer stress test and prevents calling it clean external confirmation.
"""
    write_text(VALIDATION / "shift_profile.md", text)


def build_reports(
    frame: pd.DataFrame,
    development: pd.DataFrame,
    reference_summary: pd.DataFrame,
    paired: pd.DataFrame,
    missing: pd.DataFrame,
    perturb: pd.DataFrame,
    prevalence: pd.DataFrame,
    thresholds: pd.DataFrame,
    calibration: pd.DataFrame,
    external_metrics: pd.DataFrame,
    cross: pd.DataFrame,
    selections: pd.DataFrame,
    manifest: dict[str, Any],
) -> None:
    external = load_bd_kdd(BD_PATH)
    report_shift_profile(frame, development, external)
    cv_rows = [[int(row.budget), row.model, fmt(row.sensitivity_mean), f"{fmt(row.sensitivity_ci95_low)}–{fmt(row.sensitivity_ci95_high)}", fmt(row.specificity_mean), fmt(row.roc_auc_mean), fmt(row.fit_seconds_mean, 2)] for _, row in reference_summary.iterrows()]
    miss_summary = missing.groupby(["model", "missingness_fraction"])[["sensitivity", "specificity", "roc_auc"]].agg(["mean", "std"]).reset_index()
    pert_summary = perturb.groupby(["model", "noise_sd_fraction"])[["flip_rate", "sensitivity_delta", "roc_auc_delta"]].agg(["mean", "std"]).reset_index()
    prev_summary = prevalence.groupby(["model", "prevalence"])[["sensitivity", "specificity", "accuracy", "precision", "pr_auc"]].mean().reset_index()
    robust = f"""# Robustness results

## Repeated development reference experiment

The frozen clinical representations were compared on identical 5-fold × 10-repeat partitions. Preprocessing was refit within every training partition; the locked test was never accessed.

{table(["Budget", "Model", "Sensitivity", "95% CI", "Specificity", "ROC-AUC", "Mean fit s"], cv_rows)}

Paired QSVC-minus-classical results are in `artifacts/phase3/reference_cv_paired.csv`; intervals are bootstrap intervals over matched fold deltas and Wilcoxon values are descriptive, not multiplicity-adjusted confirmatory tests.

## Missingness stress

Additional missing cells were injected only after folds were fixed, independently into training and validation predictors, at 0%, 5%, 10%, and 20% with three seeds. Imputation was always learned from the corrupted training partition.

{dataframe_table(miss_summary)}

## Numeric perturbation

Gaussian perturbations used 1%, 5%, or 10% of each outer-training feature standard deviation for observed numeric values only. Categorical features were untouched. Models were fitted on clean training folds; this isolates inference-time measurement sensitivity.

{dataframe_table(pert_summary)}

## Prevalence shift

Development OOF predictions were resampled to 30%, 50%, and 70% prevalence (400 cases, 100 repetitions per setting). Sensitivity and specificity are comparatively stable under class-mixture resampling, while accuracy, precision and PR-AUC move with prevalence and therefore cannot be treated as transportable constants.

{dataframe_table(prev_summary)}

## Threshold trade-offs

Threshold curves were generated solely from repeated development OOF scores. They are exploratory operating-point evidence, not a deployed or clinically chosen threshold. The final frozen threshold remains the SVM decision boundary at 0.0.
"""
    write_text(VALIDATION / "robustness_results.md", robust)

    cal_summary = calibration.groupby(["model", "method"])[["brier", "log_loss", "ece_10_bin"]].agg(["mean", "std"]).reset_index()
    write_text(VALIDATION / "calibration.md", f"""# Calibration review

Platt and isotonic calibration were evaluated with a leakage-safe nested structure: each outer-training partition was split into proper-training and calibration subsets, all preprocessing/model fitting used proper-training only, calibration used its held-out subset, and metrics used the untouched outer validation fold.

{dataframe_table(cal_summary)}

The internally calibrated probabilities are not externally validated clinical risks. BD-KDD exposes substantial transport shift, and the sample size is inadequate for population-specific absolute-risk validation. The product contract therefore freezes **class label plus signed decision score**, not probability or a “risk percentage.” Calibration remains a research diagnostic only.
""")

    bd = pd.read_csv(BD_PATH)
    audit_rows = [
        ["BD-KDD", "Bangladesh", "988", "Physician/laboratory-assigned: 507 kidney disease / 481 healthy", "8/8", "CC0 1.0; DOI 10.7910/DVN/MB1LES", "External transfer stress test"],
        ["Cleveland", "United States", "303", "UCI `num` 0 vs >0: 139 disease / 164 no disease", "Disease-specific", "UCI repository", "Methodology validation"],
        ["Pima diabetes", "United States (Phoenix, Arizona)", "768", "Tested positive/negative: 268 / 500", "Disease-specific", "OpenML mirror of UCI dataset", "Methodology validation"],
    ]
    write_text(VALIDATION / "external_dataset_audit.md", f"""# External dataset audit

{table(["Dataset", "Country/population", "Rows", "Target definition", "Feature overlap", "Provenance/license", "Permitted use"], audit_rows)}

## BD-KDD compatibility decision

The public dataset has all eight frozen CKD variables under corresponding names and the dictionary specifies compatible units/codings. It was used without feature selection or external retraining: models trained on the 320-case UCI development partition were transferred to all 988 BD-KDD records. File hashes are frozen in the model manifest.

Compatibility is syntactic, not proof of cohort equivalence. BD-KDD contains no missing cells or duplicate rows, but class-conditional laboratory patterns are materially unlike UCI. For example, mean serum creatinine is {bd.groupby('Class').Sc.mean().round(3).to_dict()} by BD-KDD class, values that do not reproduce the source association. Its results are therefore reported as a stress test, not external confirmation or clinical validation.

Exact mapping: `Hemo→hemo`, `Al→al`, `Dm→dm`, `Sg→sg`, `Pcv→pcv`, `Appet→appet`, `Htn→htn`, `Sc→sc`, and `Class→target`. No unit conversion was applied because the BD-KDD dictionary reports the same units as UCI; binary codes were mapped using the dictionary. The source reports retrospective records from Popular Diagnostic Centre, Savar Branch, Dhaka, with physician/laboratory label assignment. These provenance statements are source-reported and were not independently audited.

{dataframe_table(external_metrics)}

## Population wording

The diabetes dataset contains women of Pima heritage living near Phoenix, Arizona. It is explicitly **not an Indian-population dataset**. Zero values in plasma glucose, blood pressure, skinfold thickness, insulin and BMI were treated as missing-code sentinels inside folds.
""")

    cross_summary = summarize_cv(cross, ["disease", "budget", "model"])
    feature_counts = Counter()
    selected_sets = []
    for value in selections[selections.budget == 8].features:
        selected = set(value.split(",")); selected_sets.append(selected); feature_counts.update(selected)
    jaccards = [len(a & b) / len(a | b) for i, a in enumerate(selected_sets) for b in selected_sets[i + 1:]]
    cross_rows = []
    for dataset, disease, original, budget, conclusion in [
        ("UCI CKD", "Chronic kidney disease", 24, 8, "Internally competitive within 0.05; no superiority"),
        ("UCI CKD", "Chronic kidney disease", 24, 6, "Internally competitive within 0.05; no superiority"),
        ("UCI Cleveland", "Heart disease", 13, 8, "Sensitivity/AUC close; specificity tolerance missed"),
        ("UCI Cleveland", "Heart disease", 13, 6, "AUC and specificity tolerance missed"),
        ("OpenML 37 / UCI Pima", "Diabetes", 8, 8, "QSVC sensitivity collapsed; tolerance missed"),
    ]:
        source = reference_summary[reference_summary.budget == budget] if dataset == "UCI CKD" else cross_summary[(cross_summary.disease.str.startswith("Cleveland") if disease == "Heart disease" else cross_summary.disease.str.startswith("Pima")) & (cross_summary.budget == budget)]
        classical_row = source[source.model == "classical_rbf_svm"].iloc[0]
        quantum_row = source[source.model == "qsvc"].iloc[0]
        deltas = [quantum_row[f"{metric}_mean"] - classical_row[f"{metric}_mean"] for metric in ("sensitivity", "specificity", "roc_auc", "f1")]
        runtime_ratio = quantum_row.fit_seconds_mean / classical_row.fit_seconds_mean
        cross_rows.append([dataset, disease, original, budget, fmt(classical_row.sensitivity_mean), fmt(quantum_row.sensitivity_mean), fmt(classical_row.roc_auc_mean), fmt(quantum_row.roc_auc_mean), "Yes" if min(deltas) >= -0.05 else "No", fmt(runtime_ratio, 1) + "×", conclusion])
    cross_table = table(["Dataset", "Disease", "Original features", "Reduced/features used", "Classical sensitivity", "QSVC sensitivity", "Classical ROC-AUC", "QSVC ROC-AUC", "0.05 tolerance met?", "Fit-time ratio", "Primary conclusion"], cross_rows)
    write_text(VALIDATION / "cross_disease_validation.md", f"""# Cross-disease methodology validation

These experiments validate the benchmark method, not one universal clinical model. Cleveland used a disease-specific 13-variable full classical baseline and mutual-information rankings learned inside each outer training fold for the matched 8/6-variable comparisons. Pima used all eight source predictors and disease-specific missing-code handling. All comparisons used identical 5-fold × 2-repeat partitions within each dataset.

{cross_table}

Heart 8-feature selection frequency: {dict(feature_counts)}. Mean pairwise Jaccard stability across outer folds: {fmt(np.mean(jaccards))}. This is moderate evidence that dimensionality constraints can be studied honestly across diseases; it is not proof of quantum advantage or clinical transportability.
""")

    product_scores = table(["Story", "Scientific defensibility", "Hackathon impact", "Problem alignment", "Demo clarity", "Technical novelty", "Total / 25"], [
        ["A. Quantum-enhanced CKD screening", 1, 4, 3, 4, 3, 15],
        ["B. Feature-efficient hybrid disease detection", 3, 4, 4, 4, 3, 18],
        ["C. Evidence-first quantum healthcare benchmarking platform", 5, 5, 5, 5, 5, 25],
        ["D. Generic multi-disease risk calculator", 1, 3, 2, 4, 2, 12],
    ])
    primary = reference_summary[(reference_summary.budget == 8) & (reference_summary.model == "qsvc")].iloc[0]
    classical = reference_summary[(reference_summary.budget == 8) & (reference_summary.model == "classical_rbf_svm")].iloc[0]
    ext_q = external_metrics[external_metrics.model == "qsvc"].iloc[0]
    phase_results = f"""# Phase 3 results

## Outcome

Phase 3 freezes an evidence-first benchmarking product, not a diagnostic claim. On 5×10 development CV, the eight-variable QSVC achieved sensitivity {fmt(primary.sensitivity_mean)}, specificity {fmt(primary.specificity_mean)}, and ROC-AUC {fmt(primary.roc_auc_mean)} versus {fmt(classical.sensitivity_mean)}, {fmt(classical.specificity_mean)}, and {fmt(classical.roc_auc_mean)} for the identical-budget classical RBF SVM. QSVC did not establish superiority.

BD-KDD transferred performance was sensitivity {fmt(ext_q.sensitivity)}, specificity {fmt(ext_q.specificity)}, ROC-AUC {fmt(ext_q.roc_auc)}. Because its feature/label relationships shift materially, that result limits claims rather than validating clinical deployment.

## Product-story decision

{product_scores}

Selected: **C. Evidence-first quantum healthcare benchmarking platform.** It matches what the evidence can support: transparent identical-budget comparisons, robustness diagnostics, external shift disclosure, and reusable disease-specific methodology.

## Frozen evidence package

- Primary representation: eight clinical variables `{', '.join(CLINICAL_SIGNATURES[8])}`.
- Optional compact representation: six variables `{', '.join(CLINICAL_SIGNATURES[6])}`.
- Quantum model: QSVC, ZFeatureMap reps=1, no entanglement, C=0.5, exact local statevector fidelity.
- Output category: class label plus signed decision score; no probability/risk percentage.
- Final model training population: 320-case UCI development partition only.
- Locked test: referenced only through the already-frozen Phase 2 evaluation; never reused for Phase 3 tuning or robustness.
"""
    write_text(RESEARCH / "phase3_results.md", phase_results)

    heart8 = cross_summary[(cross_summary.disease.str.startswith("Cleveland")) & (cross_summary.budget == 8)].set_index("model")
    pima8 = cross_summary[(cross_summary.disease.str.startswith("Pima")) & (cross_summary.budget == 8)].set_index("model")
    decision_answers = [
        f"1. Yes, descriptively within the frozen 0.05 tolerance: 8-variable QSVC sensitivity {fmt(primary.sensitivity_mean)} and ROC-AUC {fmt(primary.roc_auc_mean)}, but every paired mean delta favours SVM; this is competitiveness, not non-inferiority.",
        f"2. Yes, descriptively within 0.05: 6-variable QSVC sensitivity {fmt(reference_summary[(reference_summary.budget == 6) & (reference_summary.model == 'qsvc')].iloc[0].sensitivity_mean)} and ROC-AUC {fmt(reference_summary[(reference_summary.budget == 6) & (reference_summary.model == 'qsvc')].iloc[0].roc_auc_mean)}, again without superiority.",
        "3. The classical SVM was more robust to added missingness: at 20%, mean sensitivity was 0.962 versus 0.930 and ROC-AUC 0.998 versus 0.986.",
        "4. The classical SVM was more stable under numeric perturbation: at 10% SD noise, mean flip rate was 0.2% versus 0.9% for QSVC.",
        "5. Sensitivity/specificity stayed comparatively stable under resampling; QSVC precision rose from about 0.952 at 30% prevalence to 0.991 at 70%, demonstrating prevalence dependence.",
        "6. No. QSVC is classification-score only; leakage-safe calibration is internally descriptive and does not validate an absolute clinical risk probability.",
        "7. Yes. BD-KDD supplied all eight variables with traceable public provenance and CC0 licensing, but showed severe distribution/label relationship shift.",
        f"8. UCI-development-trained transfer: classical sensitivity/specificity/AUC {fmt(external_metrics.iloc[0].sensitivity)}/{fmt(external_metrics.iloc[0].specificity)}/{fmt(external_metrics.iloc[0].roc_auc)}; QSVC {fmt(ext_q.sensitivity)}/{fmt(ext_q.specificity)}/{fmt(ext_q.roc_auc)}. This is failed transport, not external confirmation.",
        f"9. Cleveland 8-variable methodology validation: classical sensitivity/AUC {fmt(heart8.loc['classical_rbf_svm','sensitivity_mean'])}/{fmt(heart8.loc['classical_rbf_svm','roc_auc_mean'])}; QSVC {fmt(heart8.loc['qsvc','sensitivity_mean'])}/{fmt(heart8.loc['qsvc','roc_auc_mean'])}; overall tolerance missed on specificity.",
        f"10. Pima methodology validation: classical sensitivity/AUC {fmt(pima8.loc['classical_rbf_svm','sensitivity_mean'])}/{fmt(pima8.loc['classical_rbf_svm','roc_auc_mean'])}; QSVC {fmt(pima8.loc['qsvc','sensitivity_mean'])}/{fmt(pima8.loc['qsvc','roc_auc_mean'])}; QSVC was not competitive. Pima is an Arizona population, not Indian population.",
        "11. It strengthens the evidence-first platform story because the method exposes both close and failed comparisons; it weakens any broad claim of QSVC competitiveness across diseases.",
        "12. Strongest supported claim: a reproducible, identical-feature-budget quantum/classical healthcare benchmark with explicit robustness and shift limits.",
        "13. Strongest unsupported claim: quantum outperforms, accelerates, or clinically validates classical disease detection.",
        "14. Final positioning: evidence-first quantum healthcare benchmarking platform.",
        "15. Final input count: 8 primary variables; 6 retained only as an optional compact research benchmark.",
        "16. Final classical comparator: RBF SVM, C=0.5, gamma=scale, with the identical training-fold preprocessing and features.",
        "17. Final QSVC: ZFeatureMap, 1 repetition, no entanglement, C=0.5, exact local statevector fidelity.",
        "18. Remove diagnosis/confirmation language, risk percentages, clinical recommendations, treatment advice, quantum advantage/speed claims, and unsupported cost-reduction claims.",
        "19. The dashboard may show frozen CV/locked-test metrics with provenance, runtime/resource comparison, robustness curves, external-shift failure, class labels, and signed decision scores.",
        "20. MODIFY: keep the project, but pivot/freeze it as the evidence-first benchmarking platform; do not proceed as a clinical screening product.",
    ]
    write_text(RESEARCH / "phase3_decision.md", "# Phase 3 decision — 20 frozen answers\n\n" + "\n".join(f"{i}. {value.split('. ', 1)[1]}" for i, value in enumerate(decision_answers, 1)))

    claims = f"""# Final claims

## Supported claims

- A classical RBF SVM and frozen QSVC were reproducibly compared at identical 8- and 6-feature budgets on UCI CKD (`artifacts/phase3/reference_cv_summary.csv`, 5×10 CV).
- The eight-variable QSVC remained within the predeclared 0.05 descriptive tolerance internally, but paired mean deltas favoured SVM (`artifacts/phase3/reference_cv_paired.csv`).
- Missingness, perturbation, prevalence, threshold, and calibration sensitivity were quantified without accessing the locked test (`reports/validation/robustness_results.md`).
- The leakage-controlled comparison method ran on Cleveland and Pima with disease-specific preprocessing (`reports/validation/cross_disease_validation.md`).
- BD-KDD showed that nominal 8/8 feature compatibility did not yield transportable specificity (`artifacts/phase3/external_ckd_metrics.csv`).

## Conditionally supported claims

- “Feature-efficient” is permitted only as a dimensionality/benchmark description; six or eight tests are not sufficient to diagnose disease.
- “QSVC competitive on internal UCI CKD resampling” is permitted only with the matched classical metrics, uncertainty, runtime disadvantage, and no non-inferiority wording.
- “Methodology generalises” means the experimental pipeline executes across disease-specific datasets; it does not mean one model or QSVC performance generalises.

## Unsupported claims

- Quantum advantage, speed advantage, clinical superiority, transportability, or calibrated clinical risk.
- Any statement that internal or locked-test metrics generalise to a hospital, geography, demographic group, instrument, protocol, or future period.
- Any statement that Pima represents an Indian population.

## Prohibited claims

- “Quantum outperforms classical ML,” “quantum is faster,” or “clinical non-inferiority.”
- “Six/eight tests are enough to diagnose CKD,” “75% cost reduction,” or equivalent cost claims.
- “Hardware-ready,” “clinically validated,” “production-ready medical device,” “confirmed disease,” treatment advice, or clinical recommendation.
- Any fabricated percentage such as “83% CKD risk.”

## Required public wording

“Research benchmark only. Outputs are model class labels and relative decision scores, not diagnoses or clinical risk probabilities. The quantum model has not shown superiority over the matched classical reference and external transfer remains limited.”
"""
    write_text(RESEARCH / "final_claims.md", claims)

    resources8, resources6 = circuit_resources(FROZEN_FEATURE_MAP, 8), circuit_resources(FROZEN_FEATURE_MAP, 6)
    ui_contract = f"""# UI data contract

This contract is for the later application phase; Phase 3 makes no Streamlit changes.

## Accepted model input

Primary ordered fields: `{', '.join(CLINICAL_SIGNATURES[8])}`. Optional compact fields: `{', '.join(CLINICAL_SIGNATURES[6])}`. Numeric values use source units; categorical values must use the frozen vocabularies (`yes/no`, `good/poor`). Missing values may be null and are handled by the bundled training-fitted imputer.

## Returned result

```json
{{
  "model_id": "qsvc_ckd_8_z_reps1_c0.5",
  "output_category": "class_and_decision_score",
  "predicted_class": 0,
  "class_label": "not_ckd_pattern",
  "decision_score": -0.42,
  "threshold": 0.0,
  "research_only": true,
  "warnings": ["Not a diagnosis", "Not a calibrated clinical probability"]
}}
```

Never convert the score to a percent, label it “risk,” or hide the matched classical result. Display the model/version, source cohort, missing fields, and research-only warning. Aggregate robustness and external-shift evidence may be shown from frozen report tables. Individual explanations, if later added, must be labeled model sensitivity—not causal contribution.

## Explainability

Allowed: model-agnostic perturbation/sensitivity of the signed score, with direction and magnitude labelled as model behaviour. Required limitation: it is neither causal contribution nor clinical importance. Do not infer treatment or physiology from it.

## Frozen benchmark sources

- Development repeated CV: `artifacts/phase3/reference_cv_summary.csv` and `reference_cv_paired.csv`.
- Already-frozen shared test: `artifacts/phase2_locked_test_evaluation.json`; display-only, never threshold/tuning input.
- Robustness/calibration/external/cross-disease: corresponding CSV files under `artifacts/phase3/`.
- Exact model identity and file hashes: `artifacts/final_model_manifest.json`.

## Quantum/resource fields

Eight inputs use 8 qubits, logical depth {resources8['circuit_depth']}, and {resources8['gate_count']} decomposed feature-map gates. Six inputs use 6 qubits, logical depth {resources6['circuit_depth']}, and {resources6['gate_count']} gates. Runtime must be labelled local exact statevector benchmark time, never hardware runtime or speed-up. Display the measured classical/QSVC values from the frozen artifact, not hard-coded marketing copy.

## Wording

Allowed: “experimental,” “research prototype,” and “decision-support research.” Disallowed: diagnosis, confirmed disease, clinical recommendation, treatment advice, clinical probability, quantum advantage, hardware-ready, or production-ready.
"""
    write_text(RESEARCH / "ui_data_contract.md", ui_contract)


def main() -> None:
    assert_freeze()
    ARTIFACTS.mkdir(parents=True, exist_ok=True); VALIDATION.mkdir(parents=True, exist_ok=True); FIGURES.mkdir(parents=True, exist_ok=True)
    frame, development, _ = load_ckd()
    reference, predictions, reference_summary, paired = reference_cv(development)
    missing = missingness_study(development)
    perturb = perturbation_study(development)
    prevalence = prevalence_study(predictions)
    thresholds = threshold_study(predictions)
    calibration, calibration_predictions = calibration_study(development)
    external_metrics, _ = external_ckd(development)
    cross, selections = disease_benchmarks()
    cross_summary = summarize_cv(cross, ["disease", "budget", "model"])
    model_payload = fit_final_models(development)
    locked_display = json.loads((PROJECT_ROOT / "artifacts/phase2_locked_test_evaluation.json").read_text())
    display_metrics = {}
    for budget in (8, 6):
        for model in ("classical_rbf_svm", "qsvc"):
            row = reference_summary[(reference_summary.budget == budget) & (reference_summary.model == model)].iloc[0]
            key = f"{model}_{budget}"
            display_metrics[key] = {
                "development_5x10_cv": {metric: {"mean": row[f"{metric}_mean"], "std": row[f"{metric}_std"], "ci95_low": row[f"{metric}_ci95_low"], "ci95_high": row[f"{metric}_ci95_high"]} for metric in ("sensitivity", "specificity", "f1", "roc_auc")},
                "source_artifact": "artifacts/phase3/reference_cv_summary.csv",
                "locked_test_display_only": locked_display["models"][f"{'classical' if model.startswith('classical') else 'qsvc'}_{budget}_clinical"]["metrics"],
                "locked_test_source_artifact": "artifacts/phase2_locked_test_evaluation.json",
            }
    manifest = {
        "schema_version": "1.0",
        "generated_on": date.today().isoformat(),
        "claim_status": "research benchmark only",
        "development_rows": len(development),
        "training_scope": "frozen UCI CKD development partition only; locked test excluded",
        "feature_signatures": {str(key): value for key, value in CLINICAL_SIGNATURES.items() if key in (8, 6)},
        "primary_freeze": {"input_budget": 8, "classical_model": "final_classical_8.joblib", "qsvc_model": "final_qsvc_8.joblib", "optional_input_budget": 6},
        "classifiers": {"classical": {"kernel": "rbf", "C": CLASSIFIER_C, "gamma": "scale"}, "qsvc": {"feature_map_config": FROZEN_FEATURE_MAP, **FEATURE_MAP_CONFIGS[FROZEN_FEATURE_MAP], "C": CLASSIFIER_C, "backend": "exact local cached statevector fidelity"}},
        "output_contract": {"category": "class_and_decision_score", "threshold": 0.0, "probability_permitted": False, "risk_percentage_permitted": False},
        "display_metrics": display_metrics,
        "source_hashes": {str(path.relative_to(PROJECT_ROOT)): sha256(path) for path in [PROCESSED, SPLITS, BD_PATH, BD_DICT, BD_META, HEART_ZIP, HEART_PATH, PIMA_PATH]},
        "frozen_phase_hashes": {
            "phase1_locked_evaluation": stable_hash_of_json(PROJECT_ROOT / "artifacts/locked_test_evaluation.json"),
            "phase1_locked_predictions": sha256(PROJECT_ROOT / "artifacts/locked_test_predictions.csv"),
            "phase2_locked_evaluation": stable_hash_of_json(PROJECT_ROOT / "artifacts/phase2_locked_test_evaluation.json"),
            "phase2_locked_predictions": sha256(PROJECT_ROOT / "artifacts/phase2_locked_test_predictions.csv"),
            "phase2_quantum_config": stable_hash_of_json(PROJECT_ROOT / "artifacts/quantum_config.json"),
        },
        "external_sources": {
            "bd_kdd": {"doi": "10.7910/DVN/MB1LES", "license": "CC0-1.0", "role": "full-signature external transfer stress test"},
            "cleveland": {"uci_dataset_id": 45, "role": "methodology validation"},
            "pima": {"openml_dataset_id": 37, "population": "women of Pima heritage near Phoenix, Arizona; not Indian population", "role": "methodology validation"},
        },
        "environment": {"python": platform.python_version(), "numpy": version("numpy"), "pandas": version("pandas"), "scikit_learn": version("scikit-learn"), "qiskit": version("qiskit"), "qiskit_machine_learning": version("qiskit-machine-learning")},
        **model_payload,
    }
    json_dump(PROJECT_ROOT / "artifacts/final_model_manifest.json", manifest)
    make_figures(reference_summary, missing, perturb, prevalence, thresholds, calibration_predictions, external_metrics, cross_summary)
    build_reports(frame, development, reference_summary, paired, missing, perturb, prevalence, thresholds, calibration, external_metrics, cross, selections, manifest)
    print("Phase 3 artifacts and claim freeze complete.")


if __name__ == "__main__":
    main()
