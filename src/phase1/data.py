from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


SOURCE_URL = "https://archive.ics.uci.edu/static/public/336/chronic+kidney+disease.zip"
DATASET_DOI = "10.24432/C5G020"
RETRIEVAL_DATE = "2026-08-24"
SPLIT_SEED = 20260824

FEATURES = [
    "age", "bp", "sg", "al", "su", "rbc", "pc", "pcc", "ba", "bgr", "bu", "sc",
    "sod", "pot", "hemo", "pcv", "wc", "rc", "htn", "dm", "cad", "appet", "pe", "ane",
]
NUMERIC_FEATURES = [
    "age", "bp", "sg", "al", "su", "bgr", "bu", "sc", "sod", "pot", "hemo", "pcv", "wc", "rc",
]
CATEGORICAL_FEATURES = ["rbc", "pc", "pcc", "ba", "htn", "dm", "cad", "appet", "pe", "ane"]
TARGET = "target"

ALLOWED_CATEGORIES = {
    "rbc": {"normal", "abnormal"},
    "pc": {"normal", "abnormal"},
    "pcc": {"present", "notpresent"},
    "ba": {"present", "notpresent"},
    "htn": {"yes", "no"},
    "dm": {"yes", "no"},
    "cad": {"yes", "no"},
    "appet": {"good", "poor"},
    "pe": {"yes", "no"},
    "ane": {"yes", "no"},
}


@dataclass(frozen=True)
class ParsedDataset:
    frame: pd.DataFrame
    provenance: dict[str, Any]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _repair_column_count(raw_tokens: list[str], row_id: str, log: list[dict[str, Any]]) -> list[str]:
    if len(raw_tokens) == 25:
        return raw_tokens
    if len(raw_tokens) == 26 and raw_tokens[-1].strip() == "":
        log.append({
            "row_id": row_id,
            "rule": "remove_trailing_empty_field",
            "raw_column_count": 26,
            "detail": "A trailing comma created an empty 26th field; the empty terminal field was removed.",
        })
        return raw_tokens[:-1]
    empty_positions = [i for i, token in enumerate(raw_tokens) if token.strip() == ""]
    if len(raw_tokens) == 26 and len(empty_positions) == 1:
        pos = empty_positions[0]
        repaired = raw_tokens[:pos] + raw_tokens[pos + 1 :]
        log.append({
            "row_id": row_id,
            "rule": "remove_spurious_empty_delimiter",
            "raw_column_count": 26,
            "empty_field_position_zero_based": pos,
            "detail": "A single empty token shifted otherwise valid trailing categorical values; the empty token was removed.",
        })
        return repaired
    raise ValueError(f"{row_id}: expected 25 columns, found {len(raw_tokens)}")


def load_official_arff(path: str | Path) -> ParsedDataset:
    """Parse the official ARFF with a complete, inspectable cleanup log.

    The parser never guesses an unknown value: undocumented labels, invalid
    categorical values, numeric conversion failures, and unhandled column
    counts raise an error.
    """

    path = Path(path)
    rows: list[dict[str, Any]] = []
    repairs: list[dict[str, Any]] = []
    whitespace_variants: dict[str, set[str]] = {}
    data_started = False
    raw_data_lines = 0

    for line_number, line in enumerate(path.read_text(errors="strict").splitlines(), start=1):
        stripped_line = line.strip()
        if stripped_line.lower() == "@data":
            data_started = True
            continue
        if not data_started or not stripped_line or stripped_line.startswith("%"):
            continue

        raw_data_lines += 1
        row_id = f"ckd-{raw_data_lines:04d}"
        raw_tokens = line.split(",")
        tokens = _repair_column_count(raw_tokens, row_id, repairs)
        if len(tokens) != 25:
            raise AssertionError(f"{row_id}: repair did not produce 25 columns")

        cleaned: list[str | None] = []
        for col_name, token in zip(FEATURES + [TARGET], tokens, strict=True):
            normalized = token.strip().lower()
            if token != token.strip():
                whitespace_variants.setdefault(col_name, set()).add(repr(token))
            cleaned.append(None if normalized in {"?", ""} else normalized)

        record: dict[str, Any] = {"row_id": row_id}
        for col_name, value in zip(FEATURES + [TARGET], cleaned, strict=True):
            if col_name in NUMERIC_FEATURES:
                if value is None:
                    record[col_name] = np.nan
                else:
                    try:
                        record[col_name] = float(value)
                    except ValueError as exc:
                        raise ValueError(f"{row_id}: malformed numeric {col_name}={value!r}") from exc
            elif col_name in CATEGORICAL_FEATURES:
                if value is not None and value not in ALLOWED_CATEGORIES[col_name]:
                    raise ValueError(f"{row_id}: unexpected category {col_name}={value!r}")
                record[col_name] = value
            else:
                target_map = {"ckd": 1, "notckd": 0}
                if value not in target_map:
                    raise ValueError(f"{row_id}: unexpected target label {value!r}")
                record[TARGET] = target_map[value]
        rows.append(record)

    frame = pd.DataFrame(rows, columns=["row_id"] + FEATURES + [TARGET])
    duplicates = frame.duplicated(subset=FEATURES + [TARGET], keep=False)
    target_counts = frame[TARGET].value_counts().sort_index().to_dict()
    missingness = {feature: int(frame[feature].isna().sum()) for feature in FEATURES}

    provenance: dict[str, Any] = {
        "source_url": SOURCE_URL,
        "dataset_doi": DATASET_DOI,
        "retrieval_date": RETRIEVAL_DATE,
        "raw_file": str(path),
        "raw_sha256": sha256(path),
        "raw_data_row_count": raw_data_lines,
        "clean_row_count": int(len(frame)),
        "raw_expected_column_count": 25,
        "clean_column_count_including_row_id_and_target": int(frame.shape[1]),
        "predictor_count": len(FEATURES),
        "target_distribution": {"not_ckd": int(target_counts.get(0, 0)), "ckd": int(target_counts.get(1, 0))},
        "feature_types": {
            "numeric_or_ordered": NUMERIC_FEATURES,
            "categorical": CATEGORICAL_FEATURES,
            "target": "binary integer after explicit mapping",
        },
        "missingness": missingness,
        "total_missing_predictor_cells": int(frame[FEATURES].isna().sum().sum()),
        "rows_with_missing_predictors": int(frame[FEATURES].isna().any(axis=1).sum()),
        "duplicate_row_count_including_target": int(duplicates.sum()),
        "duplicate_row_ids": frame.loc[duplicates, "row_id"].tolist(),
        "column_repairs": repairs,
        "whitespace_variants": {key: sorted(value) for key, value in whitespace_variants.items()},
        "target_cleanup_rules": [
            "strip leading/trailing spaces and tabs",
            "convert to lowercase",
            "map 'ckd' to 1 and 'notckd' to 0",
            "reject every other target token",
        ],
        "missing_cleanup_rule": "After whitespace cleanup, '?' is mapped to missing; undocumented non-empty values are rejected.",
        "source_variable_renames": {"wbcc": "wc", "rbcc": "rc"},
        "generated_on": date.today().isoformat(),
    }
    return ParsedDataset(frame=frame, provenance=provenance)


def build_quality_table(frame: pd.DataFrame, provenance: dict[str, Any] | None = None) -> pd.DataFrame:
    whitespace_variants = (provenance or {}).get("whitespace_variants", {})
    records: list[dict[str, Any]] = []
    for feature in FEATURES:
        series = frame[feature]
        record: dict[str, Any] = {
            "feature": feature,
            "type": "numeric_or_ordered" if feature in NUMERIC_FEATURES else "categorical",
            "missing_count": int(series.isna().sum()),
            "missing_pct": float(100 * series.isna().mean()),
            "unique_non_missing": int(series.nunique(dropna=True)),
            "min": np.nan,
            "max": np.nan,
            "median": np.nan,
            "categories": "",
            "suspected_malformed_values": (
                json.dumps({"raw_whitespace_or_tab_variants": whitespace_variants[feature]})
                if feature in whitespace_variants
                else "none observed after explicit parser validation"
            ),
            "descriptive_target_relationship": "",
        }
        if feature in NUMERIC_FEATURES:
            record.update(
                min=float(series.min()),
                max=float(series.max()),
                median=float(series.median()),
                descriptive_target_relationship=json.dumps(
                    {
                        "not_ckd_median": float(frame.loc[frame[TARGET] == 0, feature].median()),
                        "ckd_median": float(frame.loc[frame[TARGET] == 1, feature].median()),
                    },
                    sort_keys=True,
                ),
            )
        else:
            categories = sorted(str(value) for value in series.dropna().unique())
            rates = {}
            for category in categories:
                subset = frame.loc[series == category, TARGET]
                rates[category] = {"n": int(len(subset)), "ckd_rate": float(subset.mean())}
            record.update(
                categories=json.dumps(categories),
                descriptive_target_relationship=json.dumps(rates, sort_keys=True),
            )
        records.append(record)
    return pd.DataFrame(records)


def make_locked_split(frame: pd.DataFrame, seed: int = SPLIT_SEED) -> dict[str, Any]:
    train_ids, test_ids = train_test_split(
        frame["row_id"].to_numpy(),
        test_size=0.20,
        random_state=seed,
        stratify=frame[TARGET].to_numpy(),
    )
    train_ids = sorted(str(value) for value in train_ids)
    test_ids = sorted(str(value) for value in test_ids)
    train_target = frame.set_index("row_id").loc[train_ids, TARGET]
    test_target = frame.set_index("row_id").loc[test_ids, TARGET]
    return {
        "seed": seed,
        "strategy": "one stratified 80/20 holdout created before EDA-driven selection or tuning",
        "development_row_ids": train_ids,
        "locked_test_row_ids": test_ids,
        "development_n": len(train_ids),
        "locked_test_n": len(test_ids),
        "development_target_distribution": {
            "not_ckd": int((train_target == 0).sum()), "ckd": int((train_target == 1).sum())
        },
        "locked_test_target_distribution": {
            "not_ckd": int((test_target == 0).sum()), "ckd": int((test_target == 1).sum())
        },
        "locked_test_policy": [
            "no feature selection",
            "no hyperparameter tuning",
            "no PCA fitting",
            "no threshold optimisation",
            "no model selection",
            "evaluate once after development decisions are frozen",
        ],
    }


def write_json(path: str | Path, payload: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
