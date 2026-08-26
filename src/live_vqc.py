"""Frozen inference services for the additional live VQC research workflow.

Training lives only in ``scripts/train_live_vqc.py``.  This module loads the
persisted circuit weights and preprocessing contract, performs deterministic
local statevector inference, and derives descriptive research aids.  It never
fits or updates a model.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import joblib
import numpy as np
import pandas as pd


READABLE_NAMES = {
    "hemo": "Haemoglobin",
    "al": "Albumin",
    "dm": "Diabetes mellitus",
    "sg": "Specific gravity",
    "pcv": "Packed cell volume",
    "appet": "Appetite",
    "htn": "Hypertension",
    "sc": "Serum creatinine",
}

UNITS = {
    "hemo": "g/dL",
    "al": "ordinal grade (0–5)",
    "dm": "dataset category",
    "sg": "unitless",
    "pcv": "%",
    "appet": "dataset category",
    "htn": "dataset category",
    "sc": "mg/dL",
}

CATEGORICAL_VALUES = {
    "dm": ("no", "yes"),
    "appet": ("good", "poor"),
    "htn": ("no", "yes"),
}


def _single_qubit_gate(state: np.ndarray, gate: np.ndarray, qubit: int) -> None:
    """Apply a 2x2 gate in Qiskit's little-endian basis convention."""

    stride = 1 << qubit
    for start in range(0, len(state), stride * 2):
        for offset in range(stride):
            zero = start + offset
            one = zero + stride
            a, b = state[zero], state[one]
            state[zero] = gate[0, 0] * a + gate[0, 1] * b
            state[one] = gate[1, 0] * a + gate[1, 1] * b


def _cx(state: np.ndarray, control: int, target: int) -> None:
    for index in range(len(state)):
        if ((index >> control) & 1) and not ((index >> target) & 1):
            paired = index | (1 << target)
            state[index], state[paired] = state[paired], state[index]


def frozen_vqc_class_scores(weights: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Exact class-1 weights for the frozen ZFeatureMap + RealAmplitudes VQC.

    This small NumPy statevector executor mirrors the persisted eight-qubit
    circuit and avoids deserialising Qiskit's native Rust circuit objects in a
    Streamlit worker thread (which can segfault on macOS).  The trained weights
    and circuit architecture remain unchanged.
    """

    matrix = np.asarray(matrix, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if matrix.ndim != 2 or matrix.shape[1] * 2 != len(weights):
        raise ValueError("Frozen VQC matrix/weight shape mismatch")
    qubits = matrix.shape[1]
    dimension = 1 << qubits
    inv_sqrt_two = 1.0 / np.sqrt(2.0)
    hadamard = np.asarray([[inv_sqrt_two, inv_sqrt_two], [inv_sqrt_two, -inv_sqrt_two]], dtype=complex)
    scores: list[float] = []
    for row in matrix:
        state = np.zeros(dimension, dtype=complex)
        state[0] = 1.0
        for qubit, value in enumerate(row):
            _single_qubit_gate(state, hadamard, qubit)
            phase = np.asarray([[1.0, 0.0], [0.0, np.exp(2.0j * float(value))]], dtype=complex)
            _single_qubit_gate(state, phase, qubit)
        for qubit, theta in enumerate(weights[:qubits]):
            cosine, sine = np.cos(theta / 2.0), np.sin(theta / 2.0)
            _single_qubit_gate(state, np.asarray([[cosine, -sine], [sine, cosine]], dtype=complex), qubit)
        for control in range(qubits - 1):
            _cx(state, control, control + 1)
        for qubit, theta in enumerate(weights[qubits:]):
            cosine, sine = np.cos(theta / 2.0), np.sin(theta / 2.0)
            _single_qubit_gate(state, np.asarray([[cosine, -sine], [sine, cosine]], dtype=complex), qubit)
        probabilities = np.abs(state) ** 2
        # Binary VQC's frozen interpret function is ``measured_integer % 2``.
        scores.append(sum(float(value) for index, value in enumerate(probabilities) if index % 2 == 1))
    return np.asarray(scores, dtype=float)


@dataclass(frozen=True)
class ModelDecision:
    model: str
    predicted_class: int
    display: str


class LiveVQCService:
    """Load and execute the frozen VQC and its descriptive support workflow."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.artifact_dir = self.root / "artifacts/live_vqc"
        self.metadata = json.loads((self.artifact_dir / "metadata.json").read_text())
        self.metrics = json.loads((self.artifact_dir / "metrics.json").read_text())
        self.feature_order = list(self.metadata["feature_order"])
        self.preprocessor = joblib.load(self.artifact_dir / "preprocessor/preprocessor.joblib")
        self.weights = np.load(self.artifact_dir / "model/weights.npy")
        self.reference_records = pd.read_csv(self.artifact_dir / "reference_records.csv")
        self.presets = json.loads((self.artifact_dir / "presets.json").read_text())
        self.training_reference = dict(self.metadata["training_reference"])
        self.observed_ranges = dict(self.metadata["observed_development_ranges"])
        expected_names = list(self.metadata["weight_parameter_names"])
        if expected_names != [f"θ[{index}]" for index in range(len(expected_names))]:
            raise ValueError("Persisted VQC weight-parameter order does not match the frozen circuit contract")
        if len(self.weights) != len(expected_names) or len(self.weights) != 2 * len(self.feature_order):
            raise ValueError("Persisted VQC weight vector has the wrong length")

        self.classical_bundle = joblib.load(self.root / "artifacts/models/final_classical_8.joblib")
        self.qsvc_bundle = joblib.load(self.root / "artifacts/models/final_qsvc_8.joblib")
        if self.feature_order != self.classical_bundle["features"] or self.feature_order != self.qsvc_bundle["features"]:
            raise ValueError("Live VQC and frozen comparator feature orders differ")

        self._reference_raw = self.reference_records[self.feature_order].copy()
        self._reference_matrix = np.asarray(self.preprocessor.transform(self._reference_raw), dtype=float)
        qsvc_model = self.qsvc_bundle["model"]
        qsvc_training_matrix = np.asarray(
            self.qsvc_bundle["preprocessor"].transform(self.reference_records[self.qsvc_bundle["features"]]),
            dtype=float,
        )
        self._qsvc_support_vectors = qsvc_training_matrix[np.asarray(qsvc_model.support_, dtype=int)]
        self._qsvc_dual = np.asarray(qsvc_model.dual_coef_[0], dtype=float)
        self._qsvc_intercept = float(qsvc_model.intercept_[0])
        self._qsvc_classes = np.asarray(qsvc_model.classes_, dtype=int)

    def load_persisted_vqc(self) -> Any:
        """Load the serialized Qiskit model for artifact-integrity checks."""

        from qiskit_machine_learning.algorithms import VQC

        return VQC.from_dill(self.artifact_dir / "model/vqc.model")

    def _profile_frame(self, profile: Mapping[str, Any]) -> pd.DataFrame:
        missing = [feature for feature in self.feature_order if feature not in profile]
        if missing:
            raise ValueError(f"Missing live-profile features: {missing}")
        row: dict[str, Any] = {}
        for feature in self.feature_order:
            value = profile[feature]
            if feature in CATEGORICAL_VALUES:
                normalized = str(value).strip().lower()
                if normalized not in CATEGORICAL_VALUES[feature]:
                    raise ValueError(f"Unsupported category for {feature}: {value!r}")
                row[feature] = normalized
            else:
                numeric = float(value)
                if not np.isfinite(numeric):
                    raise ValueError(f"Non-finite numeric value for {feature}")
                row[feature] = numeric
        return pd.DataFrame([row], columns=self.feature_order)

    def transform_profile(self, profile: Mapping[str, Any]) -> np.ndarray:
        transformed = np.asarray(self.preprocessor.transform(self._profile_frame(profile)), dtype=float)
        if transformed.shape != (1, len(self.feature_order)):
            raise ValueError(f"Unexpected transformed profile shape: {transformed.shape}")
        return transformed

    def vqc_score(self, profile: Mapping[str, Any]) -> float:
        return float(frozen_vqc_class_scores(self.weights, self.transform_profile(profile))[0])

    @staticmethod
    def display_class(predicted_class: int) -> str:
        return "Pattern closer to CKD class" if int(predicted_class) == 1 else "Pattern closer to non-CKD class"

    def vqc_decision(self, profile: Mapping[str, Any]) -> ModelDecision:
        predicted = int(self.vqc_score(profile) >= float(self.metadata["classification_threshold"]))
        return ModelDecision("VQC", predicted, self.display_class(predicted))

    def _comparator_decision(self, bundle: Mapping[str, Any], name: str, profile: Mapping[str, Any]) -> ModelDecision:
        raw = self._profile_frame(profile)
        transformed = np.asarray(bundle["preprocessor"].transform(raw[bundle["features"]]), dtype=float)
        predicted = int(np.asarray(bundle["model"].predict(transformed), dtype=int)[0])
        return ModelDecision(name, predicted, self.display_class(predicted))

    def _qsvc_decision(self, profile: Mapping[str, Any]) -> ModelDecision:
        """Execute the frozen separable ZFeatureMap fidelity kernel without native Qiskit threads."""

        raw = self._profile_frame(profile)
        matrix = np.asarray(
            self.qsvc_bundle["preprocessor"].transform(raw[self.qsvc_bundle["features"]]),
            dtype=float,
        )
        # For ZFeatureMap(reps=1), each qubit is H then P(2*x); fidelity is
        # therefore the product of cos²(x_i-y_i) across the eight qubits.
        kernel = np.prod(
            np.cos(matrix[:, None, :] - self._qsvc_support_vectors[None, :, :]) ** 2,
            axis=2,
        )
        decision = kernel @ self._qsvc_dual + self._qsvc_intercept
        predicted = int(self._qsvc_classes[int(decision[0] > 0.0)])
        return ModelDecision("QSVC", predicted, self.display_class(predicted))

    def model_comparison(self, profile: Mapping[str, Any]) -> dict[str, Any]:
        decisions = [
            self.vqc_decision(profile),
            self._qsvc_decision(profile),
            self._comparator_decision(self.classical_bundle, "RBF SVM", profile),
        ]
        positives = sum(item.predicted_class for item in decisions)
        agreement = "ALL AGREE" if positives in {0, 3} else "2 OF 3 AGREE"
        return {"agreement": agreement, "decisions": decisions}

    def perturbation_explanation(self, profile: Mapping[str, Any], top_n: int = 5) -> pd.DataFrame:
        baseline = self.vqc_score(profile)
        rows: list[dict[str, Any]] = []
        for feature in self.feature_order:
            perturbed = dict(profile)
            perturbed[feature] = self.training_reference[feature]
            reference_score = self.vqc_score(perturbed)
            signed_change = baseline - reference_score
            rows.append(
                {
                    "Feature": READABLE_NAMES[feature],
                    "feature": feature,
                    "Absolute score change": abs(signed_change),
                    "Signed score change": signed_change,
                    "Direction": (
                        "Entered value shifts the model toward the CKD-class pattern"
                        if signed_change > 0
                        else "Entered value shifts the model toward the non-CKD-class pattern"
                        if signed_change < 0
                        else "No measurable change at displayed precision"
                    ),
                }
            )
        result = pd.DataFrame(rows).sort_values("Absolute score change", ascending=False, ignore_index=True)
        maximum = float(result["Absolute score change"].max())
        if maximum <= 1e-12:
            result["Model influence"] = "minimal"
        else:
            relative = result["Absolute score change"] / maximum
            result["Model influence"] = np.select(
                [relative >= 0.66, relative >= 0.33, result["Absolute score change"] <= 1e-9],
                ["strong influence", "moderate influence", "minimal"],
                default="subtle influence",
            )
        return result.head(top_n).copy()

    def similar_records(self, profile: Mapping[str, Any], top_n: int = 5) -> pd.DataFrame:
        query = self.transform_profile(profile)[0]
        distances = np.linalg.norm(self._reference_matrix - query, axis=1)
        ordered = np.argsort(distances)[:top_n]
        if len(ordered) == 0 or float(distances[ordered[0]]) > float(self.metadata["similarity_no_match_threshold"]):
            return pd.DataFrame()
        low = float(self.metadata["similarity_distance_tertiles"][0])
        high = float(self.metadata["similarity_distance_tertiles"][1])
        records: list[dict[str, Any]] = []
        for rank, position in enumerate(ordered, start=1):
            distance = float(distances[position])
            similarity = "High" if distance <= low else "Moderate" if distance <= high else "Weak"
            row = self.reference_records.iloc[int(position)]
            records.append(
                {
                    "Rank": rank,
                    "Similarity": similarity,
                    "Haemoglobin": row["hemo"],
                    "Albumin": row["al"],
                    "Specific gravity": row["sg"],
                    "Packed cell volume": row["pcv"],
                    "Serum creatinine": row["sc"],
                    "Diabetes": str(row["dm"]).title(),
                    "Appetite": str(row["appet"]).title(),
                    "Hypertension": str(row["htn"]).title(),
                    "Recorded dataset class": "CKD" if int(row["target"]) == 1 else "non-CKD",
                }
            )
        return pd.DataFrame(records)

    def clinician_review_checklist(self, profile: Mapping[str, Any]) -> list[str]:
        items = [
            "Verify entered measurements, categories, and units against the source record.",
            "Review abnormal or unusual laboratory results in the full clinical context.",
            "Review longitudinal kidney-function measurements where available.",
        ]
        if str(profile.get("dm", "no")).lower() == "yes" or str(profile.get("htn", "no")).lower() == "yes":
            items.append("Consider relevant recorded comorbidities, including diabetes and hypertension, in context.")
        else:
            items.append("Confirm whether relevant comorbidities such as diabetes or hypertension are recorded elsewhere.")
        items.extend(
            [
                "Compare findings with the organisation's approved CKD assessment pathway.",
                "Use qualified clinical judgement before ordering further investigation or referral.",
            ]
        )
        return items

    def analyse(self, profile: Mapping[str, Any]) -> dict[str, Any]:
        decision = self.vqc_decision(profile)
        return {
            "profile": dict(profile),
            "classification": decision.display,
            "predicted_class": decision.predicted_class,
            "score": self.vqc_score(profile),
            "factors": self.perturbation_explanation(profile),
            "similar_records": self.similar_records(profile),
            "comparison": self.model_comparison(profile),
            "checklist": self.clinician_review_checklist(profile),
        }

    def circuit_text(self) -> str:
        return (self.artifact_dir / "circuit.txt").read_text()
