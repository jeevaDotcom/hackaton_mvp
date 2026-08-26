"""Deterministic, non-training data-health checks for uploaded biomedical CSV files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
import pandas as pd


REQUIRED_FEATURES = ["hemo", "al", "dm", "sg", "pcv", "appet", "htn", "sc"]
NUMERIC_FEATURES = {"hemo", "al", "sg", "pcv", "sc"}
CATEGORICAL_FEATURES = {"dm", "appet", "htn"}


def _key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())


ALIASES = {
    "hemo": "hemo", "haemoglobin": "hemo", "hemoglobin": "hemo",
    "al": "al", "albumin": "al",
    "dm": "dm", "diabetes": "dm", "diabetesmellitus": "dm",
    "sg": "sg", "specificgravity": "sg",
    "pcv": "pcv", "packedcellvolume": "pcv", "packedcellvolumepercent": "pcv",
    "appet": "appet", "appetite": "appet",
    "htn": "htn", "hypertension": "htn",
    "sc": "sc", "serumcreatinine": "sc", "serumcreatininemgdl": "sc",
}


@dataclass(frozen=True)
class DataHealthResult:
    status: str
    samples: int
    features: int
    target: str
    target_classes: int
    class_balance: str
    missing_values: int
    missing_fraction: float
    duplicates: int
    numeric_features: int
    categorical_features: int
    range_anomalies: int
    required_coverage: int
    required_total: int
    missing_required: tuple[str, ...]
    detected_required: tuple[str, ...]
    likely_shift: bool
    can_evaluate_frozen_ckd_models: bool
    notes: tuple[str, ...]


def detect_required_columns(frame: pd.DataFrame) -> dict[str, str]:
    """Map canonical frozen feature codes to uploaded column names."""

    detected: dict[str, str] = {}
    for column in frame.columns:
        canonical = ALIASES.get(_key(column))
        if canonical and canonical not in detected:
            detected[canonical] = str(column)
    return detected


def analyse_data_health(
    frame: pd.DataFrame,
    target: str,
    observed_ranges: Mapping[str, Any],
) -> DataHealthResult:
    """Assess schema and basic compatibility without fitting or running any model."""

    if frame.empty:
        raise ValueError("Uploaded CSV contains no records")
    if target not in frame.columns:
        raise ValueError("Selected target column is not present in the uploaded CSV")

    detected = detect_required_columns(frame)
    missing_required = tuple(feature for feature in REQUIRED_FEATURES if feature not in detected)
    missing_values = int(frame.isna().sum().sum())
    total_cells = max(int(frame.shape[0] * frame.shape[1]), 1)
    missing_fraction = missing_values / total_cells
    duplicates = int(frame.duplicated().sum())
    target_values = frame[target].dropna().astype(str)
    counts = target_values.value_counts()
    target_classes = int(len(counts))
    class_balance = "Unavailable"
    if target_classes:
        class_balance = " / ".join(f"{label}: {int(count)}" for label, count in counts.head(6).items())

    range_anomalies = 0
    conversion_anomalies = 0
    for feature, uploaded_column in detected.items():
        series = frame[uploaded_column]
        if feature in NUMERIC_FEATURES:
            numeric = pd.to_numeric(series, errors="coerce")
            conversion_anomalies += int((series.notna() & numeric.isna()).sum())
            low, high = observed_ranges[feature]
            range_anomalies += int(((numeric < float(low)) | (numeric > float(high))).sum())
        elif feature in CATEGORICAL_FEATURES:
            allowed = {str(value).strip().lower() for value in observed_ranges[feature]}
            normalized = series.dropna().astype(str).str.strip().str.lower()
            range_anomalies += int((~normalized.isin(allowed)).sum())
    range_anomalies += conversion_anomalies

    feature_columns = [column for column in frame.columns if column != target]
    numeric_count = int(frame[feature_columns].select_dtypes(include=[np.number]).shape[1])
    categorical_count = len(feature_columns) - numeric_count
    anomaly_fraction = range_anomalies / max(frame.shape[0] * len(REQUIRED_FEATURES), 1)
    duplicate_fraction = duplicates / max(frame.shape[0], 1)
    likely_shift = bool(anomaly_fraction > 0.01 or missing_fraction > 0.10)

    notes: list[str] = []
    if missing_required:
        notes.append("Missing frozen CKD features: " + ", ".join(missing_required))
    if target_classes < 2:
        notes.append("The selected target must contain at least two observed classes for evaluation.")
    if missing_fraction > 0.10:
        notes.append("More than 10% of uploaded cells are missing.")
    if range_anomalies:
        notes.append(f"{range_anomalies} values fall outside the UCI development ranges or expected category coding.")
    if duplicate_fraction > 0.05:
        notes.append("More than 5% of rows are duplicates.")
    if likely_shift:
        notes.append("Potential distribution shift requires review; range checks are descriptive, not clinical reference checks.")

    incompatible = bool(missing_required or target_classes < 2)
    review_required = bool(missing_fraction > 0.10 or range_anomalies or duplicate_fraction > 0.05 or likely_shift)
    status = "INCOMPATIBLE" if incompatible else "REVIEW REQUIRED" if review_required else "READY"
    if not notes:
        notes.append("Schema and descriptive checks passed; this does not establish clinical or cohort compatibility.")

    return DataHealthResult(
        status=status,
        samples=int(frame.shape[0]),
        features=len(feature_columns),
        target=str(target),
        target_classes=target_classes,
        class_balance=class_balance,
        missing_values=missing_values,
        missing_fraction=float(missing_fraction),
        duplicates=duplicates,
        numeric_features=numeric_count,
        categorical_features=categorical_count,
        range_anomalies=range_anomalies,
        required_coverage=len(detected),
        required_total=len(REQUIRED_FEATURES),
        missing_required=missing_required,
        detected_required=tuple(feature for feature in REQUIRED_FEATURES if feature in detected),
        likely_shift=likely_shift,
        can_evaluate_frozen_ckd_models=status == "READY",
        notes=tuple(notes),
    )
