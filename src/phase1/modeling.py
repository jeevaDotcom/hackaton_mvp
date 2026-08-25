from __future__ import annotations

import itertools
import json
import math
import time
from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.base import BaseEstimator
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE, mutual_info_classif
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, RepeatedStratifiedKFold, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier

from .data import CATEGORICAL_FEATURES, FEATURES, NUMERIC_FEATURES


EXPERIMENT_SEED = 20260824
OUTER_SPLITS = 5
OUTER_REPEATS = 2
INNER_SPLITS = 3
FEATURE_BUDGETS = (8, 6, 4)
SELECTION_METHODS = ("mutual_information", "wrapper_rfe", "permutation_importance")
TOLERANCE = 0.05


def make_preprocessor(columns: Iterable[str], scale: bool = True) -> ColumnTransformer:
    columns = list(columns)
    numeric = [column for column in columns if column in NUMERIC_FEATURES]
    categorical = [column for column in columns if column in CATEGORICAL_FEATURES]
    numeric_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        numeric_steps.append(("scaler", StandardScaler()))
    numeric_pipe = Pipeline(numeric_steps)
    categorical_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                OneHotEncoder(drop="if_binary", handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )
    return ColumnTransformer(
        [("numeric", numeric_pipe, numeric), ("categorical", categorical_pipe, categorical)],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def _transformed_source_names(preprocessor: ColumnTransformer) -> list[str]:
    output = list(preprocessor.get_feature_names_out())
    sources: list[str] = []
    for value in output:
        if value in FEATURES:
            sources.append(value)
            continue
        matches = [feature for feature in CATEGORICAL_FEATURES if value.startswith(feature + "_")]
        if len(matches) != 1:
            raise ValueError(f"Could not map transformed feature {value!r} to one source variable")
        sources.append(matches[0])
    return sources


@dataclass(frozen=True)
class FeatureRanking:
    method: str
    table: pd.DataFrame
    fit_row_ids: tuple[str, ...]

    def top(self, budget: int) -> list[str]:
        return self.table.sort_values(["rank", "feature"])["feature"].head(budget).tolist()


def rank_source_features(
    X: pd.DataFrame,
    y: pd.Series,
    method: str,
    *,
    seed: int,
) -> FeatureRanking:
    if method not in SELECTION_METHODS:
        raise ValueError(f"Unknown selection method: {method}")
    if not set(FEATURES).issubset(X.columns):
        raise ValueError("Feature ranker requires all 24 source features")

    fit_ids = tuple(str(value) for value in X.index)
    if method == "permutation_importance":
        rank_train, rank_valid, y_train, y_valid = train_test_split(
            X[FEATURES], y, test_size=0.25, stratify=y, random_state=seed
        )
        preprocessor = make_preprocessor(FEATURES, scale=False)
        X_train_t = preprocessor.fit_transform(rank_train, y_train)
        X_valid_t = preprocessor.transform(rank_valid)
        estimator = RandomForestClassifier(
            n_estimators=300,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            random_state=seed,
            n_jobs=1,
        )
        estimator.fit(X_train_t, y_train)
        result = permutation_importance(
            estimator,
            X_valid_t,
            y_valid,
            scoring="roc_auc",
            n_repeats=8,
            random_state=seed,
            n_jobs=1,
        )
        raw_score = result.importances_mean
    else:
        preprocessor = make_preprocessor(FEATURES, scale=True)
        X_t = preprocessor.fit_transform(X[FEATURES], y)
        if method == "mutual_information":
            raw_score = mutual_info_classif(X_t, y.to_numpy(), random_state=seed)
        else:
            estimator = LogisticRegression(
                C=1.0,
                class_weight="balanced",
                max_iter=3000,
                random_state=seed,
            )
            rfe = RFE(estimator=estimator, n_features_to_select=1, step=1)
            rfe.fit(X_t, y)
            raw_score = -rfe.ranking_.astype(float)

    source_names = _transformed_source_names(preprocessor)
    grouped: dict[str, list[float]] = {feature: [] for feature in FEATURES}
    for source, score in zip(source_names, raw_score, strict=True):
        grouped[source].append(float(score))
    source_scores = {
        feature: float(np.mean(values)) if values else -math.inf for feature, values in grouped.items()
    }
    ordered = sorted(FEATURES, key=lambda feature: (-source_scores[feature], feature))
    ranks = {feature: index + 1 for index, feature in enumerate(ordered)}
    table = pd.DataFrame(
        {
            "feature": FEATURES,
            "score": [source_scores[feature] for feature in FEATURES],
            "rank": [ranks[feature] for feature in FEATURES],
        }
    ).sort_values(["rank", "feature"], ignore_index=True)
    return FeatureRanking(method=method, table=table, fit_row_ids=fit_ids)


def model_and_grid(model_name: str, seed: int) -> tuple[BaseEstimator, dict[str, list[Any]]]:
    if model_name == "logistic_regression":
        model = LogisticRegression(max_iter=3000, random_state=seed)
        grid = {
            "model__C": [0.1, 1.0, 10.0],
            "model__class_weight": [None, "balanced"],
        }
    elif model_name == "svm_rbf":
        model = SVC(kernel="rbf", random_state=seed)
        grid = {
            "model__C": [0.5, 2.0, 8.0],
            "model__gamma": ["scale", 0.1],
            "model__class_weight": [None, "balanced"],
        }
    elif model_name == "random_forest":
        model = RandomForestClassifier(random_state=seed, n_jobs=1)
        grid = {
            "model__n_estimators": [300],
            "model__max_depth": [None, 8],
            "model__min_samples_leaf": [1, 3],
            "model__class_weight": ["balanced_subsample"],
        }
    elif model_name == "xgboost":
        model = XGBClassifier(
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=seed,
            n_jobs=1,
            subsample=0.9,
            colsample_bytree=0.9,
            tree_method="hist",
        )
        grid = {
            "model__n_estimators": [150, 300],
            "model__max_depth": [2, 3],
            "model__learning_rate": [0.05],
        }
    else:
        raise ValueError(f"Unknown model: {model_name}")
    return model, grid


def make_pipeline(model_name: str, columns: list[str], seed: int, pca_components: int | None = None) -> tuple[Pipeline, dict[str, list[Any]]]:
    model, grid = model_and_grid(model_name, seed)
    steps: list[tuple[str, Any]] = [("preprocess", make_preprocessor(columns, scale=True))]
    if pca_components is not None:
        steps.append(("pca", PCA(n_components=pca_components, random_state=seed)))
    steps.append(("model", model))
    return Pipeline(steps), grid


def continuous_score(estimator: BaseEstimator, X: pd.DataFrame) -> np.ndarray:
    if hasattr(estimator, "predict_proba"):
        return np.asarray(estimator.predict_proba(X))[:, 1]
    if hasattr(estimator, "decision_function"):
        return np.asarray(estimator.decision_function(X))
    return np.asarray(estimator.predict(X), dtype=float)


def binary_metrics(y_true: Iterable[int], y_pred: Iterable[int], y_score: Iterable[float]) -> dict[str, float]:
    y_true = np.asarray(list(y_true), dtype=int)
    y_pred = np.asarray(list(y_pred), dtype=int)
    y_score = np.asarray(list(y_score), dtype=float)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    specificity = tn / (tn + fp) if (tn + fp) else np.nan
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "sensitivity": float(recall_score(y_true, y_pred, zero_division=0)),
        "specificity": float(specificity),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_score)),
        "pr_auc": float(average_precision_score(y_true, y_score)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def fit_tuned_pipeline(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_valid: pd.DataFrame,
    *,
    model_name: str,
    columns: list[str],
    seed: int,
    pca_components: int | None = None,
) -> tuple[Pipeline, dict[str, Any], dict[str, float], np.ndarray, np.ndarray]:
    pipeline, grid = make_pipeline(model_name, columns, seed, pca_components=pca_components)
    inner = StratifiedKFold(n_splits=INNER_SPLITS, shuffle=True, random_state=seed)
    search = GridSearchCV(
        pipeline,
        grid,
        scoring="roc_auc",
        cv=inner,
        n_jobs=1,
        refit=True,
        error_score="raise",
    )
    started = time.perf_counter()
    search.fit(X_train[columns], y_train)
    predicted = search.predict(X_valid[columns])
    scores = continuous_score(search.best_estimator_, X_valid[columns])
    elapsed = time.perf_counter() - started
    return search.best_estimator_, search.best_params_, {"runtime_seconds": elapsed}, predicted, scores


def evaluate_cv(
    X: pd.DataFrame,
    y: pd.Series,
) -> tuple[pd.DataFrame, list[dict[str, Any]], list[dict[str, Any]]]:
    """Run repeated nested CV on development data only.

    Feature rankings are fit once per outer-training partition and reused for
    matched downstream models. Model preprocessing and hyperparameter tuning
    remain inside the inner CV. The untouched outer fold provides the estimate.
    """

    outer = RepeatedStratifiedKFold(
        n_splits=OUTER_SPLITS,
        n_repeats=OUTER_REPEATS,
        random_state=EXPERIMENT_SEED,
    )
    records: list[dict[str, Any]] = []
    selection_records: list[dict[str, Any]] = []
    fit_audit: list[dict[str, Any]] = []

    for outer_index, (train_pos, valid_pos) in enumerate(outer.split(X, y)):
        repeat = outer_index // OUTER_SPLITS + 1
        fold = outer_index % OUTER_SPLITS + 1
        seed = EXPERIMENT_SEED + outer_index
        X_train, X_valid = X.iloc[train_pos], X.iloc[valid_pos]
        y_train, y_valid = y.iloc[train_pos], y.iloc[valid_pos]

        rankings: dict[str, FeatureRanking] = {}
        for method in SELECTION_METHODS:
            ranking = rank_source_features(X_train, y_train, method, seed=seed)
            rankings[method] = ranking
            fit_audit.append(
                {
                    "repeat": repeat,
                    "fold": fold,
                    "method": method,
                    "fit_row_ids": list(ranking.fit_row_ids),
                    "validation_row_ids": [str(value) for value in X_valid.index],
                }
            )
            rank_map = ranking.table.set_index("feature")["rank"].to_dict()
            for budget in FEATURE_BUDGETS:
                selected = ranking.top(budget)
                selection_records.append(
                    {
                        "repeat": repeat,
                        "fold": fold,
                        "method": method,
                        "budget": budget,
                        "selected_features": selected,
                        "ranks": {feature: int(rank_map[feature]) for feature in FEATURES},
                    }
                )

        full_models = ("logistic_regression", "svm_rbf", "random_forest", "xgboost")
        for model_name in full_models:
            estimator, params, timing, pred, score = fit_tuned_pipeline(
                X_train,
                y_train,
                X_valid,
                model_name=model_name,
                columns=FEATURES,
                seed=seed,
            )
            metrics = binary_metrics(y_valid, pred, score)
            records.append(
                {
                    "repeat": repeat,
                    "fold": fold,
                    "representation": "full",
                    "selector": "none",
                    "budget": 24,
                    "model": model_name,
                    "selected_features": json.dumps(FEATURES),
                    "best_params": json.dumps(params, sort_keys=True),
                    **metrics,
                    **timing,
                }
            )

        for method, budget, model_name in itertools.product(
            SELECTION_METHODS,
            FEATURE_BUDGETS,
            ("logistic_regression", "svm_rbf", "xgboost"),
        ):
            selected = rankings[method].top(budget)
            estimator, params, timing, pred, score = fit_tuned_pipeline(
                X_train,
                y_train,
                X_valid,
                model_name=model_name,
                columns=selected,
                seed=seed,
            )
            metrics = binary_metrics(y_valid, pred, score)
            records.append(
                {
                    "repeat": repeat,
                    "fold": fold,
                    "representation": "selected",
                    "selector": method,
                    "budget": budget,
                    "model": model_name,
                    "selected_features": json.dumps(selected),
                    "best_params": json.dumps(params, sort_keys=True),
                    **metrics,
                    **timing,
                }
            )

        for components, model_name in itertools.product(FEATURE_BUDGETS, ("logistic_regression", "svm_rbf")):
            estimator, params, timing, pred, score = fit_tuned_pipeline(
                X_train,
                y_train,
                X_valid,
                model_name=model_name,
                columns=FEATURES,
                seed=seed,
                pca_components=components,
            )
            metrics = binary_metrics(y_valid, pred, score)
            explained = float(estimator.named_steps["pca"].explained_variance_ratio_.sum())
            records.append(
                {
                    "repeat": repeat,
                    "fold": fold,
                    "representation": "pca",
                    "selector": "pca",
                    "budget": components,
                    "model": model_name,
                    "selected_features": "latent_components_not_clinical_variables",
                    "pca_explained_variance": explained,
                    "best_params": json.dumps(params, sort_keys=True),
                    **metrics,
                    **timing,
                }
            )

    return pd.DataFrame(records), selection_records, fit_audit


METRIC_COLUMNS = ["accuracy", "sensitivity", "specificity", "precision", "f1", "roc_auc", "pr_auc", "runtime_seconds"]


def summarise_cv(cv_results: pd.DataFrame) -> pd.DataFrame:
    groups = ["representation", "selector", "budget", "model"]
    rows: list[dict[str, Any]] = []
    for keys, group in cv_results.groupby(groups, dropna=False):
        record = dict(zip(groups, keys, strict=True))
        record["outer_assessments"] = int(len(group))
        for metric in METRIC_COLUMNS:
            values = group[metric].astype(float).to_numpy()
            mean = float(np.mean(values))
            std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
            half = float(stats.t.ppf(0.975, len(values) - 1) * std / np.sqrt(len(values))) if len(values) > 1 else 0.0
            record[f"{metric}_mean"] = mean
            record[f"{metric}_std"] = std
            low, high = mean - half, mean + half
            if metric == "runtime_seconds":
                low = max(0.0, low)
            else:
                low, high = max(0.0, low), min(1.0, high)
            record[f"{metric}_ci95_low"] = low
            record[f"{metric}_ci95_high"] = high
        if "pca_explained_variance" in group and group["pca_explained_variance"].notna().any():
            record["pca_explained_variance_mean"] = float(group["pca_explained_variance"].mean())
        rows.append(record)
    return pd.DataFrame(rows).sort_values(groups, ignore_index=True)


def pairwise_jaccard(sets: list[set[str]]) -> tuple[float, float]:
    values = []
    for left, right in itertools.combinations(sets, 2):
        values.append(len(left & right) / len(left | right))
    return (float(np.mean(values)), float(np.std(values, ddof=1))) if values else (1.0, 0.0)


def compute_stability(selection_records: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    details: list[dict[str, Any]] = []
    overall: list[dict[str, Any]] = []
    records = pd.DataFrame(selection_records)
    for method in SELECTION_METHODS:
        method_rows = records[records["method"] == method]
        rank_samples = {feature: [] for feature in FEATURES}
        for ranks in method_rows.drop_duplicates(["repeat", "fold"])["ranks"]:
            for feature in FEATURES:
                rank_samples[feature].append(int(ranks[feature]))
        row_by_feature = {feature: {"method": method, "feature": feature} for feature in FEATURES}
        for feature in FEATURES:
            row_by_feature[feature]["mean_rank"] = float(np.mean(rank_samples[feature]))
            row_by_feature[feature]["rank_std"] = float(np.std(rank_samples[feature], ddof=1))
        for budget in FEATURE_BUDGETS:
            subset_rows = method_rows[method_rows["budget"] == budget]
            sets = [set(value) for value in subset_rows["selected_features"]]
            jaccard_mean, jaccard_std = pairwise_jaccard(sets)
            frequencies = {
                feature: float(np.mean([feature in selected for selected in sets])) for feature in FEATURES
            }
            core_count = sum(value >= 0.80 for value in frequencies.values())
            stable = bool(jaccard_mean >= 0.60 and core_count >= math.ceil(0.75 * budget))
            overall.append(
                {
                    "method": method,
                    "budget": budget,
                    "pairwise_jaccard_mean": jaccard_mean,
                    "pairwise_jaccard_std": jaccard_std,
                    "features_with_frequency_ge_0_80": core_count,
                    "stable_signature": stable,
                }
            )
            for feature in FEATURES:
                row_by_feature[feature][f"selection_frequency_{budget}"] = frequencies[feature]
                row_by_feature[feature][f"jaccard_mean_{budget}"] = jaccard_mean
        details.extend(row_by_feature.values())
    return pd.DataFrame(details), pd.DataFrame(overall)


def add_performance_deltas(summary: pd.DataFrame) -> pd.DataFrame:
    result = summary.copy()
    for metric in ("sensitivity", "specificity", "roc_auc"):
        result[f"{metric}_delta_vs_same_model_full"] = np.nan
    full = result[result["representation"] == "full"].set_index("model")
    for index, row in result.iterrows():
        if row["model"] not in full.index:
            continue
        for metric in ("sensitivity", "specificity", "roc_auc"):
            result.loc[index, f"{metric}_delta_vs_same_model_full"] = (
                row[f"{metric}_mean"] - full.loc[row["model"], f"{metric}_mean"]
            )
    result["meets_sensitivity_tolerance"] = result["sensitivity_delta_vs_same_model_full"] >= -TOLERANCE
    result["meets_roc_auc_tolerance"] = result["roc_auc_delta_vs_same_model_full"] >= -TOLERANCE
    result["meets_joint_tolerance"] = result["meets_sensitivity_tolerance"] & result["meets_roc_auc_tolerance"]
    return result


def bootstrap_metric_intervals(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_score: np.ndarray,
    *,
    seed: int,
    n_bootstrap: int = 2000,
) -> dict[str, dict[str, float]]:
    rng = np.random.default_rng(seed)
    negative = np.flatnonzero(y_true == 0)
    positive = np.flatnonzero(y_true == 1)
    values = {"sensitivity": [], "specificity": [], "roc_auc": []}
    for _ in range(n_bootstrap):
        indices = np.concatenate(
            [rng.choice(negative, size=len(negative), replace=True), rng.choice(positive, size=len(positive), replace=True)]
        )
        rng.shuffle(indices)
        metrics = binary_metrics(y_true[indices], y_pred[indices], y_score[indices])
        for metric in values:
            values[metric].append(metrics[metric])
    output: dict[str, dict[str, float]] = {}
    for metric, samples in values.items():
        output[metric] = {
            "estimate": binary_metrics(y_true, y_pred, y_score)[metric],
            "ci95_low": float(np.quantile(samples, 0.025)),
            "ci95_high": float(np.quantile(samples, 0.975)),
            "bootstrap_resamples": n_bootstrap,
        }
    return output
