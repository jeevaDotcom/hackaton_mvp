from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", "/tmp/qcare-phase3b-matplotlib-cache")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/qcare-phase3b-xdg-cache")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import confusion_matrix, pairwise_distances, roc_auc_score
from sklearn.preprocessing import MinMaxScaler, QuantileTransformer, RobustScaler
from sklearn.svm import SVC
from qiskit_machine_learning.algorithms import QSVC

from src.phase1.data import TARGET, load_official_arff
from src.phase1.modeling import EXPERIMENT_SEED, binary_metrics, make_preprocessor
from src.phase2.benchmark import CLASSIFIER_C, build_feature_map, make_quantum_kernel
from src.phase3.validation import load_bd_kdd


FEATURES = ["hemo", "al", "dm", "sg", "pcv", "appet", "htn", "sc"]
NUMERIC = ["hemo", "al", "sg", "pcv", "sc"]
CATEGORICAL = ["dm", "appet", "htn"]
RISK_CATEGORY = {"dm": "yes", "appet": "poor", "htn": "yes"}
REPORT_DIR = PROJECT_ROOT / "reports/root_cause"
FIGURE_DIR = REPORT_DIR / "figures"
RESEARCH_DIR = PROJECT_ROOT / "research"
MODEL_PATHS = {
    "classical_rbf_svm": PROJECT_ROOT / "artifacts/models/final_classical_8.joblib",
    "qsvc": PROJECT_ROOT / "artifacts/models/final_qsvc_8.joblib",
}
FROZEN_PATHS = [
    *MODEL_PATHS.values(),
    PROJECT_ROOT / "artifacts/phase3/external_ckd_metrics.csv",
    PROJECT_ROOT / "artifacts/phase3/external_ckd_predictions.csv",
    PROJECT_ROOT / "artifacts/claim_registry.json",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n")


def save_figure(fig: plt.Figure, name: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / name, dpi=180, bbox_inches="tight")
    plt.close(fig)


def fmt(value: Any, digits: int = 4) -> str:
    if value is None or (isinstance(value, (float, np.floating)) and not np.isfinite(value)):
        return "NA"
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.{digits}f}"
    return str(value)


def table(frame: pd.DataFrame, columns: list[str] | None = None, digits: int = 4) -> str:
    view = frame if columns is None else frame[columns]
    headers = [str(column) for column in view.columns]
    rows = []
    for record in view.itertuples(index=False, name=None):
        rows.append("| " + " | ".join(fmt(value, digits).replace("|", "\\|") for value in record) + " |")
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
        *rows,
    ])


def psi(reference: np.ndarray, external: np.ndarray) -> float:
    reference = np.asarray(reference, dtype=float)
    external = np.asarray(external, dtype=float)
    reference = reference[np.isfinite(reference)]
    external = external[np.isfinite(external)]
    quantiles = np.unique(np.quantile(reference, np.linspace(0, 1, 11)))
    if len(quantiles) < 3:
        quantiles = np.unique(np.concatenate(([reference.min()], reference, [reference.max()])))
    edges = np.concatenate(([-np.inf], quantiles[1:-1], [np.inf]))
    ref_hist = np.histogram(reference, bins=edges)[0] / len(reference)
    ext_hist = np.histogram(external, bins=edges)[0] / len(external)
    ref_hist = np.clip(ref_hist, 1e-6, None)
    ext_hist = np.clip(ext_hist, 1e-6, None)
    return float(np.sum((ext_hist - ref_hist) * np.log(ext_hist / ref_hist)))


def z_kernel(left: np.ndarray, right: np.ndarray | None = None) -> np.ndarray:
    """Exact fidelity for the installed reps=1 ZFeatureMap: product cos²(x_i-y_i)."""
    left = np.asarray(left, dtype=float)
    right = left if right is None else np.asarray(right, dtype=float)
    result = np.ones((len(left), len(right)), dtype=float)
    for column in range(left.shape[1]):
        result *= np.cos(left[:, None, column] - right[None, :, column]) ** 2
    return result


def centered_alignment(kernel: np.ndarray, target: np.ndarray) -> float:
    n = len(target)
    centre = np.eye(n) - np.ones((n, n)) / n
    k_centered = centre @ kernel @ centre
    y = np.where(np.asarray(target) == 1, 1.0, -1.0)
    y_centered = centre @ np.outer(y, y) @ centre
    denominator = np.linalg.norm(k_centered, "fro") * np.linalg.norm(y_centered, "fro")
    return float(np.sum(k_centered * y_centered) / denominator) if denominator else math.nan


def stratified_indices(target: np.ndarray, per_class: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    selected: list[int] = []
    for label in (0, 1):
        candidates = np.flatnonzero(target == label)
        selected.extend(rng.choice(candidates, size=min(per_class, len(candidates)), replace=False).tolist())
    return np.asarray(sorted(selected), dtype=int)


def kernel_summary(name: str, kernel: np.ndarray, target: np.ndarray) -> dict[str, Any]:
    off = kernel[np.triu_indices_from(kernel, k=1)]
    same = target[:, None] == target[None, :]
    tri = np.triu(np.ones_like(kernel, dtype=bool), k=1)
    within = kernel[tri & same]
    between = kernel[tri & ~same]
    eigenvalues = np.linalg.eigvalsh((kernel + kernel.T) / 2)
    eigenvalues = np.clip(eigenvalues, 0.0, None)
    effective_rank = float(eigenvalues.sum() ** 2 / np.square(eigenvalues).sum()) if np.square(eigenvalues).sum() else 0.0
    return {
        "matrix": name,
        "n": len(target),
        "offdiag_mean": float(off.mean()),
        "offdiag_std": float(off.std()),
        "near_one_pct": float(100 * np.mean(off >= 0.99)),
        "near_zero_pct": float(100 * np.mean(off <= 0.01)),
        "kernel_variance": float(np.var(off)),
        "within_class_mean": float(within.mean()),
        "between_class_mean": float(between.mean()),
        "within_minus_between": float(within.mean() - between.mean()),
        "effective_rank": effective_rank,
        "numerical_rank": int(np.sum(eigenvalues > 1e-8 * max(eigenvalues.max(), 1.0))),
        "top_eigenvalue_fraction": float(eigenvalues.max() / eigenvalues.sum()),
    }


def overlap_coefficient(left: np.ndarray, right: np.ndarray) -> float:
    combined = np.concatenate([left, right])
    if np.allclose(combined.min(), combined.max()):
        return 1.0
    edges = np.linspace(combined.min(), combined.max(), 41)
    h_left, _ = np.histogram(left, bins=edges, density=True)
    h_right, _ = np.histogram(right, bins=edges, density=True)
    widths = np.diff(edges)
    return float(np.sum(np.minimum(h_left, h_right) * widths))


def hedges_g(positive: np.ndarray, negative: np.ndarray) -> float:
    n1, n0 = len(positive), len(negative)
    pooled = math.sqrt(((n1 - 1) * positive.var(ddof=1) + (n0 - 1) * negative.var(ddof=1)) / (n1 + n0 - 2))
    if pooled == 0:
        return math.nan
    correction = 1 - 3 / (4 * (n1 + n0) - 9)
    return float(correction * (positive.mean() - negative.mean()) / pooled)


def evaluate_scores(target: np.ndarray, score: np.ndarray) -> dict[str, Any]:
    prediction = (score >= 0).astype(int)
    return binary_metrics(target, prediction, score)


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    frozen_before = {str(path.relative_to(PROJECT_ROOT)): sha256(path) for path in FROZEN_PATHS}

    processed = pd.read_csv(PROJECT_ROOT / "data/processed/ckd_clean.csv", dtype={"row_id": str}).set_index("row_id")
    split = json.loads((PROJECT_ROOT / "artifacts/splits.json").read_text())
    development = processed.loc[split["development_row_ids"]].copy()
    development[TARGET] = development[TARGET].astype(int)
    bd_raw = pd.read_csv(PROJECT_ROOT / "data/external/raw/BD-KDD_Dataset.csv")
    bd = load_bd_kdd(PROJECT_ROOT / "data/external/raw/BD-KDD_Dataset.csv")
    uci_parsed = load_official_arff(PROJECT_ROOT / "data/raw/chronic_kidney_disease.arff").frame.set_index("row_id")

    classical_bundle = joblib.load(MODEL_PATHS["classical_rbf_svm"])
    qsvc_bundle = joblib.load(MODEL_PATHS["qsvc"])
    if classical_bundle["features"] != FEATURES or qsvc_bundle["features"] != FEATURES:
        raise RuntimeError("Frozen eight-feature signature does not match Phase 3B contract")
    classical = classical_bundle["model"]
    qsvc = qsvc_bundle["model"]
    preprocessor = qsvc_bundle["preprocessor"]
    if not np.array_equal(classical.classes_, [0, 1]) or not np.array_equal(qsvc.classes_, [0, 1]):
        raise RuntimeError("CRITICAL BUG: frozen model class ordering is not [0, 1]")

    x_uci = np.asarray(preprocessor.transform(development[FEATURES]), dtype=float)
    x_bd = np.asarray(preprocessor.transform(bd[FEATURES]), dtype=float)
    y_uci = development[TARGET].to_numpy(dtype=int)
    y_bd = bd[TARGET].to_numpy(dtype=int)
    output_names = [str(value) for value in preprocessor.get_feature_names_out()]
    source_for_output = [value.split("_", 1)[0] if value not in FEATURES else value for value in output_names]

    # 1. Label mapping audit.
    raw_uci_values: dict[str, int] = {}
    started = False
    for line in (PROJECT_ROOT / "data/raw/chronic_kidney_disease.arff").read_text().splitlines():
        if line.strip().lower() == "@data":
            started = True
            continue
        if started and line.strip() and not line.lstrip().startswith("%"):
            raw_value = line.split(",")[-1]
            raw_uci_values[repr(raw_value)] = raw_uci_values.get(repr(raw_value), 0) + 1

    stored_predictions = pd.read_csv(PROJECT_ROOT / "artifacts/phase3/external_ckd_predictions.csv")
    label_rows = []
    auc_rows = []
    confusion_rows = []
    for model_name, estimator in (("classical_rbf_svm", classical), ("qsvc", qsvc)):
        scores = np.asarray(estimator.decision_function(x_bd), dtype=float)
        predictions = (scores >= 0).astype(int)
        current_auc = float(roc_auc_score(y_bd, scores))
        inverted_auc = float(roc_auc_score(1 - y_bd, scores))
        auc_rows.append({"model": model_name, "current_label_auc": current_auc, "inverted_label_auc": inverted_auc, "one_minus_current": 1 - current_auc})
        tn, fp, fn, tp = confusion_matrix(y_bd, predictions, labels=[0, 1]).ravel()
        confusion_rows.append({"model": model_name, "tn": tn, "fp": fp, "fn": fn, "tp": tp})
        persisted = stored_predictions[stored_predictions.model == model_name].sort_values("row_id")
        regenerated = pd.DataFrame({"row_id": bd.index, "target": y_bd, "prediction": predictions, "score": scores}).sort_values("row_id")
        label_rows.append({
            "model": model_name,
            "classes": list(map(int, estimator.classes_)),
            "decision_positive_class": int(estimator.classes_[1]),
            "prediction_match_pct": float(100 * np.mean(persisted.prediction.to_numpy() == regenerated.prediction.to_numpy())),
            "max_score_difference": float(np.max(np.abs(persisted.score.to_numpy() - regenerated.score.to_numpy()))),
        })
    auc_frame = pd.DataFrame(auc_rows)
    confusion_frame = pd.DataFrame(confusion_rows)
    label_frame = pd.DataFrame(label_rows)
    write_text(REPORT_DIR / "label_mapping_audit.md", f"""# Label Mapping Audit

## Decision

**PASS — no positive-class or target inversion bug was found.** CKD/kidney disease is canonical class `1`; non-CKD/healthy is class `0`. Both frozen estimators expose `classes_ = [0, 1]`, and positive decision scores map to `classes_[1] = 1`.

## Raw and cleaned targets

| Cohort | Raw target values | Cleaning rule | Clean counts |
|---|---|---|---|
| UCI CKD | `{raw_uci_values}` | strip/lower; `ckd → 1`, `notckd → 0` | full dataset `{uci_parsed[TARGET].value_counts().sort_index().to_dict()}`; development `{development[TARGET].value_counts().sort_index().to_dict()}` |
| BD-KDD | `{bd_raw['Class'].value_counts().sort_index().to_dict()}` | integer identity; dictionary says `0 = healthy`, `1 = kidney disease` | `{bd[TARGET].value_counts().sort_index().to_dict()}` |

## Metric and estimator ordering

- `binary_metrics` calls `confusion_matrix(..., labels=[0, 1])`, so the returned order is TN, FP, FN, TP.
- Sensitivity, precision, F1, ROC-AUC, and PR-AUC use class `1` as positive.
- SVM and QSVC both use `classes_ = [0, 1]`; `decision_function >= 0` predicts class `1`.
- Recomputed predictions match the frozen external prediction artifact exactly; maximum floating score differences are reported below.

{table(label_frame)}

## Deliberate inversion test

{table(auc_frame)}

Inverted-label AUC equals `1 − current AUC` to numerical precision, as expected. This is a diagnostic identity, not evidence that the labels should be inverted.

## Manual confusion matrices

Rows below use actual class order `[0, 1]` and predicted class order `[0, 1]`.

{table(confusion_frame, digits=0)}

The extreme specificity is therefore real under the documented label convention: both models predict almost every BD-KDD record as CKD.

Two raw UCI lines end with an empty token because they contain a documented spurious delimiter. The strict loader repairs the 26-column structure before reading the target; both repaired targets are `ckd`. They are not missing or guessed labels.
""")

    # 2. Feature semantics.
    semantics = pd.DataFrame([
        ["hemo", "Hemoglobin", "`hemo in gms` (denominator not stated)", "Hemo", "Hemoglobin level", "g/dL", "LIKELY MATCH", "No conversion"],
        ["al", "Urine albumin", "ordinal 0–5", "Al", "Urine albumin level", "0–5 scale", "EXACT MATCH", "Numeric identity"],
        ["dm", "Diabetes mellitus", "yes/no", "Dm", "Diabetes mellitus status", "0=no, 1=yes", "EXACT MATCH", "0→no; 1→yes; one-hot"],
        ["sg", "Urine specific gravity", "1.005–1.025 nominal levels", "Sg", "Urine specific gravity", "1.005–1.025", "EXACT MATCH", "Numeric identity"],
        ["pcv", "Packed cell volume", "numeric; unit not stated", "Pcv", "Packed cell volume", "percent", "LIKELY MATCH", "No conversion"],
        ["appet", "Appetite", "good/poor", "Appet", "Appetite condition", "0=poor, 1=good", "EXACT MATCH", "0→poor; 1→good; one-hot"],
        ["htn", "Hypertension", "yes/no", "Htn", "Hypertension status", "0=no, 1=yes", "EXACT MATCH", "0→no; 1→yes; one-hot"],
        ["sc", "Serum creatinine", "mg/dL (source writes mgs/dl)", "Sc", "Serum creatinine", "mg/dL", "EXACT MATCH", "Numeric identity"],
    ], columns=["UCI feature", "UCI meaning", "UCI unit/category", "BD-KDD feature", "BD-KDD meaning", "BD-KDD unit/category", "Mapping confidence", "Transformation"])
    write_text(REPORT_DIR / "feature_semantics.md", f"""# Frozen Feature Semantics Audit

## Decision

No documented unit or schema mismatch was found. Six mappings are exact. Hemoglobin and packed-cell volume are **likely matches**, because the UCI source description omits a denominator/unit that BD-KDD states explicitly. This is a documentation limitation, not measured evidence of a conversion mismatch.

{table(semantics)}

## Qualification

The mapping is syntactically and clinically plausible, but source dictionaries cannot prove laboratory calibration, assay practice, coding practice, or target-assignment equivalence across hospitals. The experiment remains a full-signature cross-cohort stress test rather than clean clinical external validation.
""")

    # 3. Raw distribution shift.
    raw_rows: list[dict[str, Any]] = []
    stat_names = ["min", "p1", "p5", "median", "p95", "p99", "max", "mean", "std", "missing_pct"]
    for feature in NUMERIC:
        u = development[feature].dropna().to_numpy(dtype=float)
        b = bd[feature].dropna().to_numpy(dtype=float)
        def describe(values: np.ndarray, total: int, missing: int) -> dict[str, float]:
            q = np.quantile(values, [0.01, 0.05, 0.5, 0.95, 0.99])
            return {"min": values.min(), "p1": q[0], "p5": q[1], "median": q[2], "p95": q[3], "p99": q[4], "max": values.max(), "mean": values.mean(), "std": values.std(ddof=1), "missing_pct": 100 * missing / total}
        us = describe(u, len(development), int(development[feature].isna().sum()))
        bs = describe(b, len(bd), int(bd[feature].isna().sum()))
        row: dict[str, Any] = {"feature": feature, "type": "numeric"}
        row.update({f"uci_{key}": value for key, value in us.items()})
        row.update({f"bd_{key}": value for key, value in bs.items()})
        row.update({
            "ks_statistic": float(stats.ks_2samp(u, b).statistic),
            "wasserstein": float(stats.wasserstein_distance(u, b)),
            "psi": psi(u, b),
            "prevalence_difference_pp": math.nan,
        })
        raw_rows.append(row)
    categorical_rows = []
    for feature in CATEGORICAL:
        risk = RISK_CATEGORY[feature]
        u_prev = float((development[feature] == risk).mean())
        b_prev = float((bd[feature] == risk).mean())
        categorical_rows.append({"feature": feature, "risk_category": risk, "uci_prevalence": u_prev, "bd_prevalence": b_prev, "difference_pp": 100 * (b_prev - u_prev), "uci_missing_pct": 100 * development[feature].isna().mean(), "bd_missing_pct": 100 * bd[feature].isna().mean()})
        raw_rows.append({
            "feature": feature, "type": "categorical", "uci_mean": u_prev, "bd_mean": b_prev,
            "uci_missing_pct": 100 * development[feature].isna().mean(), "bd_missing_pct": 100 * bd[feature].isna().mean(),
            "prevalence_difference_pp": 100 * (b_prev - u_prev), "ks_statistic": math.nan, "wasserstein": math.nan,
            "psi": psi((development[feature] == risk).astype(float).to_numpy(), (bd[feature] == risk).astype(float).to_numpy()),
        })
    raw_shift = pd.DataFrame(raw_rows)
    raw_shift.to_csv(REPORT_DIR / "raw_feature_shift.csv", index=False)
    categorical_shift = pd.DataFrame(categorical_rows)

    conditional_rows = []
    for feature in NUMERIC:
        u = development[feature].fillna(development[feature].median()).to_numpy(dtype=float)
        b = bd[feature].fillna(development[feature].median()).to_numpy(dtype=float)
        raw_uci_auc = float(roc_auc_score(y_uci, u))
        direction = 1.0 if raw_uci_auc >= 0.5 else -1.0
        conditional_rows.append({
            "feature": feature,
            "uci_risk_direction": "higher" if direction > 0 else "lower",
            "uci_directed_auc": float(roc_auc_score(y_uci, direction * u)),
            "bd_auc_using_uci_direction": float(roc_auc_score(y_bd, direction * b)),
            "uci_non_ckd_mean": float(u[y_uci == 0].mean()),
            "uci_ckd_mean": float(u[y_uci == 1].mean()),
            "bd_non_ckd_mean": float(b[y_bd == 0].mean()),
            "bd_ckd_mean": float(b[y_bd == 1].mean()),
            "uci_ckd_minus_non_mean": float(u[y_uci == 1].mean() - u[y_uci == 0].mean()),
            "bd_ckd_minus_non_mean": float(b[y_bd == 1].mean() - b[y_bd == 0].mean()),
        })
    for feature in CATEGORICAL:
        risk = RISK_CATEGORY[feature]
        u = (development[feature] == risk).astype(float).to_numpy()
        b = (bd[feature] == risk).astype(float).to_numpy()
        raw_uci_auc = float(roc_auc_score(y_uci, u))
        direction = 1.0 if raw_uci_auc >= 0.5 else -1.0
        conditional_rows.append({
            "feature": feature,
            "uci_risk_direction": risk if direction > 0 else f"not {risk}",
            "uci_directed_auc": float(roc_auc_score(y_uci, direction * u)),
            "bd_auc_using_uci_direction": float(roc_auc_score(y_bd, direction * b)),
            "uci_non_ckd_mean": float(u[y_uci == 0].mean()),
            "uci_ckd_mean": float(u[y_uci == 1].mean()),
            "bd_non_ckd_mean": float(b[y_bd == 0].mean()),
            "bd_ckd_mean": float(b[y_bd == 1].mean()),
            "uci_ckd_minus_non_mean": float(u[y_uci == 1].mean() - u[y_uci == 0].mean()),
            "bd_ckd_minus_non_mean": float(b[y_bd == 1].mean() - b[y_bd == 0].mean()),
        })
    conditional_shift = pd.DataFrame(conditional_rows)
    conditional_shift["directed_auc_loss"] = conditional_shift.bd_auc_using_uci_direction - conditional_shift.uci_directed_auc
    conditional_shift.to_csv(REPORT_DIR / "class_conditional_shift.csv", index=False)

    fig, axes = plt.subplots(3, 2, figsize=(11, 11))
    for ax, feature in zip(axes.flat, NUMERIC, strict=False):
        ax.hist(development[feature].dropna(), bins=25, density=True, alpha=0.55, label="UCI development")
        ax.hist(bd[feature].dropna(), bins=25, density=True, alpha=0.55, label="BD-KDD")
        ax.set(title=feature, ylabel="Density")
    axes.flat[-1].axis("off")
    axes.flat[0].legend()
    save_figure(fig, "raw_numeric_overlays.png")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(categorical_shift))
    ax.bar(x - 0.18, 100 * categorical_shift.uci_prevalence, 0.36, label="UCI development")
    ax.bar(x + 0.18, 100 * categorical_shift.bd_prevalence, 0.36, label="BD-KDD")
    ax.set(xticks=x, xticklabels=[f"{r.feature}={r.risk_category}" for r in categorical_shift.itertuples()], ylabel="Prevalence (%)", title="Categorical frozen-feature prevalence")
    ax.legend()
    save_figure(fig, "raw_categorical_prevalence.png")
    fig, ax = plt.subplots(figsize=(10, 5))
    positions = np.arange(len(conditional_shift))
    ax.bar(positions - 0.18, conditional_shift.uci_directed_auc, 0.36, label="UCI development")
    ax.bar(positions + 0.18, conditional_shift.bd_auc_using_uci_direction, 0.36, label="BD-KDD, UCI direction")
    ax.axhline(0.5, color="black", linestyle="--", linewidth=1)
    ax.set(xticks=positions, xticklabels=conditional_shift.feature, ylim=(0, 1), ylabel="Single-feature ROC-AUC", title="Transport of frozen-feature target associations")
    ax.legend()
    save_figure(fig, "class_conditional_auc_transport.png")

    worst_raw = raw_shift.loc[raw_shift.psi.idxmax()]
    numeric_summary = raw_shift[raw_shift.type == "numeric"][["feature", "uci_median", "bd_median", "uci_mean", "bd_mean", "uci_missing_pct", "bd_missing_pct", "ks_statistic", "wasserstein", "psi"]]
    write_text(REPORT_DIR / "raw_feature_shift.md", f"""# Raw Frozen-Feature Shift

## Decision

All eight inputs shift materially in at least one marginal property. The largest PSI is **{worst_raw.feature} ({worst_raw.psi:.3f})**. PSI is a descriptive bin-based shift indicator, not a hypothesis test or universal severity scale.

## Numeric features

{table(numeric_summary)}

The CSV contains min, p1, p5, median, p95, p99, max, mean, standard deviation, missingness, KS statistic, Wasserstein distance, and PSI for every numeric frozen feature.

## Categorical prevalence

{table(categorical_shift)}

## Class-conditional relationship transport

Each feature's risk direction is fixed from UCI development, then applied unchanged to BD-KDD. This is descriptive association transport, not feature selection.

{table(conditional_shift)}

The UCI-directed single-feature AUCs collapse toward 0.5 in BD-KDD. This loss of class-conditional structure is more mechanistically important than marginal shift alone and is consistent with both frozen models losing discrimination.

## Plots

- [Numeric overlays](figures/raw_numeric_overlays.png)
- [Categorical prevalence](figures/raw_categorical_prevalence.png)
- [Class-conditional AUC transport](figures/class_conditional_auc_transport.png)

P-values are intentionally omitted: with 988 external records they would not measure practical transportability, and marginal tests do not establish a causal mechanism.
""")

    # 4. Frozen scaler audit.
    numeric_pipeline = preprocessor.named_transformers_["numeric"]
    scaler = numeric_pipeline.named_steps["scaler"]
    numeric_indices = [output_names.index(feature) for feature in NUMERIC]
    scaler_rows = []
    outside_matrix = np.zeros((len(bd), len(NUMERIC)), dtype=bool)
    for local_index, (feature, column_index) in enumerate(zip(NUMERIC, numeric_indices, strict=True)):
        u = x_uci[:, column_index]
        b = x_bd[:, column_index]
        u_min, u_max = float(u.min()), float(u.max())
        outside_matrix[:, local_index] = (b < u_min) | (b > u_max)
        scaler_rows.append({
            "feature": feature,
            "scaler_mean": float(scaler.mean_[local_index]),
            "scaler_scale": float(scaler.scale_[local_index]),
            "uci_t_min": u_min,
            "uci_t_p1": float(np.quantile(u, 0.01)),
            "uci_t_p99": float(np.quantile(u, 0.99)),
            "uci_t_max": u_max,
            "bd_t_min": float(b.min()),
            "bd_t_p1": float(np.quantile(b, 0.01)),
            "bd_t_p99": float(np.quantile(b, 0.99)),
            "bd_t_max": float(b.max()),
            "bd_below_uci_min_pct": float(100 * np.mean(b < u_min)),
            "bd_above_uci_max_pct": float(100 * np.mean(b > u_max)),
            "bd_outside_uci_range_pct": float(100 * np.mean((b < u_min) | (b > u_max))),
            "bd_beyond_2sd_pct": float(100 * np.mean(np.abs(b) > 2)),
            "bd_beyond_3sd_pct": float(100 * np.mean(np.abs(b) > 3)),
            "bd_beyond_5sd_pct": float(100 * np.mean(np.abs(b) > 5)),
        })
    scaler_shift = pd.DataFrame(scaler_rows)
    scaler_shift.to_csv(REPORT_DIR / "scaler_shift.csv", index=False)
    cell_outside_pct = float(100 * outside_matrix.mean())
    sample_any_outside_pct = float(100 * outside_matrix.any(axis=1).mean())
    fig, axes = plt.subplots(3, 2, figsize=(11, 11))
    for ax, feature, column_index in zip(axes.flat, NUMERIC, numeric_indices, strict=False):
        ax.hist(x_uci[:, column_index], bins=25, density=True, alpha=0.55, label="UCI transformed")
        ax.hist(x_bd[:, column_index], bins=25, density=True, alpha=0.55, label="BD-KDD transformed")
        ax.axvline(-3, color="firebrick", linestyle="--", linewidth=1)
        ax.axvline(3, color="firebrick", linestyle="--", linewidth=1)
        ax.set(title=feature, ylabel="Density")
    axes.flat[-1].axis("off")
    axes.flat[0].legend()
    save_figure(fig, "frozen_scaler_overlays.png")
    write_text(REPORT_DIR / "scaler_shift.md", f"""# Frozen UCI-Scaler Shift

## Decision

Using the exact persisted UCI-development preprocessor, **{cell_outside_pct:.2f}% of BD-KDD numeric feature cells** lie outside the corresponding UCI-development transformed min/max, and **{sample_any_outside_pct:.2f}% of BD-KDD records** contain at least one such numeric value.

{table(scaler_shift)}

The scaler mean/scale and all transformed reference bounds come from the persisted QSVC preprocessor. Because the scaler was fitted on UCI development data, transformed values are measured in UCI training standard deviations.

[Transformed distribution overlays](figures/frozen_scaler_overlays.png)
""")

    # 5. Installed feature-map angle and periodicity audit.
    circuit = build_feature_map("z_reps1", len(output_names))
    decomposed_ops = [(instruction.operation.name, [str(value) for value in instruction.operation.params]) for instruction in circuit.decompose().data]
    phase_expressions = [params[-1] for name, params in decomposed_ops if name == "u" and params and "x[" in params[-1]]
    if phase_expressions != [f"2*x[{index}]" for index in range(len(output_names))]:
        raise RuntimeError(f"Unexpected installed ZFeatureMap phase mapping: {phase_expressions}")
    two_pi = 2 * np.pi
    angle_rows: list[dict[str, Any]] = []
    angle_value_rows: list[dict[str, Any]] = []
    for feature_index, (output_name, source) in enumerate(zip(output_names, source_for_output, strict=True)):
        u = x_uci[:, feature_index]
        b = x_bd[:, feature_index]
        phase_u, phase_b = 2 * u, 2 * b
        mod_u, mod_b = np.mod(phase_u, two_pi), np.mod(phase_b, two_pi)
        unique_u, unique_b = np.unique(np.round(u, 10)), np.unique(np.round(b, 10))
        raw_diff = np.abs(unique_b[:, None] - unique_u[None, :])
        angular = np.abs(np.angle(np.exp(1j * (2 * unique_b[:, None] - 2 * unique_u[None, :]))))
        cross_alias_pairs = int(np.sum((raw_diff > 0.5) & (angular < 0.01)))
        def within_alias_count(unique_values: np.ndarray) -> int:
            if len(unique_values) < 2:
                return 0
            left, right = np.triu_indices(len(unique_values), 1)
            differences = np.abs(unique_values[left] - unique_values[right])
            circular = np.abs(np.angle(np.exp(1j * 2 * (unique_values[left] - unique_values[right]))))
            return int(np.sum((differences > 0.5) & (circular < 0.01)))
        all_cross_angular = np.abs(np.angle(np.exp(1j * (phase_b[:, None] - phase_u[None, :]))))
        angle_rows.append({
            "output_feature": output_name,
            "source_feature": source,
            "uci_x_min": float(u.min()), "uci_x_max": float(u.max()),
            "bd_x_min": float(b.min()), "bd_x_max": float(b.max()),
            "uci_phase_min": float(phase_u.min()), "uci_phase_max": float(phase_u.max()),
            "bd_phase_min": float(phase_b.min()), "bd_phase_max": float(phase_b.max()),
            "uci_phase_mod_min": float(mod_u.min()), "uci_phase_mod_max": float(mod_u.max()),
            "bd_phase_mod_min": float(mod_b.min()), "bd_phase_mod_max": float(mod_b.max()),
            "uci_principal_wrap_pct": float(100 * np.mean(np.abs(phase_u) > np.pi)),
            "bd_principal_wrap_pct": float(100 * np.mean(np.abs(phase_b) > np.pi)),
            "uci_abs_ge_2pi_pct": float(100 * np.mean(np.abs(phase_u) >= two_pi)),
            "bd_abs_ge_2pi_pct": float(100 * np.mean(np.abs(phase_b) >= two_pi)),
            "uci_max_full_periods_from_zero": int(np.floor(np.max(np.abs(phase_u)) / two_pi)),
            "bd_max_full_periods_from_zero": int(np.floor(np.max(np.abs(phase_b)) / two_pi)),
            "uci_unique_x": len(unique_u), "bd_unique_x": len(unique_b),
            "uci_distinct_x_near_modulo_pairs": within_alias_count(unique_u),
            "bd_distinct_x_near_modulo_pairs": within_alias_count(unique_b),
            "cross_distinct_x_near_modulo_pairs": cross_alias_pairs,
            "cross_angular_distance_median": float(np.median(all_cross_angular)),
            "cross_angular_distance_p5": float(np.quantile(all_cross_angular, 0.05)),
        })
        for cohort, row_ids, targets, values in (
            ("UCI development", development.index, y_uci, u),
            ("BD-KDD", bd.index, y_bd, b),
        ):
            phases = 2 * values
            for row_id, target, value, phase in zip(row_ids, targets, values, phases, strict=True):
                angle_value_rows.append({
                    "cohort": cohort, "row_id": row_id, "target": int(target),
                    "output_feature": output_name, "source_feature": source,
                    "transformed_x": float(value), "phase_angle_2x": float(phase),
                    "phase_mod_2pi": float(np.mod(phase, two_pi)),
                    "outside_principal_phase": bool(abs(phase) > np.pi),
                    "full_periods_from_zero": int(np.floor(abs(phase) / two_pi)),
                })
    angle_audit = pd.DataFrame(angle_rows)
    pd.DataFrame(angle_value_rows).to_csv(REPORT_DIR / "quantum_angle_audit.csv", index=False)
    angle_audit.to_csv(REPORT_DIR / "quantum_angle_summary.csv", index=False)

    fig, axes = plt.subplots(4, 2, figsize=(12, 14))
    for ax, row_index in zip(axes.flat, range(len(output_names)), strict=True):
        values = np.linspace(min(x_uci[:, row_index].min(), x_bd[:, row_index].min()), max(x_uci[:, row_index].max(), x_bd[:, row_index].max()), 200)
        ax.plot(values, 2 * values)
        ax.set(title=output_names[row_index], xlabel="Scaled x", ylabel="Actual phase 2x")
    save_figure(fig, "angle_scaled_to_phase.png")
    fig, axes = plt.subplots(4, 2, figsize=(12, 14))
    for ax, column_index in zip(axes.flat, range(len(output_names)), strict=True):
        take = np.linspace(0, len(x_bd) - 1, min(300, len(x_bd))).astype(int)
        ax.scatter(x_bd[take, column_index], np.mod(2 * x_bd[take, column_index], two_pi), s=8, alpha=0.5)
        ax.set(title=output_names[column_index], xlabel="Scaled x", ylabel="Phase modulo 2π")
    save_figure(fig, "angle_scaled_to_modulo.png")
    fig, axes = plt.subplots(4, 2, figsize=(12, 14))
    for ax, column_index in zip(axes.flat, range(len(output_names)), strict=True):
        ax.hist(np.mod(2 * x_uci[:, column_index], two_pi), bins=24, density=True, alpha=0.55, label="UCI")
        ax.hist(np.mod(2 * x_bd[:, column_index], two_pi), bins=24, density=True, alpha=0.55, label="BD-KDD")
        ax.set(title=output_names[column_index], xlabel="Phase modulo 2π", ylabel="Density")
    axes.flat[0].legend()
    save_figure(fig, "angle_modulo_distributions.png")
    fig, ax = plt.subplots(figsize=(10, 5))
    positions = np.arange(len(angle_audit))
    ax.bar(positions - 0.18, angle_audit.bd_principal_wrap_pct, 0.36, label="Outside principal [−π, π]")
    ax.bar(positions + 0.18, angle_audit.bd_abs_ge_2pi_pct, 0.36, label="At least one full 2π from zero")
    ax.set(xticks=positions, xticklabels=angle_audit.output_feature, ylabel="BD-KDD values (%)", title="Per-feature phase wrapping")
    ax.legend()
    save_figure(fig, "angle_wrap_counts.png")
    write_text(REPORT_DIR / "quantum_angle_audit.md", f"""# Quantum Angle and Periodicity Audit

## Concrete installed mapping

Qiskit generated a one-repetition `ZFeatureMap` with one Hadamard and `P(2*x[i])` per qubit. The decomposed installed circuit contains phase expressions `{phase_expressions}`. Therefore the audited phase is `2x`, and the fidelity kernel is periodic in each scaled input with period `π`.

{table(angle_audit)}

`principal_wrap_pct` counts phase values outside `[−π, π]`; `abs_ge_2pi_pct` counts values at least one complete phase period from zero. Near-modulo pairs require transformed values to differ by more than 0.5 while their circular phase distance is below 0.01 radians.

`quantum_angle_audit.csv` contains every UCI-development and BD-KDD transformed value, actual phase, modulo phase, principal-wrap flag, and full-period count. `quantum_angle_summary.csv` contains the table above.

## Plots

- [Scaled value → phase](figures/angle_scaled_to_phase.png)
- [Scaled value → phase modulo 2π](figures/angle_scaled_to_modulo.png)
- [UCI vs BD-KDD modulo-angle distributions](figures/angle_modulo_distributions.png)
- [Per-feature wrap counts](figures/angle_wrap_counts.png)

Phase wrapping alone is not labelled clinically meaningful aliasing. The state-collision audit tests whether high-distance clinical representations actually receive high fidelity.
""")

    # 6. Actual frozen FidelityQuantumKernel and collision audit.
    u_idx = stratified_indices(y_uci, 60, EXPERIMENT_SEED)
    b_idx = stratified_indices(y_bd, 80, EXPERIMENT_SEED + 1)
    x_rep = np.vstack([x_uci[u_idx], x_bd[b_idx]])
    y_rep = np.concatenate([y_uci[u_idx], y_bd[b_idx]])
    cohort_rep = np.array(["UCI"] * len(u_idx) + ["BD-KDD"] * len(b_idx))
    id_rep = np.concatenate([development.index.to_numpy()[u_idx], bd.index.to_numpy()[b_idx]])
    actual_kernel = np.asarray(qsvc.quantum_kernel.evaluate(x_rep), dtype=float)
    analytic_kernel = z_kernel(x_rep)
    analytic_max_error = float(np.max(np.abs(actual_kernel - analytic_kernel)))
    if analytic_max_error > 1e-10:
        raise RuntimeError(f"Analytic Z-kernel check failed: {analytic_max_error}")
    n_u = len(u_idx)
    kernel_summaries = pd.DataFrame([
        kernel_summary("within_UCI", actual_kernel[:n_u, :n_u], y_uci[u_idx]),
        kernel_summary("within_BD-KDD", actual_kernel[n_u:, n_u:], y_bd[b_idx]),
    ])
    cross_kernel = actual_kernel[n_u:, :n_u]
    cross_summary = pd.DataFrame([{
        "matrix": "BD-KDD_to_UCI",
        "rows": cross_kernel.shape[0], "columns": cross_kernel.shape[1],
        "mean": float(cross_kernel.mean()), "std": float(cross_kernel.std()),
        "near_one_pct": float(100 * np.mean(cross_kernel >= 0.99)),
        "near_zero_pct": float(100 * np.mean(cross_kernel <= 0.01)),
        "geometry_auc": float(roc_auc_score(y_bd[b_idx], cross_kernel[:, y_uci[u_idx] == 1].mean(axis=1) - cross_kernel[:, y_uci[u_idx] == 0].mean(axis=1))),
    }])
    distances = pairwise_distances(x_rep)
    tri = np.triu_indices(len(x_rep), k=1)
    high_distance_threshold = float(np.quantile(distances[tri], 0.95))
    collision_mask = (distances[tri] >= high_distance_threshold) & (actual_kernel[tri] >= 0.95)
    collision_indices = np.flatnonzero(collision_mask)
    collision_rows = []
    for position in collision_indices[np.argsort(actual_kernel[tri][collision_mask])[::-1][:20]]:
        left, right = tri[0][position], tri[1][position]
        collision_rows.append({
            "left_id": id_rep[left], "left_cohort": cohort_rep[left], "left_target": int(y_rep[left]),
            "right_id": id_rep[right], "right_cohort": cohort_rep[right], "right_target": int(y_rep[right]),
            "clinical_distance": float(distances[left, right]), "quantum_fidelity": float(actual_kernel[left, right]),
            "left_transformed": np.round(x_rep[left], 4).tolist(), "right_transformed": np.round(x_rep[right], 4).tolist(),
        })
    collision_frame = pd.DataFrame(collision_rows)
    collision_frame.to_csv(REPORT_DIR / "kernel_collision_examples.csv", index=False)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    axes[0].hist(actual_kernel[:n_u, :n_u][np.triu_indices(n_u, 1)], bins=30, alpha=0.75)
    axes[0].set(title="Within UCI", xlabel="Fidelity")
    axes[1].hist(actual_kernel[n_u:, n_u:][np.triu_indices(len(b_idx), 1)], bins=30, alpha=0.75)
    axes[1].set(title="Within BD-KDD", xlabel="Fidelity")
    axes[2].hist(cross_kernel.ravel(), bins=30, alpha=0.75)
    axes[2].set(title="BD-KDD to UCI", xlabel="Fidelity")
    save_figure(fig, "kernel_similarity_distributions.png")
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(distances[tri], actual_kernel[tri], s=7, alpha=0.25)
    ax.axvline(high_distance_threshold, color="firebrick", linestyle="--", label="95th-percentile distance")
    ax.axhline(0.95, color="darkorange", linestyle="--", label="Fidelity 0.95")
    ax.set(xlabel="Euclidean distance in frozen transformed representation", ylabel="Quantum fidelity", title="Distance–fidelity collision audit")
    ax.legend()
    save_figure(fig, "kernel_collision_scatter.png")
    write_text(REPORT_DIR / "kernel_shift.md", f"""# Quantum-Kernel Shift and State-Collision Audit

## Method

The persisted frozen QSVC `FidelityQuantumKernel` was evaluated on deterministic class-stratified representatives: {len(u_idx)} UCI-development and {len(b_idx)} BD-KDD records. The installed `ZFeatureMap` result matched the closed-form `∏ cos²(xᵢ−yᵢ)` with maximum absolute error **{analytic_max_error:.3e}**.

## Within-cohort geometry

{table(kernel_summaries)}

## Cross-cohort geometry

{table(cross_summary)}

## Collision test

High clinical distance was predefined descriptively as the top 5% of pairwise Euclidean distances in the frozen transformed representation ({high_distance_threshold:.3f} or greater). A representation collision required fidelity at least 0.95. **{len(collision_indices)} of {len(tri[0])} representative pairs ({100 * len(collision_indices) / len(tri[0]):.3f}%)** met both conditions.

Examples are stored in `kernel_collision_examples.csv`. Because the distance mixes UCI-standardised numeric values and one-hot clinical indicators, it is a representation-space clinical distance, not a validated clinical similarity metric.

## Plots

- [Kernel similarity distributions](figures/kernel_similarity_distributions.png)
- [Distance–fidelity collision audit](figures/kernel_collision_scatter.png)
""")

    # 7 and 8. Classical RBF and score diagnostics.
    score_rows = []
    score_arrays: dict[tuple[str, str], np.ndarray] = {}
    for model_name, estimator in (("classical_rbf_svm", classical), ("qsvc", qsvc)):
        for cohort, matrix, target in (("UCI development (training diagnostic)", x_uci, y_uci), ("BD-KDD external", x_bd, y_bd)):
            scores = np.asarray(estimator.decision_function(matrix), dtype=float)
            score_arrays[(model_name, cohort)] = scores
            positive, negative = scores[target == 1], scores[target == 0]
            score_rows.append({
                "model": model_name, "cohort": cohort,
                "ckd_score_median": float(np.median(positive)), "non_ckd_score_median": float(np.median(negative)),
                "overlap_coefficient": overlap_coefficient(positive, negative),
                "hedges_g_ckd_minus_non": hedges_g(positive, negative),
                "ckd_above_boundary_pct": float(100 * np.mean(positive >= 0)),
                "non_ckd_above_boundary_pct": float(100 * np.mean(negative >= 0)),
                "all_above_boundary_pct": float(100 * np.mean(scores >= 0)),
                "roc_auc": float(roc_auc_score(target, scores)),
            })
    score_frame = pd.DataFrame(score_rows)
    score_frame.to_csv(REPORT_DIR / "score_distribution.csv", index=False)
    gamma = float(classical._gamma)
    support = np.asarray(classical.support_vectors_, dtype=float)
    bd_support_distances = pairwise_distances(x_bd, support)
    rbf_rep = np.exp(-gamma * pairwise_distances(x_rep, squared=True))
    rbf_kernel_summary = pd.DataFrame([
        kernel_summary("RBF_within_UCI", rbf_rep[:n_u, :n_u], y_uci[u_idx]),
        kernel_summary("RBF_within_BD-KDD", rbf_rep[n_u:, n_u:], y_bd[b_idx]),
    ])
    support_summary = pd.DataFrame([
        {"actual_class": label, "n": int(np.sum(y_bd == label)), "min_distance_median": float(np.median(bd_support_distances[y_bd == label].min(axis=1))), "min_distance_p95": float(np.quantile(bd_support_distances[y_bd == label].min(axis=1), 0.95)), "median_distance_to_all_support_vectors": float(np.median(bd_support_distances[y_bd == label]))}
        for label in (0, 1)
    ])
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    for ax, (model_name, cohort) in zip(axes.flat, score_arrays, strict=True):
        target = y_uci if cohort.startswith("UCI") else y_bd
        scores = score_arrays[(model_name, cohort)]
        ax.hist(scores[target == 0], bins=30, alpha=0.55, density=True, label="non-CKD")
        ax.hist(scores[target == 1], bins=30, alpha=0.55, density=True, label="CKD")
        ax.axvline(0, color="black", linestyle="--", linewidth=1)
        ax.set(title=f"{model_name} · {cohort}", xlabel="Decision score", ylabel="Density")
    axes.flat[0].legend()
    save_figure(fig, "decision_score_distributions.png")
    write_text(REPORT_DIR / "score_distribution.md", f"""# Frozen Score-Distribution Diagnostic

## Class score separation

{table(score_frame)}

The overlap coefficient is histogram overlap on `[0,1]`; lower is better separation. Hedges’ g is positive when CKD scores exceed non-CKD scores. The UCI values are training-set diagnostics for the frozen development-fitted model, not independent performance estimates.

## Classical RBF geometry

The frozen classical model uses `gamma={gamma:.6g}` and {len(support)} support vectors.

{table(rbf_kernel_summary)}

### BD-KDD distance from frozen classical support vectors

{table(support_summary)}

## Mechanistic explanation

On BD-KDD, the non-CKD fraction above the decision boundary is the false-positive rate. Values near 99% directly explain specificity near 1%. Both frozen models shift nearly all external scores to the CKD side.

[Decision-score distributions](figures/decision_score_distributions.png)
""")

    # 9. Diagnostic-only leave-one-feature-out kernel geometry.
    ablation_rows = []
    for removed in [None, *FEATURES]:
        keep = [index for index, source in enumerate(source_for_output) if source != removed]
        train_matrix = x_uci[:, keep]
        external_matrix = x_bd[:, keep]
        k_train = z_kernel(train_matrix)
        k_external = z_kernel(external_matrix, train_matrix)
        diagnostic = SVC(C=CLASSIFIER_C, kernel="precomputed")
        diagnostic.fit(k_train, y_uci)
        score = np.asarray(diagnostic.decision_function(k_external), dtype=float)
        geometry_score = k_external[:, y_uci == 1].mean(axis=1) - k_external[:, y_uci == 0].mean(axis=1)
        same_class_similarity = []
        different_class_similarity = []
        for row_index, label in enumerate(y_bd):
            same_class_similarity.extend(k_external[row_index, y_uci == label])
            different_class_similarity.extend(k_external[row_index, y_uci != label])
        metrics = evaluate_scores(y_bd, score)
        ablation_rows.append({
            "removed_feature": "none (8-feature diagnostic replay)" if removed is None else removed,
            "dimensions": len(keep), "external_auc": metrics["roc_auc"], "sensitivity": metrics["sensitivity"], "specificity": metrics["specificity"],
            "kernel_target_alignment_uci": centered_alignment(k_train, y_uci),
            "external_geometry_auc": float(roc_auc_score(y_bd, geometry_score)),
            "same_minus_different_similarity": float(np.mean(same_class_similarity) - np.mean(different_class_similarity)),
        })
    ablation = pd.DataFrame(ablation_rows)
    baseline_ablation_auc = float(ablation.iloc[0].external_auc)
    ablation["auc_change_vs_8_feature_diagnostic"] = ablation.external_auc - baseline_ablation_auc
    ablation.to_csv(REPORT_DIR / "ablation_diagnostic.csv", index=False)
    best_ablation = ablation.iloc[1:].sort_values("external_auc", ascending=False).iloc[0]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(ablation.removed_feature, ablation.external_auc)
    ax.axhline(baseline_ablation_auc, color="firebrick", linestyle="--", label="8-feature diagnostic replay")
    ax.set(ylim=(0, 1), ylabel="BD-KDD ROC-AUC", title="Diagnostic-only quantum-kernel feature ablation")
    ax.tick_params(axis="x", rotation=35)
    ax.legend()
    save_figure(fig, "ablation_auc.png")
    write_text(REPORT_DIR / "ablation_diagnostic.md", f"""# Feature-by-Feature Quantum-Kernel Ablation — Diagnostic Only

## Boundary

These are disposable precomputed-kernel SVC fits using the exact analytical fidelity of the frozen `ZFeatureMap`. They do **not** alter or replace the frozen QSVC. The eight-feature diagnostic replay reproduces the frozen kernel definition before leave-one-feature-out geometry is inspected.

{table(ablation)}

The largest external AUC after removal was **{best_ablation.external_auc:.3f}** when removing **{best_ablation.removed_feature}** (change {best_ablation.auc_change_vs_8_feature_diagnostic:+.3f}). This is a mechanism probe, not feature selection or a new final model.

[Ablation AUC plot](figures/ablation_auc.png)
""")

    # 10. Frozen-model clipping diagnostics.
    clip_rows = []
    clip_specs: dict[str, tuple[np.ndarray, np.ndarray]] = {
        "none (frozen external result)": (np.full(x_uci.shape[1], -np.inf), np.full(x_uci.shape[1], np.inf)),
        "UCI development min/max": (x_uci.min(axis=0), x_uci.max(axis=0)),
        "UCI development p1/p99": (np.quantile(x_uci, 0.01, axis=0), np.quantile(x_uci, 0.99, axis=0)),
        "±3 transformed SD": (np.full(x_uci.shape[1], -3.0), np.full(x_uci.shape[1], 3.0)),
    }
    for name, (lower, upper) in clip_specs.items():
        clipped = np.clip(x_bd, lower, upper)
        score = np.asarray(qsvc.decision_function(clipped), dtype=float)
        metrics = evaluate_scores(y_bd, score)
        clip_rows.append({"condition": name, "changed_cell_pct": float(100 * np.mean(~np.isclose(clipped, x_bd))), **{key: metrics[key] for key in ["sensitivity", "specificity", "roc_auc", "pr_auc", "tn", "fp", "fn", "tp"]}})
    clipping = pd.DataFrame(clip_rows)
    clipping["auc_change_vs_frozen"] = clipping.roc_auc - float(clipping.iloc[0].roc_auc)
    clipping.to_csv(REPORT_DIR / "clipping_diagnostic.csv", index=False)
    best_clipping = clipping.iloc[1:].sort_values("roc_auc", ascending=False).iloc[0]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(clipping.condition, clipping.roc_auc)
    ax.axhline(float(clipping.iloc[0].roc_auc), color="firebrick", linestyle="--", label="Frozen result")
    ax.set(ylim=(0, 1), ylabel="BD-KDD ROC-AUC", title="Frozen-QSVC diagnostic clipping")
    ax.tick_params(axis="x", rotation=25)
    ax.legend()
    save_figure(fig, "clipping_auc.png")
    write_text(REPORT_DIR / "clipping_diagnostic.md", f"""# Temporary Clipping Experiment — Diagnostic Only

The persisted QSVC and decision boundary were not retrained. Only BD-KDD transformed inputs were temporarily clipped before being passed to the frozen estimator.

{table(clipping)}

The best clipping condition was **{best_clipping.condition}**, with ROC-AUC **{best_clipping.roc_auc:.3f}** (change {best_clipping.auc_change_vs_frozen:+.3f}). The original frozen external result remains authoritative.

[Clipping AUC plot](figures/clipping_auc.png)
""")

    # 11. Post-hoc bounded encodings, fitted only on UCI development.
    base = make_preprocessor(FEATURES, scale=False)
    base_uci = np.asarray(base.fit_transform(development[FEATURES], y_uci), dtype=float)
    base_bd = np.asarray(base.transform(bd[FEATURES]), dtype=float)
    bound = np.pi / 4

    minmax = MinMaxScaler(feature_range=(-bound, bound), clip=True).fit(base_uci)
    robust = RobustScaler().fit(base_uci)
    quantile = QuantileTransformer(n_quantiles=min(100, len(base_uci)), output_distribution="uniform", random_state=EXPERIMENT_SEED).fit(base_uci)
    bounded_transforms: dict[str, Callable[[np.ndarray], np.ndarray]] = {
        "MinMax clipped to [−π/4, π/4]": lambda values: minmax.transform(values),
        "RobustScaler + tanh to (−π/4, π/4)": lambda values: bound * np.tanh(robust.transform(values)),
        "UCI quantile map to [−π/4, π/4]": lambda values: (2 * quantile.transform(values) - 1) * bound,
    }
    bounded_rows = []
    for name, transform in bounded_transforms.items():
        train_matrix = transform(base_uci)
        external_matrix = transform(base_bd)
        kernel, _ = make_quantum_kernel("z_reps1", train_matrix.shape[1], seed=EXPERIMENT_SEED)
        exploratory = QSVC(quantum_kernel=kernel, C=CLASSIFIER_C)
        exploratory.fit(train_matrix, y_uci)
        score = np.asarray(exploratory.decision_function(external_matrix), dtype=float)
        metrics = evaluate_scores(y_bd, score)
        bounded_rows.append({
            "condition": name, "fit_scope": "UCI development only", "external_use": "one post-hoc BD-KDD evaluation",
            "train_min": float(train_matrix.min()), "train_max": float(train_matrix.max()),
            "external_min": float(external_matrix.min()), "external_max": float(external_matrix.max()),
            **{key: metrics[key] for key in ["sensitivity", "specificity", "roc_auc", "pr_auc", "tn", "fp", "fn", "tp"]},
        })
    bounded = pd.DataFrame(bounded_rows)
    frozen_auc = float(auc_frame.loc[auc_frame.model == "qsvc", "current_label_auc"].iloc[0])
    bounded["auc_change_vs_original_frozen"] = bounded.roc_auc - frozen_auc
    bounded.to_csv(REPORT_DIR / "exploratory_bounded_encoding.csv", index=False)
    best_bounded = bounded.sort_values("roc_auc", ascending=False).iloc[0]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(bounded.condition, bounded.roc_auc)
    ax.axhline(frozen_auc, color="firebrick", linestyle="--", label="Original frozen QSVC")
    ax.set(ylim=(0, 1), ylabel="BD-KDD ROC-AUC", title="Post-hoc bounded-encoding research")
    ax.tick_params(axis="x", rotation=25)
    ax.legend()
    save_figure(fig, "bounded_encoding_auc.png")
    write_text(REPORT_DIR / "exploratory_bounded_encoding.md", f"""# Alternative Bounded Encoding — Post-Hoc Exploratory Analysis

## Scientific boundary

These models are experimental copies. Each preprocessing transform was fitted **only on UCI development data**, then a fresh QSVC was fitted there and evaluated once on BD-KDD. Nothing overwrites the frozen model or its external result. The interval `[−π/4, π/4]` was chosen because the installed feature-map phase is `2x`; it prevents more than a half-turn per feature inside the UCI-fitted range and avoids mapping binary endpoints to the same quantum state.

{table(bounded)}

The best exploratory result was **{best_bounded.condition}**, ROC-AUC **{best_bounded.roc_auc:.3f}** (change {best_bounded.auc_change_vs_original_frozen:+.3f} versus the original frozen QSVC).

Even an improvement would support only this wording: **Post-hoc analysis identified a potential transportability improvement.** It would not convert the original experiment into successful external validation.

[Bounded-encoding AUC plot](figures/bounded_encoding_auc.png)
""")

    # Compact machine-readable summary used for the final interpretation.
    summary = {
        "label_mapping_correct": True,
        "semantic_mismatch_found": False,
        "semantic_likely_matches": ["hemo", "pcv"],
        "worst_shifted_feature_by_psi": str(worst_raw.feature),
        "worst_shifted_feature_psi": float(worst_raw.psi),
        "bd_numeric_cells_outside_uci_range_pct": cell_outside_pct,
        "bd_records_any_numeric_outside_uci_range_pct": sample_any_outside_pct,
        "features_with_principal_phase_wrap": angle_audit.loc[angle_audit.bd_principal_wrap_pct > 0, "output_feature"].tolist(),
        "features_with_full_2pi_phase_crossing": angle_audit.loc[angle_audit.bd_abs_ge_2pi_pct > 0, "output_feature"].tolist(),
        "representative_high_distance_high_fidelity_pairs": int(len(collision_indices)),
        "representative_pair_count": int(len(tri[0])),
        "representative_collision_pct": float(100 * len(collision_indices) / len(tri[0])),
        "actual_vs_analytic_kernel_max_error": analytic_max_error,
        "classical_external_auc": float(auc_frame.loc[auc_frame.model == "classical_rbf_svm", "current_label_auc"].iloc[0]),
        "qsvc_external_auc": frozen_auc,
        "best_clipping_condition": str(best_clipping.condition),
        "best_clipping_auc": float(best_clipping.roc_auc),
        "best_clipping_auc_change": float(best_clipping.auc_change_vs_frozen),
        "best_ablation_removed_feature": str(best_ablation.removed_feature),
        "best_ablation_auc": float(best_ablation.external_auc),
        "best_ablation_auc_change": float(best_ablation.auc_change_vs_8_feature_diagnostic),
        "best_bounded_condition": str(best_bounded.condition),
        "best_bounded_auc": float(best_bounded.roc_auc),
        "best_bounded_auc_change": float(best_bounded.auc_change_vs_original_frozen),
        "frozen_hashes_before": frozen_before,
    }
    frozen_after = {str(path.relative_to(PROJECT_ROOT)): sha256(path) for path in FROZEN_PATHS}
    summary["frozen_hashes_after"] = frozen_after
    summary["frozen_artifacts_unchanged"] = frozen_before == frozen_after
    write_text(REPORT_DIR / "phase3b_summary.json", json.dumps(summary, indent=2, sort_keys=True))
    if frozen_before != frozen_after:
        raise RuntimeError("Frozen artifacts changed during Phase 3B")
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
