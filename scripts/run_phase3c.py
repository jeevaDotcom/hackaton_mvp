from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", "/tmp/qcare-phase3c-matplotlib-cache")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/qcare-phase3c-xdg-cache")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import pairwise_distances, roc_auc_score
from sklearn.preprocessing import MinMaxScaler, QuantileTransformer, RobustScaler
from qiskit_machine_learning.algorithms import QSVC

from src.phase1.data import TARGET, load_official_arff
from src.phase1.modeling import EXPERIMENT_SEED, make_preprocessor
from src.phase2.benchmark import CLASSIFIER_C, make_quantum_kernel
from src.phase3.validation import load_bd_kdd


FEATURES = ["hemo", "al", "dm", "sg", "pcv", "appet", "htn", "sc"]
NUMERIC = ["hemo", "al", "sg", "pcv", "sc"]
CATEGORY_ORDER = {"dm": ["no", "yes"], "appet": ["good", "poor"], "htn": ["no", "yes"]}
SIGNED_ENCODING = {"dm": "yes", "appet": "poor", "htn": "yes"}
REPORT_DIR = PROJECT_ROOT / "reports/root_cause"
FIGURE_DIR = REPORT_DIR / "figures"
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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n")


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


def json_ready(value: Any) -> Any:
    """Convert NumPy/pandas scalars and missing values to strict JSON values."""
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if value is None or value is pd.NA:
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    return value


def table(frame: pd.DataFrame, columns: list[str] | None = None, digits: int = 4) -> str:
    view = frame if columns is None else frame[columns]
    rows = []
    for record in view.itertuples(index=False, name=None):
        rows.append("| " + " | ".join(fmt(value, digits).replace("|", "\\|") for value in record) + " |")
    return "\n".join([
        "| " + " | ".join(str(value) for value in view.columns) + " |",
        "|" + "|".join("---" for _ in view.columns) + "|",
        *rows,
    ])


def z_kernel(left: np.ndarray, right: np.ndarray | None = None) -> np.ndarray:
    left = np.asarray(left, dtype=float)
    right = left if right is None else np.asarray(right, dtype=float)
    result = np.ones((len(left), len(right)), dtype=float)
    for column in range(left.shape[1]):
        result *= np.cos(left[:, None, column] - right[None, :, column]) ** 2
    return result


def centered_alignment(kernel: np.ndarray, target: np.ndarray) -> float:
    n = len(target)
    centre = np.eye(n) - np.ones((n, n)) / n
    kernel_centered = centre @ kernel @ centre
    signed = np.where(target == 1, 1.0, -1.0)
    target_centered = centre @ np.outer(signed, signed) @ centre
    denominator = np.linalg.norm(kernel_centered, "fro") * np.linalg.norm(target_centered, "fro")
    return float(np.sum(kernel_centered * target_centered) / denominator) if denominator else math.nan


def overlap_coefficient(left: np.ndarray, right: np.ndarray, bins: int = 50) -> float:
    values = np.concatenate([left, right])
    if np.isclose(values.min(), values.max()):
        return 1.0
    edges = np.linspace(values.min(), values.max(), bins + 1)
    first, _ = np.histogram(left, bins=edges, density=True)
    second, _ = np.histogram(right, bins=edges, density=True)
    return float(np.sum(np.minimum(first, second) * np.diff(edges)))


def bootstrap_auc(
    target: np.ndarray,
    scores: dict[str, np.ndarray],
    *,
    replicates: int,
    seed: int,
    block_size: int = 250,
) -> dict[str, np.ndarray]:
    """Class-stratified patient bootstrap with shared indices across score vectors."""
    target = np.asarray(target, dtype=int)
    negative = np.flatnonzero(target == 0)
    positive = np.flatnonzero(target == 1)
    rng = np.random.default_rng(seed)
    output = {name: np.empty(replicates, dtype=float) for name in scores}
    offset = 0
    while offset < replicates:
        size = min(block_size, replicates - offset)
        pos_draw = positive[rng.integers(0, len(positive), size=(size, len(positive)))]
        neg_draw = negative[rng.integers(0, len(negative), size=(size, len(negative)))]
        draw = np.concatenate([pos_draw, neg_draw], axis=1)
        for name, score in scores.items():
            sampled = np.asarray(score, dtype=float)[draw]
            ranks = stats.rankdata(sampled, axis=1, method="average")
            rank_sum_positive = ranks[:, : len(positive)].sum(axis=1)
            output[name][offset : offset + size] = (
                rank_sum_positive - len(positive) * (len(positive) + 1) / 2
            ) / (len(positive) * len(negative))
        offset += size
    return output


def auc_ci(values: np.ndarray) -> tuple[float, float]:
    return float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))


def profile_rows(dataset: str, frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label in (0, 1):
        group = frame[frame[TARGET] == label]
        label_name = "non-CKD" if label == 0 else "CKD"
        for feature in NUMERIC:
            values = group[feature].dropna().to_numpy(dtype=float)
            quantiles = np.quantile(values, [0.05, 0.25, 0.5, 0.75, 0.95])
            rows.append({
                "dataset": dataset, "label": label, "label_name": label_name, "feature": feature,
                "feature_type": "numeric", "category": "", "count": len(values),
                "missing_count": int(group[feature].isna().sum()), "category_count": math.nan,
                "proportion": math.nan, "mean": float(values.mean()), "sd": float(values.std(ddof=1)),
                "min": float(values.min()), "p5": float(quantiles[0]), "p25": float(quantiles[1]),
                "median": float(quantiles[2]), "p75": float(quantiles[3]), "p95": float(quantiles[4]),
                "max": float(values.max()),
            })
        for feature, categories in CATEGORY_ORDER.items():
            observed = group[feature].dropna()
            for category in categories:
                count = int((observed == category).sum())
                rows.append({
                    "dataset": dataset, "label": label, "label_name": label_name, "feature": feature,
                    "feature_type": "categorical", "category": category, "count": len(observed),
                    "missing_count": int(group[feature].isna().sum()), "category_count": count,
                    "proportion": float(count / len(observed)), "mean": math.nan, "sd": math.nan,
                    "min": math.nan, "p5": math.nan, "p25": math.nan, "median": math.nan,
                    "p75": math.nan, "p95": math.nan, "max": math.nan,
                })
    return rows


def signed_feature_values(frame: pd.DataFrame, feature: str) -> tuple[np.ndarray, np.ndarray, str]:
    if feature in NUMERIC:
        mask = frame[feature].notna().to_numpy()
        return frame.loc[mask, TARGET].to_numpy(dtype=int), frame.loc[mask, feature].to_numpy(dtype=float), "raw numeric; increasing value"
    positive_category = SIGNED_ENCODING[feature]
    mask = frame[feature].notna().to_numpy()
    values = (frame.loc[mask, feature] == positive_category).astype(float).to_numpy()
    return frame.loc[mask, TARGET].to_numpy(dtype=int), values, f"binary indicator: {positive_category}=1"


def classify_direction(auc: float, low: float, high: float, encoding: str) -> str:
    if low > 0.5:
        return f"positive ({encoding})"
    if high < 0.5:
        return f"negative ({encoding})"
    return "uncertain / includes random orientation"


def relationship_classification(uci: pd.Series, bd: pd.Series) -> str:
    uci_side = 1 if uci.ci95_low > 0.5 else (-1 if uci.ci95_high < 0.5 else 0)
    bd_side = 1 if bd.ci95_low > 0.5 else (-1 if bd.ci95_high < 0.5 else 0)
    if uci_side == 0:
        return "INCONCLUSIVE"
    if bd_side == -uci_side:
        return "REVERSED"
    if bd_side == 0:
        return "FLATTENED"
    if abs(bd.auc - 0.5) < 0.75 * abs(uci.auc - 0.5):
        return "WEAKENED"
    return "PRESERVED"


def kernel_information(name: str, kernel: np.ndarray, target: np.ndarray) -> tuple[dict[str, Any], np.ndarray]:
    upper = kernel[np.triu_indices_from(kernel, 1)]
    same = target[:, None] == target[None, :]
    triangular = np.triu(np.ones_like(kernel, dtype=bool), 1)
    within = kernel[triangular & same]
    between = kernel[triangular & ~same]
    eigenvalues = np.clip(np.linalg.eigvalsh((kernel + kernel.T) / 2), 0.0, None)
    positive = eigenvalues[eigenvalues > max(eigenvalues.max(), 1.0) * 1e-10]
    effective_rank = float(eigenvalues.sum() ** 2 / np.square(eigenvalues).sum())
    return ({
        "matrix": name, "n": len(target), "offdiag_mean": float(upper.mean()),
        "offdiag_median": float(np.median(upper)), "offdiag_sd": float(upper.std(ddof=1)),
        "offdiag_variance": float(upper.var(ddof=1)), "offdiag_p5": float(np.quantile(upper, 0.05)),
        "offdiag_p25": float(np.quantile(upper, 0.25)), "offdiag_p75": float(np.quantile(upper, 0.75)),
        "offdiag_p95": float(np.quantile(upper, 0.95)), "within_class_mean": float(within.mean()),
        "between_class_mean": float(between.mean()), "within_minus_between": float(within.mean() - between.mean()),
        "effective_rank": effective_rank, "numerical_rank": int(len(positive)),
        "condition_number_positive_spectrum": float(positive.max() / positive.min()) if len(positive) else math.nan,
        "top_eigenvalue_fraction": float(eigenvalues.max() / eigenvalues.sum()),
        "centered_kernel_target_alignment": centered_alignment(kernel, target),
    }, eigenvalues[::-1])


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    frozen_before = {str(path.relative_to(PROJECT_ROOT)): sha256(path) for path in FROZEN_PATHS}

    uci = load_official_arff(PROJECT_ROOT / "data/raw/chronic_kidney_disease.arff").frame.set_index("row_id")
    uci[TARGET] = uci[TARGET].astype(int)
    split = json.loads((PROJECT_ROOT / "artifacts/splits.json").read_text())
    development = uci.loc[split["development_row_ids"]].copy()
    bd_raw = pd.read_csv(PROJECT_ROOT / "data/external/raw/BD-KDD_Dataset.csv")
    bd = load_bd_kdd(PROJECT_ROOT / "data/external/raw/BD-KDD_Dataset.csv")

    classical_bundle = joblib.load(MODEL_PATHS["classical_rbf_svm"])
    qsvc_bundle = joblib.load(MODEL_PATHS["qsvc"])
    classical = classical_bundle["model"]
    qsvc = qsvc_bundle["model"]
    preprocessor = qsvc_bundle["preprocessor"]
    x_development = np.asarray(preprocessor.transform(development[FEATURES]), dtype=float)
    x_bd = np.asarray(preprocessor.transform(bd[FEATURES]), dtype=float)
    y_development = development[TARGET].to_numpy(dtype=int)
    y_bd = bd[TARGET].to_numpy(dtype=int)

    # Task 1: target profile.
    bd_counts = bd[TARGET].value_counts().sort_index()
    uci_counts = uci[TARGET].value_counts().sort_index()
    development_counts = development[TARGET].value_counts().sort_index()
    write_text(REPORT_DIR / "bd_kdd_target_profile.md", f"""# BD-KDD Target Profile

## BD-KDD

- Total records: **{len(bd)}**.
- Kidney disease (`1`): **{int(bd_counts[1])}**.
- Healthy/non-CKD (`0`): **{int(bd_counts[0])}**.
- Kidney-disease prevalence: **{100 * bd_counts[1] / len(bd):.2f}%**.
- Exact raw target labels: `{bd_raw['Class'].value_counts().sort_index().to_dict()}`.
- Canonical mapping: raw `0 → healthy/non-CKD → 0`; raw `1 → kidney disease → 1`.

## UCI comparison

- Full source cohort: **{len(uci)}**; CKD **{int(uci_counts[1])}**, non-CKD **{int(uci_counts[0])}**, CKD prevalence **{100 * uci_counts[1] / len(uci):.2f}%**.
- Frozen development cohort: **{len(development)}**; CKD **{int(development_counts[1])}**, non-CKD **{int(development_counts[0])}**, CKD prevalence **{100 * development_counts[1] / len(development):.2f}%**.
- Raw labels are `ckd` and `notckd`; whitespace is stripped before canonical `ckd → 1`, `notckd → 0` mapping.

The prevalence difference is descriptive. Prevalence alone neither proves nor disproves target comparability.
""")

    # Task 2: per-label profiles.
    profiles = pd.DataFrame(profile_rows("UCI full source cohort", uci) + profile_rows("BD-KDD", bd))
    profiles.to_csv(REPORT_DIR / "per_label_feature_profiles.csv", index=False)
    numeric_profiles = profiles[profiles.feature_type == "numeric"].copy()
    categorical_profiles = profiles[profiles.feature_type == "categorical"].copy()
    sc_profiles = numeric_profiles[numeric_profiles.feature == "sc"]
    write_text(REPORT_DIR / "per_label_feature_profiles.md", f"""# Per-Label Frozen-Feature Profiles

These descriptive profiles use the full 400-record UCI source cohort and all 988 BD-KDD records. They do not tune or evaluate a model.

## Numeric profiles

{table(numeric_profiles, ['dataset', 'label_name', 'feature', 'count', 'missing_count', 'mean', 'sd', 'min', 'p5', 'p25', 'median', 'p75', 'p95', 'max'])}

## Categorical class-conditional proportions

{table(categorical_profiles, ['dataset', 'label_name', 'feature', 'category', 'count', 'missing_count', 'category_count', 'proportion'])}

## Serum-creatinine medians

{table(sc_profiles, ['dataset', 'label_name', 'count', 'missing_count', 'median', 'p25', 'p75', 'min', 'max'])}
""")

    # Tasks 4–6: signed univariate AUC and relationship direction.
    univariate_rows = []
    univariate_bootstraps: dict[tuple[str, str], np.ndarray] = {}
    for dataset_name, frame in (("UCI full source cohort", uci), ("BD-KDD", bd)):
        for feature_index, feature in enumerate(FEATURES):
            target, values, encoding = signed_feature_values(frame, feature)
            point = float(roc_auc_score(target, values))
            boot = bootstrap_auc(target, {feature: values}, replicates=5000, seed=EXPERIMENT_SEED + feature_index + (0 if dataset_name.startswith("UCI") else 100))[feature]
            low, high = auc_ci(boot)
            univariate_bootstraps[(dataset_name, feature)] = boot
            univariate_rows.append({
                "dataset": dataset_name, "feature": feature, "method": encoding,
                "n_observed": len(values), "missing_count": int(len(frame) - len(values)),
                "auc": point, "ci95_low": low, "ci95_high": high,
                "direction": classify_direction(point, low, high, encoding),
                "ci_includes_0_5": bool(low <= 0.5 <= high),
            })
    univariate = pd.DataFrame(univariate_rows)
    relationship_rows = []
    for feature in FEATURES:
        u = univariate[(univariate.dataset == "UCI full source cohort") & (univariate.feature == feature)].iloc[0]
        b = univariate[(univariate.dataset == "BD-KDD") & (univariate.feature == feature)].iloc[0]
        classification = relationship_classification(u, b)
        relationship_rows.append({
            "feature": feature, "uci_auc": u.auc, "uci_ci95": f"[{u.ci95_low:.3f}, {u.ci95_high:.3f}]",
            "bd_auc": b.auc, "bd_ci95": f"[{b.ci95_low:.3f}, {b.ci95_high:.3f}]",
            "uci_direction": u.direction, "bd_direction": b.direction,
            "classification": classification,
            "interpretation": "Strong UCI association is not distinguishable from random orientation in BD-KDD." if classification == "FLATTENED" else "See signed AUC and intervals.",
        })
    relationships = pd.DataFrame(relationship_rows)
    univariate.to_csv(REPORT_DIR / "univariate_auc.csv", index=False)
    relationships.to_csv(REPORT_DIR / "feature_direction_analysis.csv", index=False)
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(FEATURES))
    for offset, dataset_name, colour in ((-0.15, "UCI full source cohort", "#2A6FBB"), (0.15, "BD-KDD", "#E67932")):
        subset = univariate[univariate.dataset == dataset_name].set_index("feature").loc[FEATURES]
        ax.errorbar(x + offset, subset.auc, yerr=[subset.auc - subset.ci95_low, subset.ci95_high - subset.auc], fmt="o", capsize=4, label=dataset_name, color=colour)
    ax.axhline(0.5, color="black", linestyle="--", linewidth=1)
    ax.set(xticks=x, xticklabels=FEATURES, ylim=(0, 1), ylabel="Signed univariate ROC-AUC", title="Within-dataset signed feature discrimination")
    ax.legend()
    save_figure(fig, "univariate_auc_signed.png")
    write_text(REPORT_DIR / "univariate_auc.md", f"""# Within-Dataset Signed Univariate AUC

## Method

Numeric variables use their raw increasing value as the score. Binary variables use `dm=yes`, `appet=poor`, and `htn=yes` as score 1. ROC-AUC for a binary score is the Mann–Whitney discriminatory probability and is an appropriate binary-feature equivalent. Missing values are excluded feature-by-feature. Confidence intervals are class-stratified, patient-level percentile bootstrap intervals from 5,000 replicates.

Signed orientation is retained: values below 0.5 are not automatically flipped.

{table(univariate)}

## UCI → BD-KDD direction classification

{table(relationships)}

## Monotonicity note

ROC-AUC depends only on ranking. A strictly increasing transformation—including positive-factor unit conversion, standardisation, min-max scaling, or another strictly monotonic map—preserves ranking and therefore preserves ROC-AUC. A strictly decreasing transformation reverses orientation, producing `1 − AUC` apart from ties. Non-monotonic transformations can change ranking. Consequently, a near-random within-BD-KDD univariate AUC cannot be rescued by ordinary positive unit conversion or scaling; it indicates absent/flattened ranking signal under that feature orientation, subject to its bootstrap uncertainty.

[Signed-AUC plot](figures/univariate_auc_signed.png)
""")

    # Tasks 7–8: external model/configuration bootstrap.
    score_sets: dict[str, np.ndarray] = {
        "Frozen classical RBF SVM": np.asarray(classical.decision_function(x_bd), dtype=float),
        "Frozen QSVC": np.asarray(qsvc.decision_function(x_bd), dtype=float),
    }
    p1, p99 = np.quantile(x_development, [0.01, 0.99], axis=0)
    clipped = np.clip(x_bd, p1, p99)
    score_sets["Frozen QSVC + diagnostic UCI p1/p99 clipping"] = np.asarray(qsvc.decision_function(clipped), dtype=float)

    base = make_preprocessor(FEATURES, scale=False)
    base_train = np.asarray(base.fit_transform(development[FEATURES], y_development), dtype=float)
    base_external = np.asarray(base.transform(bd[FEATURES]), dtype=float)
    bound = np.pi / 4
    minmax = MinMaxScaler(feature_range=(-bound, bound), clip=True).fit(base_train)
    robust = RobustScaler().fit(base_train)
    quantile = QuantileTransformer(n_quantiles=min(100, len(base_train)), output_distribution="uniform", random_state=EXPERIMENT_SEED).fit(base_train)
    transforms: dict[str, Callable[[np.ndarray], np.ndarray]] = {
        "Post-hoc bounded MinMax QSVC": lambda values: minmax.transform(values),
        "Post-hoc bounded robust-tanh QSVC": lambda values: bound * np.tanh(robust.transform(values)),
        "Post-hoc bounded quantile QSVC": lambda values: (2 * quantile.transform(values) - 1) * bound,
    }
    for name, transform in transforms.items():
        train_matrix, external_matrix = transform(base_train), transform(base_external)
        kernel, _ = make_quantum_kernel("z_reps1", train_matrix.shape[1], seed=EXPERIMENT_SEED)
        exploratory = QSVC(quantum_kernel=kernel, C=CLASSIFIER_C)
        exploratory.fit(train_matrix, y_development)
        score_sets[name] = np.asarray(exploratory.decision_function(external_matrix), dtype=float)

    external_boot = bootstrap_auc(y_bd, score_sets, replicates=10000, seed=EXPERIMENT_SEED + 500)
    external_rows = []
    for name, score in score_sets.items():
        point = float(roc_auc_score(y_bd, score))
        low, high = auc_ci(external_boot[name])
        external_rows.append({
            "configuration": name, "auc": point, "ci95_low": low, "ci95_high": high,
            "bootstrap_probability_auc_above_0_5": float(np.mean(external_boot[name] > 0.5)),
            "random_discrimination_assessment": "INDISTINGUISHABLE FROM RANDOM" if low <= 0.5 <= high else ("WEAK EVIDENCE ABOVE RANDOM" if low > 0.5 else "WEAK EVIDENCE BELOW RANDOM"),
        })
    external_auc = pd.DataFrame(external_rows)
    delta = external_boot["Frozen QSVC"] - external_boot["Frozen classical RBF SVM"]
    delta_point = float(roc_auc_score(y_bd, score_sets["Frozen QSVC"]) - roc_auc_score(y_bd, score_sets["Frozen classical RBF SVM"]))
    delta_low, delta_high = auc_ci(delta)
    external_auc.to_csv(REPORT_DIR / "external_auc_bootstrap.csv", index=False)
    fig, ax = plt.subplots(figsize=(11, 5.5))
    positions = np.arange(len(external_auc))
    ax.errorbar(positions, external_auc.auc, yerr=[external_auc.auc - external_auc.ci95_low, external_auc.ci95_high - external_auc.auc], fmt="o", capsize=5)
    ax.axhline(0.5, color="black", linestyle="--", linewidth=1)
    ax.set(xticks=positions, xticklabels=external_auc.configuration, ylim=(0.4, 0.6), ylabel="BD-KDD ROC-AUC", title="Paired patient-bootstrap external uncertainty")
    ax.tick_params(axis="x", rotation=30)
    save_figure(fig, "external_auc_bootstrap.png")
    write_text(REPORT_DIR / "external_auc_bootstrap.md", f"""# External ROC-AUC Bootstrap Audit

## Method

The audit uses 10,000 class-stratified patient-level bootstrap replicates. Identical sampled patient indices are used for every configuration, so QSVC–SVM differences are paired. Percentile 95% confidence intervals are descriptive uncertainty intervals for this fixed BD-KDD cohort.

{table(external_auc)}

## Paired frozen-model difference

- Point estimate, QSVC − SVM: **{delta_point:+.4f}**.
- 95% bootstrap CI: **[{delta_low:+.4f}, {delta_high:+.4f}]**.
- Bootstrap portion above zero: **{100 * np.mean(delta > 0):.1f}%**.
- The interval {'includes' if delta_low <= 0 <= delta_high else 'does not include'} zero.

**Conclusion:** 0.525 and 0.511 are not presented as a quantum benefit. {'All tested configurations have intervals containing 0.5; no tested configuration demonstrated reliable better-than-random external discrimination.' if all((row.ci95_low <= 0.5 <= row.ci95_high) for row in external_auc.itertuples()) else 'See configuration-specific assessments above.'}

[Bootstrap interval plot](figures/external_auc_bootstrap.png)
""")

    # Tasks 9–10: full external and internal kernel information.
    quantum_uci = z_kernel(x_development)
    quantum_bd = z_kernel(x_bd)
    q_uci_summary, q_uci_eigen = kernel_information("QSVC UCI development", quantum_uci, y_development)
    q_bd_summary, q_bd_eigen = kernel_information("QSVC BD-KDD", quantum_bd, y_bd)
    quantum_summary = pd.DataFrame([q_uci_summary, q_bd_summary])
    gamma = float(classical._gamma)
    rbf_uci = np.exp(-gamma * pairwise_distances(x_development, squared=True))
    rbf_bd = np.exp(-gamma * pairwise_distances(x_bd, squared=True))
    r_uci_summary, r_uci_eigen = kernel_information("RBF UCI development", rbf_uci, y_development)
    r_bd_summary, r_bd_eigen = kernel_information("RBF BD-KDD", rbf_bd, y_bd)
    rbf_summary = pd.DataFrame([r_uci_summary, r_bd_summary])
    eigen_rows = []
    for matrix, values in (("QSVC UCI development", q_uci_eigen), ("QSVC BD-KDD", q_bd_eigen), ("RBF UCI development", r_uci_eigen), ("RBF BD-KDD", r_bd_eigen)):
        for rank, value in enumerate(values, start=1):
            eigen_rows.append({"matrix": matrix, "rank": rank, "eigenvalue": float(value)})
    pd.DataFrame(eigen_rows).to_csv(REPORT_DIR / "kernel_eigenvalue_spectra.csv", index=False)
    write_text(REPORT_DIR / "kernel_information_content.md", f"""# QSVC Kernel Information Content

The exact full-cohort kernel was computed analytically as `∏ cos²(xᵢ−yᵢ)`, previously verified against the persisted Qiskit `FidelityQuantumKernel` to maximum absolute error `3.19×10⁻¹³`.

{table(quantum_summary)}

The external kernel has high effective rank but almost no label-aligned separation: high rank here indicates many near-orthogonal directions, not useful target information. The positive-spectrum condition number excludes eigenvalues below `1e-10 × max(eigenvalue)` and should be interpreted only as a numerical descriptor. The full ordered spectrum is in `kernel_eigenvalue_spectra.csv`.

This distinguishes gross collisions from low-separation geometry: Phase 3B found zero high-distance/fidelity≥0.95 representative collisions, while Phase 3C shows generally uninformative external class geometry.
""")

    score_geometry_rows = []
    for model_name, estimator in (("Frozen RBF SVM", classical), ("Frozen QSVC", qsvc)):
        for cohort, matrix, target in (("UCI development (training diagnostic)", x_development, y_development), ("BD-KDD", x_bd, y_bd)):
            scores = np.asarray(estimator.decision_function(matrix), dtype=float)
            positive, negative = scores[target == 1], scores[target == 0]
            score_geometry_rows.append({
                "model": model_name, "cohort": cohort, "ckd_median_score": float(np.median(positive)),
                "non_ckd_median_score": float(np.median(negative)), "score_overlap_coefficient": overlap_coefficient(positive, negative),
                "fraction_non_ckd_above_boundary": float(np.mean(negative >= 0)), "fraction_ckd_above_boundary": float(np.mean(positive >= 0)),
                "auc": float(roc_auc_score(target, scores)),
            })
    score_geometry = pd.DataFrame(score_geometry_rows)
    write_text(REPORT_DIR / "classical_geometry.md", f"""# Classical RBF Geometry Comparison

The frozen RBF kernel uses `gamma={gamma:.8f}` on the same frozen scaled representation.

## Kernel geometry

{table(rbf_summary)}

## Decision-score geometry compared with QSVC

{table(score_geometry)}

Both model families lose within-versus-between-class similarity separation and develop heavy class-score overlap on BD-KDD. This supports loss of usable feature-label geometry shared across kernels rather than a quantum-only mechanism.

The full RBF and QSVC eigenvalue spectra are in `kernel_eigenvalue_spectra.csv`.
""")

    # Task 12: creatinine deep dive.
    sc_uni = univariate[univariate.feature == "sc"]
    sc_rows = profiles[(profiles.feature == "sc") & (profiles.feature_type == "numeric")]
    overlap_rows = []
    for dataset_name, frame in (("UCI full source cohort", uci), ("BD-KDD", bd)):
        negative = frame.loc[(frame[TARGET] == 0) & frame.sc.notna(), "sc"].to_numpy(dtype=float)
        positive = frame.loc[(frame[TARGET] == 1) & frame.sc.notna(), "sc"].to_numpy(dtype=float)
        overlap_rows.append({"dataset": dataset_name, "histogram_overlap_coefficient": overlap_coefficient(positive, negative), "non_ckd_missing_pct": float(100 * frame.loc[frame[TARGET] == 0, "sc"].isna().mean()), "ckd_missing_pct": float(100 * frame.loc[frame[TARGET] == 1, "sc"].isna().mean())})
    overlap_frame = pd.DataFrame(overlap_rows)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, (dataset_name, frame) in zip(axes, (("UCI full source cohort", uci), ("BD-KDD", bd)), strict=True):
        ax.hist(frame.loc[(frame[TARGET] == 0) & frame.sc.notna(), "sc"], bins=35, density=True, alpha=0.55, label="non-CKD")
        ax.hist(frame.loc[(frame[TARGET] == 1) & frame.sc.notna(), "sc"], bins=35, density=True, alpha=0.55, label="CKD")
        ax.set(title=dataset_name, xlabel="Serum creatinine (documented mg/dL)", ylabel="Density")
    axes[0].legend()
    save_figure(fig, "serum_creatinine_by_label.png")
    write_text(REPORT_DIR / "serum_creatinine_deep_dive.md", f"""# Serum Creatinine Deep Dive

## Per-label distribution

{table(sc_rows, ['dataset', 'label_name', 'count', 'missing_count', 'mean', 'sd', 'min', 'p5', 'p25', 'median', 'p75', 'p95', 'max'])}

## Signed within-dataset AUC

Higher raw serum creatinine is the score orientation.

{table(sc_uni, ['dataset', 'n_observed', 'missing_count', 'auc', 'ci95_low', 'ci95_high', 'direction'])}

## Distribution overlap and missingness

{table(overlap_frame)}

UCI documents serum creatinine as `mgs/dl`; BD-KDD documents `mg/dL`, so unit confidence is high. No CKD stage is assigned: staging requires renal-function and chronicity evidence that cannot be derived from one creatinine value. The BD-KDD medians show that both labelled groups occupy a substantially higher and far more overlapping creatinine distribution than the UCI non-CKD/CKD contrast, consistent with a materially different renal-function cohort or label/cohort construction.

[Serum-creatinine distributions](figures/serum_creatinine_by_label.png)
""")

    summary = {
        "bd": {"total": len(bd), "ckd": int(bd_counts[1]), "non_ckd": int(bd_counts[0]), "prevalence": float(bd_counts[1] / len(bd))},
        "uci_full": {"total": len(uci), "ckd": int(uci_counts[1]), "non_ckd": int(uci_counts[0]), "prevalence": float(uci_counts[1] / len(uci))},
        "univariate": univariate.to_dict(orient="records"),
        "relationships": relationships.to_dict(orient="records"),
        "external_auc": external_auc.to_dict(orient="records"),
        "paired_delta": {"point": delta_point, "ci95_low": delta_low, "ci95_high": delta_high, "probability_above_zero": float(np.mean(delta > 0))},
        "quantum_kernel": quantum_summary.to_dict(orient="records"),
        "classical_kernel": rbf_summary.to_dict(orient="records"),
        "serum_creatinine_profiles": sc_rows.to_dict(orient="records"),
        "frozen_hashes_before": frozen_before,
    }
    frozen_after = {str(path.relative_to(PROJECT_ROOT)): sha256(path) for path in FROZEN_PATHS}
    summary["frozen_hashes_after"] = frozen_after
    summary["frozen_artifacts_unchanged"] = frozen_before == frozen_after
    write_text(
        REPORT_DIR / "phase3c_summary.json",
        json.dumps(json_ready(summary), indent=2, sort_keys=True, allow_nan=False),
    )
    if frozen_before != frozen_after:
        raise RuntimeError("Frozen artifacts changed during Phase 3C")
    print(json.dumps({
        "bd_counts": summary["bd"], "uci_counts": summary["uci_full"],
        "paired_delta": summary["paired_delta"], "frozen_artifacts_unchanged": summary["frozen_artifacts_unchanged"],
        "external_auc": summary["external_auc"], "relationships": summary["relationships"],
        "quantum_kernel": summary["quantum_kernel"],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
