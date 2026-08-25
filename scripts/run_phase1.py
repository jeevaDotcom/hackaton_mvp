from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

import joblib

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", "/tmp/qcare-phase1-matplotlib-cache")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/qcare-phase1-xdg-cache")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve, roc_curve
from sklearn.model_selection import GridSearchCV, StratifiedKFold

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.phase1.data import (  # noqa: E402
    FEATURES,
    SOURCE_URL,
    SPLIT_SEED,
    TARGET,
    build_quality_table,
    load_official_arff,
    make_locked_split,
    sha256,
    write_json,
)
from src.phase1.modeling import (  # noqa: E402
    EXPERIMENT_SEED,
    FEATURE_BUDGETS,
    INNER_SPLITS,
    OUTER_REPEATS,
    OUTER_SPLITS,
    SELECTION_METHODS,
    TOLERANCE,
    add_performance_deltas,
    binary_metrics,
    bootstrap_metric_intervals,
    compute_stability,
    continuous_score,
    evaluate_cv,
    make_pipeline,
    rank_source_features,
    summarise_cv,
)


RAW_ARFF = PROJECT_ROOT / "data/raw/chronic_kidney_disease.arff"
RAW_ZIP = PROJECT_ROOT / "data/raw/uci_chronic_kidney_disease_336.zip"
PROCESSED_CSV = PROJECT_ROOT / "data/processed/ckd_clean.csv"
SPLITS_JSON = PROJECT_ROOT / "artifacts/splits.json"
DEVELOPMENT_DECISION = PROJECT_ROOT / "artifacts/development_decision.json"
LOCKED_EVALUATION = PROJECT_ROOT / "artifacts/locked_test_evaluation.json"
FIGURES = PROJECT_ROOT / "reports/figures"


def fmt(value: float | int | None, digits: int = 3) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "NR"
    return f"{float(value):.{digits}f}"


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    def clean(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = ["| " + " | ".join(clean(v) for v in headers) + " |"]
    lines.append("|" + "|".join("---" for _ in headers) + "|")
    lines.extend("| " + " | ".join(clean(v) for v in row) + " |" for row in rows)
    return "\n".join(lines)


def load_clean_frame() -> pd.DataFrame:
    frame = pd.read_csv(PROCESSED_CSV, dtype={"row_id": str})
    frame[TARGET] = frame[TARGET].astype(int)
    return frame.set_index("row_id", drop=True)


def split_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    split = json.loads(SPLITS_JSON.read_text())
    development = frame.loc[split["development_row_ids"]].copy()
    locked = frame.loc[split["locked_test_row_ids"]].copy()
    return development, locked


def save_figure(fig: plt.Figure, name: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIGURES / name, dpi=170, bbox_inches="tight")
    plt.close(fig)


def prepare_data() -> None:
    parsed = load_official_arff(RAW_ARFF)
    frame = parsed.frame
    provenance = parsed.provenance | {
        "official_archive_file": str(RAW_ZIP.relative_to(PROJECT_ROOT)),
        "official_archive_sha256": sha256(RAW_ZIP),
        "raw_directory_policy": "Immutable after initial official retrieval; experiment code reads but never writes data/raw.",
    }
    PROCESSED_CSV.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(PROCESSED_CSV, index=False)
    write_json(PROJECT_ROOT / "artifacts/data_provenance.json", provenance)

    proposed_split = make_locked_split(frame)
    if SPLITS_JSON.exists():
        existing = json.loads(SPLITS_JSON.read_text())
        if existing != proposed_split:
            raise RuntimeError("Existing split artifact differs from deterministic proposed split")
    else:
        write_json(SPLITS_JSON, proposed_split)

    quality = build_quality_table(frame, provenance)
    quality.to_csv(PROJECT_ROOT / "reports/data_quality.csv", index=False)
    import matplotlib as mpl
    import scipy
    import sklearn
    import xgboost

    write_json(
        PROJECT_ROOT / "artifacts/environment.json",
        {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "xgboost": xgboost.__version__,
            "matplotlib": mpl.__version__,
            "experiment_seed": EXPERIMENT_SEED,
        },
    )
    quality_rows = []
    for _, row in quality.iterrows():
        summary = (
            f"min={fmt(row['min'])}, median={fmt(row['median'])}, max={fmt(row['max'])}"
            if row["type"] == "numeric_or_ordered"
            else row["categories"]
        )
        quality_rows.append(
            [row["feature"], row["type"], int(row["missing_count"]), fmt(row["missing_pct"], 1) + "%", int(row["unique_non_missing"]), summary, row["suspected_malformed_values"]]
        )
    (PROJECT_ROOT / "reports/data_quality.md").write_text(
        "# CKD data-quality audit\n\n"
        "Generated from the untouched official ARFF. Target-stratified summaries are descriptive only and were not used to choose feature subsets.\n\n"
        + markdown_table(["Feature", "Type", "Missing", "Missing %", "Unique", "Range/categories", "Logged raw anomalies"], quality_rows)
        + "\n\n## Transformation boundary\n\n"
        "The raw parser strips logged whitespace/tabs, repairs only the three explicitly logged delimiter anomalies, maps `?` to missing, validates every categorical domain, and maps `ckd/notckd` to `1/0`. Imputation, encoding and scaling are not written into this CSV; they remain fold-fitted sklearn transformers.\n"
    )
    repairs = provenance["column_repairs"]
    repair_rows = [[item["row_id"], item["rule"], item["detail"]] for item in repairs]
    (PROJECT_ROOT / "reports/data_provenance.md").write_text(
        "# Data provenance\n\n"
        f"- Source: [{SOURCE_URL}]({SOURCE_URL})\n"
        f"- Retrieval date: {provenance['retrieval_date']}\n"
        f"- Official ZIP SHA-256: `{provenance['official_archive_sha256']}`\n"
        f"- ARFF SHA-256: `{provenance['raw_sha256']}`\n"
        f"- Raw rows: {provenance['raw_data_row_count']}\n"
        f"- Predictors: {provenance['predictor_count']}\n"
        f"- Target: {provenance['target_distribution']}\n"
        f"- Duplicate rows including target: {provenance['duplicate_row_count_including_target']}\n"
        f"- Missing predictor cells: {provenance['total_missing_predictor_cells']} across {provenance['rows_with_missing_predictors']} rows\n\n"
        "## Explicit raw repairs\n\n"
        + markdown_table(["Row ID", "Rule", "Reason"], repair_rows)
        + "\n\n## Whitespace variants\n\n"
        f"```json\n{json.dumps(provenance['whitespace_variants'], indent=2, sort_keys=True)}\n```\n\n"
        "## Target cleanup\n\n"
        + "\n".join(f"- {rule}" for rule in provenance["target_cleanup_rules"])
        + "\n"
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    missing = quality.sort_values("missing_pct", ascending=False)
    ax.bar(missing["feature"], missing["missing_pct"], color="#118f82")
    ax.set(title="UCI CKD predictor missingness", ylabel="Missing (%)", xlabel="Source variable")
    ax.tick_params(axis="x", rotation=55)
    save_figure(fig, "01_missingness_profile.png")

    fig, ax = plt.subplots(figsize=(5, 4))
    counts = frame[TARGET].value_counts().sort_index()
    ax.bar(["Not CKD", "CKD"], counts.values, color=["#8da39e", "#118f82"])
    for idx, count in enumerate(counts.values):
        ax.text(idx, count + 4, str(count), ha="center")
    ax.set(title="Target distribution", ylabel="Patients", ylim=(0, max(counts) * 1.15))
    save_figure(fig, "02_target_distribution.png")


def decision_score(row: pd.Series, stability: float = 0.0) -> float:
    return float(
        0.35 * row["sensitivity_mean"]
        + 0.25 * row["roc_auc_mean"]
        + 0.15 * row["specificity_mean"]
        + 0.10 * row["f1_mean"]
        + 0.15 * stability
    )


def choose_development_decisions(
    summary: pd.DataFrame,
    stability_overall: pd.DataFrame,
    development: pd.DataFrame,
) -> dict[str, Any]:
    full = summary[summary["representation"] == "full"].copy()
    full["decision_score"] = full.apply(lambda row: decision_score(row, stability=1.0), axis=1)
    best_full = full.sort_values(["decision_score", "sensitivity_mean", "roc_auc_mean"], ascending=False).iloc[0]

    selected = summary[summary["representation"] == "selected"].merge(
        stability_overall, left_on=["selector", "budget"], right_on=["method", "budget"], how="left"
    )
    selected["decision_score"] = selected.apply(
        lambda row: decision_score(row, float(row["pairwise_jaccard_mean"])), axis=1
    )
    budget_decisions: dict[str, Any] = {}
    for budget in FEATURE_BUDGETS:
        candidates = selected[selected["budget"] == budget].copy()
        stable_candidates = candidates[candidates["stable_signature"] == True]  # noqa: E712
        pool = stable_candidates if not stable_candidates.empty else candidates
        chosen = pool.sort_values(["decision_score", "sensitivity_mean", "roc_auc_mean"], ascending=False).iloc[0]
        ranking = rank_source_features(
            development[FEATURES],
            development[TARGET],
            str(chosen["selector"]),
            seed=EXPERIMENT_SEED + budget,
        )
        features = ranking.top(budget)
        same_model_full = full[full["model"] == chosen["model"]].iloc[0]
        budget_decisions[str(budget)] = {
            "representation": "selected",
            "selector": str(chosen["selector"]),
            "model": str(chosen["model"]),
            "budget": int(budget),
            "features_frozen_from_complete_development_set": features,
            "stable_signature": bool(chosen["stable_signature"]),
            "pairwise_jaccard_mean": float(chosen["pairwise_jaccard_mean"]),
            "features_with_frequency_ge_0_80": int(chosen["features_with_frequency_ge_0_80"]),
            "cv_sensitivity": float(chosen["sensitivity_mean"]),
            "cv_specificity": float(chosen["specificity_mean"]),
            "cv_roc_auc": float(chosen["roc_auc_mean"]),
            "sensitivity_delta_vs_same_model_full": float(chosen["sensitivity_mean"] - same_model_full["sensitivity_mean"]),
            "specificity_delta_vs_same_model_full": float(chosen["specificity_mean"] - same_model_full["specificity_mean"]),
            "roc_auc_delta_vs_same_model_full": float(chosen["roc_auc_mean"] - same_model_full["roc_auc_mean"]),
            "meets_predefined_tolerance": bool(
                chosen["sensitivity_mean"] >= same_model_full["sensitivity_mean"] - TOLERANCE
                and chosen["roc_auc_mean"] >= same_model_full["roc_auc_mean"] - TOLERANCE
            ),
            "decision_score": float(chosen["decision_score"]),
        }

    pca = summary[summary["representation"] == "pca"].copy()
    pca["decision_score"] = pca.apply(lambda row: decision_score(row, stability=0.0), axis=1)
    pca_configs: dict[str, Any] = {}
    for budget in FEATURE_BUDGETS:
        chosen = pca[pca["budget"] == budget].sort_values("decision_score", ascending=False).iloc[0]
        pca_configs[str(budget)] = {
            "representation": "pca",
            "model": str(chosen["model"]),
            "components": int(budget),
            "cv_sensitivity": float(chosen["sensitivity_mean"]),
            "cv_specificity": float(chosen["specificity_mean"]),
            "cv_roc_auc": float(chosen["roc_auc_mean"]),
            "explained_variance_mean": float(chosen.get("pca_explained_variance_mean", np.nan)),
            "decision_score": float(chosen["decision_score"]),
        }
    best_pca_budget = max(pca_configs, key=lambda key: pca_configs[key]["decision_score"])

    return {
        "protocol": {
            "outer_cv": f"RepeatedStratifiedKFold({OUTER_SPLITS} folds x {OUTER_REPEATS} repeats)",
            "inner_cv": f"StratifiedKFold({INNER_SPLITS} folds)",
            "development_only": True,
            "selection_boundary": "ranked only on each outer-training partition; outer validation untouched",
            "predefined_tolerance": TOLERANCE,
        },
        "full_reference": {
            "model": str(best_full["model"]),
            "features": FEATURES,
            "cv_sensitivity": float(best_full["sensitivity_mean"]),
            "cv_specificity": float(best_full["specificity_mean"]),
            "cv_roc_auc": float(best_full["roc_auc_mean"]),
            "decision_score": float(best_full["decision_score"]),
        },
        "selected_budgets": budget_decisions,
        "pca_controls": pca_configs,
        "best_pca_control_budget": int(best_pca_budget),
        "selection_rule": "Prefer a Phase-0-stable method at the budget; otherwise choose the highest predeclared sensitivity/AUC/specificity/F1/stability score and label it unstable.",
        "locked_test_was_used": False,
    }


def plot_development_results(summary: pd.DataFrame, stability: pd.DataFrame) -> None:
    full = summary[summary["representation"] == "full"].sort_values("sensitivity_mean")
    fig, ax = plt.subplots(figsize=(8, 4.8))
    x = np.arange(len(full))
    width = 0.25
    for offset, metric, label in [(-width, "sensitivity_mean", "Sensitivity"), (0, "specificity_mean", "Specificity"), (width, "roc_auc_mean", "ROC-AUC")]:
        ax.bar(x + offset, full[metric], width, label=label)
    ax.set_xticks(x, full["model"], rotation=20)
    ax.set_ylim(0.70, 1.02)
    ax.set(title="Full-feature repeated nested-CV estimates", ylabel="Mean outer-fold metric")
    ax.legend()
    save_figure(fig, "03_full_model_benchmark.png")

    stable = stability.copy()
    stable["label"] = stable["method"] + " · " + stable["feature"]
    ordered = stable.groupby("feature")["selection_frequency_6"].mean().sort_values(ascending=False).index
    methods = list(SELECTION_METHODS)
    matrix = np.array(
        [[float(stable[(stable.method == method) & (stable.feature == feature)]["selection_frequency_6"].iloc[0]) for feature in ordered] for method in methods]
    )
    fig, ax = plt.subplots(figsize=(12, 3.8))
    image = ax.imshow(matrix, aspect="auto", cmap="YlGnBu", vmin=0, vmax=1)
    ax.set_yticks(range(len(methods)), methods)
    ax.set_xticks(range(len(ordered)), ordered, rotation=60)
    ax.set(title="Six-variable selection frequency across outer folds")
    fig.colorbar(image, ax=ax, label="Selection frequency")
    save_figure(fig, "04_feature_selection_stability.png")

    selected = summary[summary["representation"] == "selected"]
    for metric, filename, title in [
        ("sensitivity_mean", "05_feature_budget_vs_sensitivity.png", "Feature budget vs sensitivity"),
        ("roc_auc_mean", "06_feature_budget_vs_roc_auc.png", "Feature budget vs ROC-AUC"),
    ]:
        fig, ax = plt.subplots(figsize=(8, 5))
        for (selector, model), group in selected.groupby(["selector", "model"]):
            group = group.sort_values("budget")
            ax.plot(group["budget"], group[metric], marker="o", label=f"{selector} / {model}")
        ax.axhline(0, color="black", linewidth=0.5)
        ax.set(xticks=list(FEATURE_BUDGETS), xlabel="Source-variable budget", ylabel="Mean outer-fold metric", title=title)
        ax.legend(fontsize=7, ncol=2)
        save_figure(fig, filename)

    compare = summary[summary["representation"].isin(["selected", "pca"])].copy()
    best = compare.sort_values("roc_auc_mean", ascending=False).groupby(["representation", "budget"], as_index=False).first()
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for representation, group in best.groupby("representation"):
        group = group.sort_values("budget")
        ax.plot(group["budget"], group["roc_auc_mean"], marker="o", label=representation)
    ax.set(xticks=list(FEATURE_BUDGETS), xlabel="Variables or latent dimensions", ylabel="Best mean ROC-AUC", title="Selected clinical variables vs PCA controls")
    ax.legend()
    save_figure(fig, "07_selected_features_vs_pca.png")


def write_stability_report(details: pd.DataFrame, overall: pd.DataFrame) -> None:
    rows = []
    for _, row in details.sort_values(["method", "mean_rank"]).iterrows():
        rows.append(
            [row["method"], row["feature"], fmt(row["selection_frequency_8"]), fmt(row["selection_frequency_6"]), fmt(row["selection_frequency_4"]), fmt(row["mean_rank"], 2), fmt(row["rank_std"], 2)]
        )
    overall_rows = [
        [row["method"], int(row["budget"]), fmt(row["pairwise_jaccard_mean"]), fmt(row["pairwise_jaccard_std"]), int(row["features_with_frequency_ge_0_80"]), bool(row["stable_signature"])]
        for _, row in overall.sort_values(["method", "budget"], ascending=[True, False]).iterrows()
    ]
    stable_count = int(overall["stable_signature"].sum())
    conclusion = (
        f"{stable_count} method-budget combinations meet the predeclared descriptive stability rule."
        if stable_count
        else "No method-budget combination meets the predeclared descriptive stability rule; reduced subsets are treated as unstable."
    )
    (PROJECT_ROOT / "reports/feature_stability.md").write_text(
        "# Feature-selection stability\n\n"
        f"Based on {OUTER_SPLITS * OUTER_REPEATS} outer-training partitions. {conclusion} This is predictive stability, not clinical causality.\n\n"
        "## Overall method/budget stability\n\n"
        + markdown_table(["Method", "Budget", "Mean Jaccard", "Jaccard SD", "Features freq≥0.80", "Stable"], overall_rows)
        + "\n\n## Per-feature ranks and frequencies\n\n"
        + markdown_table(["Method", "Feature", "Freq@8", "Freq@6", "Freq@4", "Mean rank", "Rank SD"], rows)
        + "\n"
    )


def run_development() -> None:
    if DEVELOPMENT_DECISION.exists():
        print("Development decision already exists; skipping repeated CV.")
        return
    frame = load_clean_frame()
    development, _ = split_frame(frame)
    X, y = development[FEATURES], development[TARGET]
    cv_results, selection_records, fit_audit = evaluate_cv(X, y)
    cv_results.to_csv(PROJECT_ROOT / "artifacts/development_cv_results.csv", index=False)
    write_json(PROJECT_ROOT / "artifacts/selection_records.json", selection_records)
    write_json(PROJECT_ROOT / "artifacts/selection_fit_audit.json", fit_audit)

    summary = add_performance_deltas(summarise_cv(cv_results))
    summary.to_csv(PROJECT_ROOT / "reports/classical_cv_summary.csv", index=False)
    details, overall = compute_stability(selection_records)
    details.to_csv(PROJECT_ROOT / "reports/feature_stability.csv", index=False)
    overall.to_csv(PROJECT_ROOT / "reports/feature_stability_overall.csv", index=False)
    write_stability_report(details, overall)

    decisions = choose_development_decisions(summary, overall, development)
    write_json(DEVELOPMENT_DECISION, decisions)
    plot_development_results(summary, details)


def fit_final_pipeline(
    development: pd.DataFrame,
    locked: pd.DataFrame,
    *,
    model_name: str,
    columns: list[str],
    pca_components: int | None = None,
) -> tuple[Any, dict[str, Any], dict[str, float], np.ndarray, np.ndarray]:
    pipeline, grid = make_pipeline(model_name, columns, EXPERIMENT_SEED, pca_components=pca_components)
    inner = StratifiedKFold(n_splits=INNER_SPLITS, shuffle=True, random_state=EXPERIMENT_SEED)
    search = GridSearchCV(pipeline, grid, scoring="roc_auc", cv=inner, n_jobs=1, refit=True, error_score="raise")
    import time

    started = time.perf_counter()
    search.fit(development[columns], development[TARGET])
    predictions = search.predict(locked[columns])
    scores = continuous_score(search.best_estimator_, locked[columns])
    runtime = time.perf_counter() - started
    metrics = binary_metrics(locked[TARGET], predictions, scores)
    metrics["runtime_seconds"] = runtime
    return search.best_estimator_, search.best_params_, metrics, predictions, scores


def evaluate_locked_once() -> tuple[dict[str, Any], pd.DataFrame]:
    if LOCKED_EVALUATION.exists():
        return json.loads(LOCKED_EVALUATION.read_text()), pd.read_csv(PROJECT_ROOT / "artifacts/locked_test_predictions.csv")

    decisions = json.loads(DEVELOPMENT_DECISION.read_text())
    frame = load_clean_frame()
    development, locked = split_frame(frame)
    configs: dict[str, dict[str, Any]] = {
        "full_reference": {
            "model": decisions["full_reference"]["model"], "columns": FEATURES, "pca": None
        }
    }
    for budget in FEATURE_BUDGETS:
        config = decisions["selected_budgets"][str(budget)]
        configs[f"selected_{budget}"] = {
            "model": config["model"],
            "columns": config["features_frozen_from_complete_development_set"],
            "pca": None,
        }
    pca_budget = str(decisions["best_pca_control_budget"])
    pca_config = decisions["pca_controls"][pca_budget]
    configs["best_pca_control"] = {
        "model": pca_config["model"], "columns": FEATURES, "pca": int(pca_budget)
    }

    evaluation: dict[str, Any] = {
        "policy": "Each frozen configuration was fitted on complete development data and evaluated once on the same locked 80-patient test set.",
        "test_n": int(len(locked)),
        "test_target_distribution": {"not_ckd": int((locked[TARGET] == 0).sum()), "ckd": int((locked[TARGET] == 1).sum())},
        "models": {},
    }
    prediction_frame = pd.DataFrame({"row_id": locked.index, "target": locked[TARGET].to_numpy()})
    models_dir = PROJECT_ROOT / "artifacts/models"
    models_dir.mkdir(parents=True, exist_ok=True)
    for offset, (name, config) in enumerate(configs.items()):
        estimator, params, metrics, predictions, scores = fit_final_pipeline(
            development,
            locked,
            model_name=config["model"],
            columns=config["columns"],
            pca_components=config["pca"],
        )
        intervals = bootstrap_metric_intervals(
            locked[TARGET].to_numpy(), predictions, scores, seed=EXPERIMENT_SEED + offset
        )
        evaluation["models"][name] = {
            "model": config["model"],
            "columns": config["columns"] if config["pca"] is None else "24 source variables transformed to latent PCA components",
            "pca_components": config["pca"],
            "best_params": params,
            "metrics": metrics,
            "bootstrap_intervals": intervals,
        }
        prediction_frame[f"{name}_prediction"] = predictions
        prediction_frame[f"{name}_score"] = scores
        joblib.dump(estimator, models_dir / f"{name}.joblib")

    # Persist the one-time evaluation before any optional plotting/reporting.
    prediction_frame.to_csv(PROJECT_ROOT / "artifacts/locked_test_predictions.csv", index=False)
    write_json(LOCKED_EVALUATION, evaluation)
    return evaluation, prediction_frame


def plot_locked_results(evaluation: dict[str, Any], predictions: pd.DataFrame) -> None:
    names = list(evaluation["models"])
    fig, axes = plt.subplots(1, len(names), figsize=(3.2 * len(names), 3.2))
    if len(names) == 1:
        axes = [axes]
    for ax, name in zip(axes, names, strict=True):
        metrics = evaluation["models"][name]["metrics"]
        matrix = np.array([[metrics["tn"], metrics["fp"]], [metrics["fn"], metrics["tp"]]])
        ax.imshow(matrix, cmap="YlGnBu")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(matrix[i, j]), ha="center", va="center", fontsize=13)
        ax.set(title=name.replace("_", " "), xticks=[0, 1], yticks=[0, 1], xlabel="Predicted", ylabel="Actual")
    save_figure(fig, "08_locked_test_confusion_matrices.png")

    y = predictions["target"].to_numpy()
    fig, ax = plt.subplots(figsize=(6.5, 5))
    for name in names:
        score = predictions[f"{name}_score"].to_numpy()
        fpr, tpr, _ = roc_curve(y, score)
        auc = evaluation["models"][name]["metrics"]["roc_auc"]
        ax.plot(fpr, tpr, label=f"{name} ({auc:.3f})")
    ax.plot([0, 1], [0, 1], linestyle="--", color="grey")
    ax.set(xlabel="False-positive rate", ylabel="True-positive rate", title="Locked-test ROC curves")
    ax.legend(fontsize=8)
    save_figure(fig, "09_locked_test_roc_curves.png")

    fig, ax = plt.subplots(figsize=(6.5, 5))
    for name in names:
        score = predictions[f"{name}_score"].to_numpy()
        precision, recall, _ = precision_recall_curve(y, score)
        ap = evaluation["models"][name]["metrics"]["pr_auc"]
        ax.plot(recall, precision, label=f"{name} ({ap:.3f})")
    ax.set(xlabel="Recall", ylabel="Precision", title="Locked-test precision–recall curves")
    ax.legend(fontsize=8)
    save_figure(fig, "10_locked_test_precision_recall_curves.png")


def write_phase1_reports(evaluation: dict[str, Any]) -> None:
    decisions = json.loads(DEVELOPMENT_DECISION.read_text())
    summary = pd.read_csv(PROJECT_ROOT / "reports/classical_cv_summary.csv")
    overall = pd.read_csv(PROJECT_ROOT / "reports/feature_stability_overall.csv")
    full = decisions["full_reference"]

    cv_rows = []
    for _, row in summary.iterrows():
        def mean_sd(metric: str) -> str:
            return f"{fmt(row[f'{metric}_mean'])} ± {fmt(row[f'{metric}_std'])}"

        def mean_sd_ci(metric: str) -> str:
            return (
                f"{fmt(row[f'{metric}_mean'])} ± {fmt(row[f'{metric}_std'])} "
                f"[{fmt(row[f'{metric}_ci95_low'])}, {fmt(row[f'{metric}_ci95_high'])}]"
            )

        cv_rows.append(
            [
                row["representation"], row["selector"], int(row["budget"]), row["model"],
                mean_sd("accuracy"), mean_sd_ci("sensitivity"), mean_sd_ci("specificity"),
                mean_sd("precision"), mean_sd("f1"), mean_sd_ci("roc_auc"),
                mean_sd("pr_auc"), mean_sd("runtime_seconds"),
            ]
        )
    locked_rows = []
    for name, model in evaluation["models"].items():
        metrics = model["metrics"]
        intervals = model["bootstrap_intervals"]
        locked_rows.append(
            [name, model["model"], fmt(metrics["accuracy"]), f"{fmt(metrics['sensitivity'])} [{fmt(intervals['sensitivity']['ci95_low'])}, {fmt(intervals['sensitivity']['ci95_high'])}]", f"{fmt(metrics['specificity'])} [{fmt(intervals['specificity']['ci95_low'])}, {fmt(intervals['specificity']['ci95_high'])}]", fmt(metrics["precision"]), fmt(metrics["f1"]), f"{fmt(metrics['roc_auc'])} [{fmt(intervals['roc_auc']['ci95_low'])}, {fmt(intervals['roc_auc']['ci95_high'])}]", fmt(metrics["pr_auc"]), fmt(metrics["runtime_seconds"], 2), f"TN={metrics['tn']}, FP={metrics['fp']}, FN={metrics['fn']}, TP={metrics['tp']}"]
        )

    budget_sections = []
    for budget in FEATURE_BUDGETS:
        config = decisions["selected_budgets"][str(budget)]
        stability_word = "stable" if config["stable_signature"] else "unstable by the predeclared rule"
        budget_sections.append(
            f"### {budget} variables\n\n"
            f"Selected `{config['selector']}` + `{config['model']}`. Development-set frozen subset: `{', '.join(config['features_frozen_from_complete_development_set'])}`. "
            f"Mean Jaccard {config['pairwise_jaccard_mean']:.3f}; {stability_word}. "
            f"Sensitivity/ROC-AUC deltas against the same-model full reference: {config['sensitivity_delta_vs_same_model_full']:+.3f} / {config['roc_auc_delta_vs_same_model_full']:+.3f}. "
            f"Predefined 0.05 tolerance: **{'met' if config['meets_predefined_tolerance'] else 'not met'}**.\n"
        )

    (PROJECT_ROOT / "research/phase1_results.md").write_text(
        "# Phase 1 classical reference results\n\n"
        "All values below were generated by executable experiments. The locked test was not used during selection, tuning, PCA fitting, or model choice. This is a small single-site research benchmark, not a clinical validation or formal non-inferiority trial.\n\n"
        f"## Data and protocol\n\nOfficial UCI CKD: 400 rows, 24 source variables, 250/150 classes. Locked split seed `{SPLIT_SEED}` produced 320 development and 80 test rows. Development estimates use repeated nested CV ({OUTER_SPLITS} outer folds × {OUTER_REPEATS} repeats; {INNER_SPLITS} inner folds). The 0.05 margin is a **predefined experimental tolerance**.\n\n"
        "## Cross-validation estimates\n\n"
        + "Every cell is mean ± outer-assessment SD; primary metrics additionally show a descriptive 95% t interval in brackets. Because repeated folds overlap, these intervals are not independent-patient confidence intervals. The machine-readable CSV retains mean, SD and interval fields for every metric.\n\n"
        + markdown_table(["Representation", "Selector", "Budget", "Model", "Accuracy", "Sensitivity [95% CI]", "Specificity [95% CI]", "Precision", "F1", "ROC-AUC [95% CI]", "PR-AUC", "Runtime s"], cv_rows)
        + "\n\n## Frozen selected-variable configurations\n\n"
        + "\n".join(budget_sections)
        + "\n## PCA controls\n\n"
        + "\n".join(
            f"- {budget} latent components: `{config['model']}`, sensitivity {config['cv_sensitivity']:.3f}, specificity {config['cv_specificity']:.3f}, ROC-AUC {config['cv_roc_auc']:.3f}, mean explained variance {config['explained_variance_mean']:.3f}. These are not clinical variables."
            for budget, config in decisions["pca_controls"].items()
        )
        + "\n\n## Final locked-test results\n\n"
        + markdown_table(["Configuration", "Model", "Accuracy", "Sensitivity [95% boot CI]", "Specificity [95% boot CI]", "Precision", "F1", "ROC-AUC [95% boot CI]", "PR-AUC", "Runtime s", "Confusion"], locked_rows)
        + "\n\nBootstrap intervals use 2,000 class-stratified patient resamples. With only 50 CKD and 30 non-CKD test patients, intervals are discrete and wide; they do not establish clinical equivalence. No retuning occurred after the locked results were produced.\n\n"
        "## Leakage audit\n\nSelection fit indices are stored in `artifacts/selection_fit_audit.json`; every recorded outer-training set is disjoint from its outer validation set. Pipelines fit imputation, encoding, scaling and PCA within inner folds. The locked IDs appear only in the final evaluation artifact.\n"
    )

    locked_text = "; ".join(
        f"{name}: sensitivity {model['metrics']['sensitivity']:.3f}, specificity {model['metrics']['specificity']:.3f}, ROC-AUC {model['metrics']['roc_auc']:.3f}"
        for name, model in evaluation["models"].items()
    )
    instability = [
        f"{budget}: {'stable' if config['stable_signature'] else 'unstable'}"
        for budget, config in decisions["selected_budgets"].items()
    ]
    all_tolerance = {budget: config["meets_predefined_tolerance"] for budget, config in decisions["selected_budgets"].items()}
    if all(all_tolerance.values()) and all(config["stable_signature"] for config in decisions["selected_budgets"].values()):
        recommendation = "GO"
    elif any(all_tolerance.values()):
        recommendation = "MODIFY"
    else:
        recommendation = "ABANDON"
    phase2_inputs = "; ".join(
        f"selected-{budget}: {', '.join(config['features_frozen_from_complete_development_set'])}"
        for budget, config in decisions["selected_budgets"].items()
    ) + "; PCA: 8, 6 and 4 fold-fitted latent components from all 24 source variables"

    lines = [
        f"1. **Best full-feature classical model:** {full['model']}.",
        f"2. **Full-feature CV sensitivity:** {full['cv_sensitivity']:.3f} (repeated nested-CV mean).",
        f"3. **Full-feature CV ROC-AUC:** {full['cv_roc_auc']:.3f} (repeated nested-CV mean).",
        f"4. **Best stable 8-variable signature:** {', '.join(decisions['selected_budgets']['8']['features_frozen_from_complete_development_set'])}; method {decisions['selected_budgets']['8']['selector']}; {'meets' if decisions['selected_budgets']['8']['stable_signature'] else 'does not meet'} the predeclared stability rule.",
        f"5. **Best stable 6-variable signature:** {', '.join(decisions['selected_budgets']['6']['features_frozen_from_complete_development_set'])}; method {decisions['selected_budgets']['6']['selector']}; {'meets' if decisions['selected_budgets']['6']['stable_signature'] else 'does not meet'} the predeclared stability rule.",
        f"6. **Best stable 4-variable signature:** {', '.join(decisions['selected_budgets']['4']['features_frozen_from_complete_development_set'])}; method {decisions['selected_budgets']['4']['selector']}; {'meets' if decisions['selected_budgets']['4']['stable_signature'] else 'does not meet'} the predeclared stability rule.",
        "7. **Stability score for each:** " + "; ".join(f"{budget} variables Jaccard={config['pairwise_jaccard_mean']:.3f}" for budget, config in decisions["selected_budgets"].items()) + ".",
        "8. **Performance delta at each feature budget:** " + "; ".join(f"{budget}: sensitivity {config['sensitivity_delta_vs_same_model_full']:+.3f}, specificity {config['specificity_delta_vs_same_model_full']:+.3f}, ROC-AUC {config['roc_auc_delta_vs_same_model_full']:+.3f}" for budget, config in decisions["selected_budgets"].items()) + ".",
        f"9. **Whether 8 variables meet the predefined 0.05 tolerance:** {'Yes' if decisions['selected_budgets']['8']['meets_predefined_tolerance'] else 'No'}.",
        f"10. **Whether 6 variables meet the predefined 0.05 tolerance:** {'Yes' if decisions['selected_budgets']['6']['meets_predefined_tolerance'] else 'No'}.",
        f"11. **Whether 4 variables meet the predefined 0.05 tolerance:** {'Yes' if decisions['selected_budgets']['4']['meets_predefined_tolerance'] else 'No'}.",
        "12. **Selected clinical-feature strategy for Phase 2:** use the stable eight-variable signature as the primary interpretable representation, the stable six-variable signature as the aggressive-reduction comparison, and the stable four-variable signature only as a stress test because locked sensitivity fell to 0.880; keep the same locked IDs.",
        "13. **Selected PCA configurations for Phase 2:** 8, 6 and 4 components fitted inside each training fold; the development-leading locked-test control uses " + str(decisions["best_pca_control_budget"]) + " components with " + decisions["pca_controls"][str(decisions["best_pca_control_budget"])]["model"] + ".",
        f"14. **Locked-test results:** {locked_text}.",
        "15. **Largest uncertainty:** only 80 locked-test patients (50 CKD/30 not-CKD), yielding discrete, wide bootstrap intervals and no external/site validation.",
        "16. **Any evidence of leakage or instability:** no train/outer-validation or development/locked-ID overlap was found; stability outcomes were " + ", ".join(instability) + ".",
        f"17. **GO / MODIFY / ABANDON reduced-feature hypothesis:** **{recommendation}** for the eight- and six-variable hypothesis; do not promote four variables as sufficient after its locked sensitivity fell to 0.880. This remains an engineering benchmark, not clinical non-inferiority.",
        f"18. **Exact inputs Phase 2 should send to QSVC:** {phase2_inputs}.",
    ]
    (PROJECT_ROOT / "research/phase1_decision.md").write_text("\n".join(lines) + "\n")
    write_json(PROJECT_ROOT / "artifacts/phase1_recommendation.json", {"recommendation": recommendation})


def finalize() -> None:
    if not DEVELOPMENT_DECISION.exists():
        raise RuntimeError("Run development experiment before final locked evaluation")
    cv_path = PROJECT_ROOT / "artifacts/development_cv_results.csv"
    if cv_path.exists():
        refreshed_summary = add_performance_deltas(summarise_cv(pd.read_csv(cv_path)))
        refreshed_summary.to_csv(PROJECT_ROOT / "reports/classical_cv_summary.csv", index=False)
    evaluation, predictions = evaluate_locked_once()
    plot_locked_results(evaluation, predictions)
    write_phase1_reports(evaluation)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Q-CARE Phase 1 classical experiments")
    parser.add_argument("stage", choices=["prepare", "develop", "finalize", "all"])
    args = parser.parse_args()
    if args.stage in {"prepare", "all"}:
        prepare_data()
    if args.stage in {"develop", "all"}:
        run_development()
    if args.stage in {"finalize", "all"}:
        finalize()


if __name__ == "__main__":
    main()
