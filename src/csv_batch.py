"""Deterministic CSV batch mapping, validation, inference, and export helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from io import StringIO
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from src.live_vqc import CATEGORICAL_VALUES, READABLE_NAMES, LiveVQCService


MAX_BATCH_ROWS = 1_000
FEATURE_ORDER = ["hemo", "al", "dm", "sg", "pcv", "appet", "htn", "sc"]
NUMERIC_FEATURES = {"hemo", "al", "sg", "pcv", "sc"}
CATEGORICAL_FEATURES = set(CATEGORICAL_VALUES)


def batch_size_error(row_count: int) -> str | None:
    if int(row_count) > MAX_BATCH_ROWS:
        return f"This research MVP supports up to {MAX_BATCH_ROWS:,} rows per batch. Split larger files into smaller batches."
    return None


def _normalize_column_name(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())


ALIASES: dict[str, tuple[str, ...]] = {
    "hemo": ("hemo", "haemoglobin", "hemoglobin", "hb", "hgb"),
    "al": ("al", "albumin", "urinaryalbumin", "albuminordinal", "albumingrade"),
    "dm": ("dm", "diabetes", "diabetesmellitus"),
    "sg": ("sg", "specificgravity", "urinespecificgravity", "spgravity"),
    "pcv": ("pcv", "packedcellvolume", "hematocrit", "haematocrit", "hct"),
    "appet": ("appet", "appetite"),
    "htn": ("htn", "hypertension"),
    "sc": ("sc", "serumcreatinine", "creatinine", "screatinine", "creat"),
}

AMBIGUOUS_ALBUMIN_ALIASES = {
    "serumalbumin",
    "serumalb",
    "salbumin",
}

_ALIAS_TO_FEATURE = {
    alias: feature for feature, aliases in ALIASES.items() for alias in aliases
}


@dataclass(frozen=True)
class MappingSuggestion:
    feature: str
    display_name: str
    suggested_column: str | None
    status: str
    candidates: tuple[str, ...] = ()


def suggest_column_mapping(columns: Sequence[object]) -> dict[str, MappingSuggestion]:
    """Suggest one deterministic source column for each frozen feature."""

    source_columns = [str(column) for column in columns]
    normalized = [(column, _normalize_column_name(column)) for column in source_columns]
    suggestions: dict[str, MappingSuggestion] = {}
    for feature in FEATURE_ORDER:
        aliases = set(ALIASES[feature])
        candidates = tuple(column for column, key in normalized if key in aliases)
        ambiguous = tuple(column for column, key in normalized if key in AMBIGUOUS_ALBUMIN_ALIASES)
        if feature == "al" and ambiguous:
            suggestions[feature] = MappingSuggestion(
                feature, READABLE_NAMES[feature], None, "AMBIGUOUS", ambiguous
            )
        elif not candidates:
            suggestions[feature] = MappingSuggestion(feature, READABLE_NAMES[feature], None, "MISSING")
        elif len(candidates) > 1:
            suggestions[feature] = MappingSuggestion(
                feature, READABLE_NAMES[feature], candidates[0], "REVIEW REQUIRED", candidates
            )
        else:
            suggestions[feature] = MappingSuggestion(
                feature, READABLE_NAMES[feature], candidates[0], "MAPPED", candidates
            )
    return suggestions


def validate_mapping(mapping: Mapping[str, str | None], columns: Sequence[object]) -> list[str]:
    """Return blocking mapping errors, including duplicate source assignments."""

    available = {str(column) for column in columns}
    errors: list[str] = []
    selected: dict[str, str] = {}
    for feature in FEATURE_ORDER:
        source = mapping.get(feature)
        if not source:
            errors.append(f"{READABLE_NAMES[feature]} is not mapped")
        elif str(source) not in available:
            errors.append(f"{READABLE_NAMES[feature]} maps to missing column {source!r}")
        else:
            selected[feature] = str(source)
    reverse: dict[str, list[str]] = {}
    for feature, source in selected.items():
        reverse.setdefault(source, []).append(feature)
    for source, features in reverse.items():
        if len(features) > 1:
            errors.append(f"Column {source!r} is assigned to multiple features: {', '.join(features)}")
    return errors


def _missing(value: object) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value)) or (isinstance(value, str) and not value.strip())
    except (TypeError, ValueError):
        return False


def _normalize_category(feature: str, value: object) -> str:
    normalized = str(value).strip().lower()
    if feature in {"dm", "htn"}:
        normalized = {"y": "yes", "n": "no", "true": "yes", "false": "no"}.get(normalized, normalized)
    if normalized not in CATEGORICAL_VALUES[feature]:
        raise ValueError(f'{READABLE_NAMES[feature]} value {value!r} is not supported')
    return normalized


def _normalize_numeric(feature: str, value: object, observed_ranges: Mapping[str, Any]) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid {READABLE_NAMES[feature]} value {value!r}") from error
    if not np.isfinite(numeric):
        raise ValueError(f"Invalid {READABLE_NAMES[feature]} value {value!r}")
    if feature == "al" and (numeric < 0 or numeric > 5 or not numeric.is_integer()):
        raise ValueError(f"{READABLE_NAMES[feature]} must be a dataset ordinal grade from 0 to 5")
    low, high = observed_ranges[feature]
    if numeric < float(low) or numeric > float(high):
        raise ValueError(f"{READABLE_NAMES[feature]} value {value!r} is outside the observed development range")
    return numeric


def normalize_row(
    row: pd.Series,
    mapping: Mapping[str, str | None],
    observed_ranges: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, list[str]]:
    """Normalize and independently validate one source row."""

    profile: dict[str, Any] = {}
    errors: list[str] = []
    for feature in FEATURE_ORDER:
        source = mapping.get(feature)
        if not source or source not in row.index:
            errors.append(f"Missing mapped column for {READABLE_NAMES[feature]}")
            continue
        value = row[source]
        if _missing(value):
            errors.append(f"Missing {READABLE_NAMES[feature]}")
            continue
        try:
            profile[feature] = (
                _normalize_numeric(feature, value, observed_ranges)
                if feature in NUMERIC_FEATURES
                else _normalize_category(feature, value)
            )
        except ValueError as error:
            errors.append(str(error))
    return (profile if not errors else None), errors


def _agreement(predictions: Sequence[int]) -> str:
    if len(predictions) != 3:
        return "DISAGREEMENT"
    positives = sum(int(value) for value in predictions)
    return "3 OF 3 AGREE" if positives in {0, 3} else "2 OF 3 AGREE"


def build_batch_results(
    frame: pd.DataFrame,
    mapping: Mapping[str, str | None],
    service: LiveVQCService,
) -> pd.DataFrame:
    """Validate all rows, run frozen models only for valid rows, and preserve order."""

    rows: list[dict[str, Any]] = []
    valid_profiles: list[dict[str, Any]] = []
    valid_positions: list[int] = []
    for position, (_, source_row) in enumerate(frame.iterrows()):
        profile, errors = normalize_row(source_row, mapping, service.observed_ranges)
        result: dict[str, Any] = {
            "row_number": position + 1,
            "validation_status": "VALID" if not errors else "INVALID",
            "validation_errors": "; ".join(errors),
        }
        for feature in FEATURE_ORDER:
            result[feature] = None if profile is None else profile.get(feature)
        for model in ("rbf_svm", "qsvc", "vqc"):
            result[f"{model}_prediction"] = None
            result[f"{model}_score"] = None
        result["model_agreement"] = None
        rows.append(result)
        if profile is not None:
            valid_positions.append(position)
            valid_profiles.append(profile)

    if valid_profiles:
        predictions = service.batch_model_outputs(valid_profiles)
        for position, output in zip(valid_positions, predictions, strict=True):
            result = rows[position]
            for model in ("rbf_svm", "qsvc", "vqc"):
                result[f"{model}_prediction"] = int(output[f"{model}_prediction"])
                result[f"{model}_score"] = float(output[f"{model}_score"])
            result["model_agreement"] = _agreement(
                [int(result[f"{model}_prediction"]) for model in ("rbf_svm", "qsvc", "vqc")]
            )
    return pd.DataFrame(rows, columns=result_columns())


def result_columns() -> list[str]:
    return [
        "row_number", "validation_status", "validation_errors", *FEATURE_ORDER,
        "rbf_svm_prediction", "qsvc_prediction", "vqc_prediction",
        "rbf_svm_score", "qsvc_score", "vqc_score", "model_agreement",
    ]


def summarize_results(results: pd.DataFrame) -> dict[str, int]:
    valid = results[results.validation_status == "VALID"]
    return {
        "total_rows": int(len(results)),
        "valid_rows": int((results.validation_status == "VALID").sum()),
        "invalid_rows": int((results.validation_status == "INVALID").sum()),
        "three_of_three": int((valid.model_agreement == "3 OF 3 AGREE").sum()),
        "two_of_three": int((valid.model_agreement == "2 OF 3 AGREE").sum()),
        "disagreement": int((valid.model_agreement == "DISAGREEMENT").sum()),
    }


def filter_results(
    results: pd.DataFrame,
    validation: str = "All",
    agreement: str = "All",
    rbf_svm: str = "All",
    qsvc: str = "All",
    vqc: str = "All",
) -> pd.DataFrame:
    filtered = results.copy()
    if validation != "All":
        filtered = filtered[filtered.validation_status == validation.upper()]
    if agreement != "All":
        filtered = filtered[filtered.model_agreement == agreement]
    for model, selection in (("rbf_svm", rbf_svm), ("qsvc", qsvc), ("vqc", vqc)):
        if selection != "All":
            prediction = 1 if selection == "CKD-like" else 0
            filtered = filtered[filtered[f"{model}_prediction"] == prediction]
    return filtered.reset_index(drop=True)


def export_results(results: pd.DataFrame) -> bytes:
    """Export only the documented public batch result columns."""

    return results[result_columns()].to_csv(index=False).encode("utf-8")


def csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8")


def load_csv_bytes(data: bytes) -> pd.DataFrame:
    return pd.read_csv(StringIO(data.decode("utf-8")))
