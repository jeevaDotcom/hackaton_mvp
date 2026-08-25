"""Single artifact-backed data layer for the Q-CARE Streamlit application."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


FEATURE_NAMES = {
    "hemo": "Haemoglobin",
    "al": "Albumin",
    "dm": "Diabetes mellitus",
    "sg": "Specific gravity",
    "pcv": "Packed cell volume",
    "appet": "Appetite",
    "htn": "Hypertension",
    "sc": "Serum creatinine",
}

DATASETS = {
    "ckd": {
        "name": "UCI Chronic Kidney Disease",
        "population": "Apollo Hospitals, Karaikudi, Tamil Nadu, India",
        "records": 400,
        "original_features": 24,
        "url": "https://archive.ics.uci.edu/dataset/336/chronic",
    },
    "external": {
        "name": "BD-KDD",
        "population": "Popular Diagnostic Centre, Savar Branch, Dhaka, Bangladesh",
        "records": 988,
        "original_features": 25,
        "url": "https://doi.org/10.7910/DVN/MB1LES",
    },
    "heart": {
        "name": "UCI Cleveland Heart Disease",
        "population": "Cleveland Clinic Foundation, United States",
        "records": 303,
        "original_features": 13,
        "url": "https://archive.ics.uci.edu/dataset/45/heart%2Bdisease",
    },
    "diabetes": {
        "name": "Pima Indians Diabetes / OpenML 37",
        "population": "Women of Pima heritage near Phoenix, Arizona, United States",
        "records": 768,
        "original_features": 8,
        "url": "https://www.openml.org/d/37",
    },
}


@dataclass(frozen=True)
class ReplayResult:
    dataset: str
    representation: str
    budget: int
    model: str
    sensitivity: float
    specificity: float
    f1: float
    roc_auc: float
    runtime_seconds: float
    qubits: int
    circuit_depth: int
    tolerance: str
    source_artifact: str
    protocol: str


class ResultsRepository:
    """Load frozen Phase 1–3 artifacts and expose UI-ready views."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or Path(__file__).resolve().parents[1])
        self.manifest = self._json("artifacts/final_model_manifest.json")
        self.claim_registry = self._json("artifacts/claim_registry.json")
        self.phase1 = self._json("artifacts/development_decision.json")
        self.phase2_locked = self._json("artifacts/phase2_locked_test_evaluation.json")
        self.reference = self._csv("artifacts/phase3/reference_cv_summary.csv")
        self.quantum = self._csv("artifacts/quantum_cv_summary.csv")
        self.feature_stability = self._csv("reports/feature_stability.csv")
        self.feature_stability_overall = self._csv("reports/feature_stability_overall.csv")
        self.missingness = self._csv("artifacts/phase3/missingness.csv")
        self.perturbation = self._csv("artifacts/phase3/perturbation.csv")
        self.training_size = self._csv("artifacts/quantum_training_size_results.csv")
        self.finite_shots = self._csv("artifacts/quantum_finite_shot_results.csv")
        self.noise = self._csv("artifacts/quantum_noise_results.csv")
        self.external = self._csv("artifacts/phase3/external_ckd_metrics.csv")
        self.external_bootstrap = self._csv("reports/root_cause/external_auc_bootstrap.csv")
        self.univariate_auc = self._csv("reports/root_cause/univariate_auc.csv")
        self.feature_profiles = self._csv("reports/root_cause/per_label_feature_profiles.csv")
        self.phase3c = self._json("reports/root_cause/phase3c_summary.json")
        self.cross_disease = self._csv("artifacts/phase3/cross_disease_cv.csv")

    def _csv(self, relative: str) -> pd.DataFrame:
        return pd.read_csv(self.root / relative)

    def _json(self, relative: str) -> Any:
        return json.loads((self.root / relative).read_text())

    @property
    def primary_features(self) -> list[str]:
        return list(self.manifest["feature_signatures"]["8"])

    @property
    def secondary_features(self) -> list[str]:
        return list(self.manifest["feature_signatures"]["6"])

    def reference_metric(self, budget: int, model: str, metric: str) -> float:
        row = self.reference[(self.reference.budget == budget) & (self.reference.model == model)]
        if len(row) != 1:
            raise KeyError((budget, model, metric))
        return float(row.iloc[0][f"{metric}_mean"])

    def runtime_ratio(self, budget: int) -> float:
        subset = self.quantum[(self.quantum.representation == "clinical") & (self.quantum.budget == budget)]
        classical = subset[(subset.model == "classical_rbf_svm") & (subset.feature_map_config == "rbf")].iloc[0]
        quantum = subset[(subset.model == "qsvc") & (subset.feature_map_config == "z_reps1")].iloc[0]
        return float(quantum.training_wall_seconds_mean / classical.training_wall_seconds_mean)

    def headline_values(self) -> dict[str, Any]:
        external_qsvc = self.external[self.external.model == "qsvc"].iloc[0]
        classical_uncertainty = self.external_bootstrap[
            self.external_bootstrap.configuration == "Frozen classical RBF SVM"
        ].iloc[0]
        qsvc_uncertainty = self.external_bootstrap[
            self.external_bootstrap.configuration == "Frozen QSVC"
        ].iloc[0]
        paired = self.phase3c["paired_delta"]
        return {
            "features_original": DATASETS["ckd"]["original_features"],
            "features_primary": 8,
            "qsvc_sensitivity": self.reference_metric(8, "qsvc", "sensitivity"),
            "classical_sensitivity": self.reference_metric(8, "classical_rbf_svm", "sensitivity"),
            "runtime_ratio_8": self.runtime_ratio(8),
            "runtime_ratio_6": self.runtime_ratio(6),
            "external_sensitivity": float(external_qsvc.sensitivity),
            "external_specificity": float(external_qsvc.specificity),
            "external_roc_auc": float(external_qsvc.roc_auc),
            "external_classical_roc_auc": float(classical_uncertainty.auc),
            "external_classical_ci95_low": float(classical_uncertainty.ci95_low),
            "external_classical_ci95_high": float(classical_uncertainty.ci95_high),
            "external_qsvc_ci95_low": float(qsvc_uncertainty.ci95_low),
            "external_qsvc_ci95_high": float(qsvc_uncertainty.ci95_high),
            "external_paired_auc_delta": float(paired["point"]),
            "external_paired_delta_ci95_low": float(paired["ci95_low"]),
            "external_paired_delta_ci95_high": float(paired["ci95_high"]),
        }

    def external_transport_table(self) -> pd.DataFrame:
        h = self.headline_values()
        return pd.DataFrame([
            {
                "Model": "RBF SVM",
                "Internal UCI ROC-AUC": f'{self.reference_metric(8, "classical_rbf_svm", "roc_auc"):.3f}',
                "BD-KDD ROC-AUC": h["external_classical_roc_auc"],
                "95% CI": f'{h["external_classical_ci95_low"]:.3f}-{h["external_classical_ci95_high"]:.3f}',
                "External assessment": "Indistinguishable from random",
            },
            {
                "Model": "QSVC",
                "Internal UCI ROC-AUC": f'{int(self.reference_metric(8, "qsvc", "roc_auc") * 1000) / 1000:.3f}',
                "BD-KDD ROC-AUC": h["external_roc_auc"],
                "95% CI": f'{h["external_qsvc_ci95_low"]:.3f}-{h["external_qsvc_ci95_high"]:.3f}',
                "External assessment": "Indistinguishable from random",
            },
        ])

    def feature_transportability_table(self) -> pd.DataFrame:
        value = self.univariate_auc.copy()
        value["Dataset"] = value.dataset.map({"UCI full source cohort": "UCI", "BD-KDD": "BD-KDD"})
        value["Feature"] = value.feature.map(lambda code: f"{code} - {FEATURE_NAMES[code]}")
        value["Signed AUC"] = value.auc.astype(float)
        value["CI low"] = value.ci95_low.astype(float)
        value["CI high"] = value.ci95_high.astype(float)
        order = {feature: index for index, feature in enumerate(self.primary_features)}
        value["feature_order"] = value.feature.map(order)
        return value.sort_values(["feature_order", "Dataset"])[
            ["feature", "Feature", "feature_order", "Dataset", "Signed AUC", "CI low", "CI high"]
        ]

    def creatinine_median_table(self) -> pd.DataFrame:
        value = self.feature_profiles[
            (self.feature_profiles.feature == "sc")
            & (self.feature_profiles.feature_type == "numeric")
        ].copy()
        medians = value.pivot(index="label_name", columns="dataset", values="median")
        return pd.DataFrame([
            {
                "Label": "CKD",
                "UCI median (mg/dL)": float(medians.loc["CKD", "UCI full source cohort"]),
                "BD-KDD median (mg/dL)": float(medians.loc["CKD", "BD-KDD"]),
            },
            {
                "Label": "non-CKD",
                "UCI median (mg/dL)": float(medians.loc["non-CKD", "UCI full source cohort"]),
                "BD-KDD median (mg/dL)": float(medians.loc["non-CKD", "BD-KDD"]),
            },
        ])

    def ckd_reference_table(self) -> pd.DataFrame:
        value = self.reference[self.reference.budget.isin([8, 6])].copy()
        value["Model"] = value.model.map({"classical_rbf_svm": "RBF SVM", "qsvc": "QSVC"})
        return value.rename(columns={
            "budget": "Features", "sensitivity_mean": "Sensitivity", "specificity_mean": "Specificity",
            "f1_mean": "F1", "roc_auc_mean": "ROC-AUC", "fit_seconds_mean": "Runtime (s)",
        })[["Features", "Model", "Sensitivity", "Specificity", "F1", "ROC-AUC", "Runtime (s)"]].sort_values(["Features", "Model"], ascending=[False, True])

    def feature_stability_table(self) -> pd.DataFrame:
        value = self.feature_stability[
            (self.feature_stability.method == "wrapper_rfe")
            & self.feature_stability.feature.isin(self.primary_features)
        ].copy()
        value["Variable"] = value.feature.map(lambda code: f"{code} — {FEATURE_NAMES[code]}")
        return value.rename(columns={
            "selection_frequency_8": "Selection frequency",
            "mean_rank": "Mean rank",
            "jaccard_mean_8": "Jaccard stability",
        })[["Variable", "Selection frequency", "Mean rank", "Jaccard stability"]].sort_values("Mean rank")

    def phase2_budget_table(self, representation: str = "clinical") -> pd.DataFrame:
        value = self.quantum[
            (self.quantum.representation == representation)
            & self.quantum.budget.isin([8, 6, 4])
            & self.quantum.feature_map_config.isin(["rbf", "z_reps1"])
        ].copy()
        value["Model"] = value.model.map({"classical_rbf_svm": "RBF SVM", "qsvc": "QSVC"})
        value["Status"] = value.budget.map({8: "PRIMARY", 6: "RETAINED", 4: "STRESS TEST — NOT RETAINED"})
        return value.rename(columns={
            "budget": "Features", "sensitivity_mean": "Sensitivity", "specificity_mean": "Specificity",
            "f1_mean": "F1", "roc_auc_mean": "ROC-AUC", "training_wall_seconds_mean": "Runtime (s)",
        })[["Features", "Model", "Sensitivity", "Specificity", "F1", "ROC-AUC", "Runtime (s)", "Status"]]

    def replay(self, representation: str, budget: int, model: str) -> ReplayResult:
        internal_model = {"RBF SVM": "classical_rbf_svm", "QSVC": "qsvc"}[model]
        config = "rbf" if model == "RBF SVM" else "z_reps1"
        row = self.quantum[
            (self.quantum.representation == representation)
            & (self.quantum.budget == budget)
            & (self.quantum.model == internal_model)
            & (self.quantum.feature_map_config == config)
        ]
        if len(row) != 1:
            raise KeyError((representation, budget, model))
        item = row.iloc[0]
        tolerance = "REFERENCE" if model == "RBF SVM" else self._quantum_tolerance(representation, budget)
        return ReplayResult(
            dataset="UCI CKD",
            representation=representation,
            budget=budget,
            model=model,
            sensitivity=float(item.sensitivity_mean),
            specificity=float(item.specificity_mean),
            f1=float(item.f1_mean),
            roc_auc=float(item.roc_auc_mean),
            runtime_seconds=float(item.training_wall_seconds_mean),
            qubits=int(item.qubit_count),
            circuit_depth=int(item.circuit_depth),
            tolerance=tolerance,
            source_artifact="artifacts/quantum_cv_summary.csv",
            protocol="Development-only repeated stratified 5-fold × 2-repeat CV; matched folds and feature budget.",
        )

    def _quantum_tolerance(self, representation: str, budget: int) -> str:
        subset = self.quantum[
            (self.quantum.representation == representation)
            & (self.quantum.budget == budget)
            & self.quantum.feature_map_config.isin(["rbf", "z_reps1"])
        ].set_index("model")
        deltas = [float(subset.loc["qsvc", f"{metric}_mean"] - subset.loc["classical_rbf_svm", f"{metric}_mean"]) for metric in ("sensitivity", "specificity", "f1", "roc_auc")]
        return "SUPPORTED" if min(deltas) >= -0.05 else "NOT SUPPORTED"

    def missingness_summary(self) -> pd.DataFrame:
        value = self.missingness.groupby(["missingness_fraction", "model"])[["sensitivity", "specificity", "roc_auc"]].mean().reset_index()
        value["Model"] = value.model.map({"classical_rbf_svm": "RBF SVM", "qsvc": "QSVC"})
        value["Additional missingness"] = value.missingness_fraction * 100
        return value.rename(columns={"sensitivity": "Sensitivity", "specificity": "Specificity", "roc_auc": "ROC-AUC"})[["Additional missingness", "Model", "Sensitivity", "Specificity", "ROC-AUC"]]

    def perturbation_summary(self) -> pd.DataFrame:
        value = self.perturbation.groupby(["noise_sd_fraction", "model"])[["flip_rate", "sensitivity_delta", "roc_auc_delta"]].mean().reset_index()
        value["Model"] = value.model.map({"classical_rbf_svm": "RBF SVM", "qsvc": "QSVC"})
        value["Perturbation"] = value.noise_sd_fraction.map({0.01: "Low · 1% SD", 0.05: "Medium · 5% SD", 0.10: "High · 10% SD"})
        return value.rename(columns={"flip_rate": "Flip rate", "sensitivity_delta": "Sensitivity Δ", "roc_auc_delta": "ROC-AUC Δ"})[["Perturbation", "Model", "Flip rate", "Sensitivity Δ", "ROC-AUC Δ"]]

    def training_size_summary(self) -> pd.DataFrame:
        value = self.training_size.groupby(["training_fraction", "model"])[["sensitivity", "roc_auc", "training_wall_seconds"]].mean().reset_index()
        value["Model"] = value.model.map({"classical_rbf_svm": "RBF SVM", "qsvc": "QSVC"})
        value["Training data"] = value.training_fraction * 100
        return value.rename(columns={"sensitivity": "Sensitivity", "roc_auc": "ROC-AUC", "training_wall_seconds": "Runtime (s)"})[["Training data", "Model", "Sensitivity", "ROC-AUC", "Runtime (s)"]]

    def cross_disease_summary(self) -> pd.DataFrame:
        value = self.cross_disease.groupby(["disease", "budget", "model"])[["sensitivity", "specificity", "roc_auc", "f1", "fit_seconds"]].mean().reset_index()
        value["Model"] = value.model.map({"classical_rbf_svm": "RBF SVM", "qsvc": "QSVC"})
        return value

    def circuit_text(self) -> str:
        return (self.root / "artifacts/qsvc_z_reps1_8_circuit.txt").read_text().rstrip()

    def evidence_matrix(self) -> pd.DataFrame:
        return pd.DataFrame([
            ["Predictive performance", "Stronger", "Competitive internally", "SUPPORTED"],
            ["Feature-budget performance", "Strong at 8 and 6", "Within 0.05 internally", "SUPPORTED"],
            ["Runtime", "Baseline", "Hundreds of times slower", "NOT SUPPORTED"],
            ["Missing-data robustness", "Stronger", "Degraded more", "NOT SUPPORTED"],
            ["Perturbation robustness", "Stronger", "Higher flip rate", "NOT SUPPORTED"],
            ["Small-sample behaviour", "Consistently strong", "No observed advantage", "NOT SUPPORTED"],
            ["Finite-shot robustness", "Not applicable", "Stable at tested shots", "SUPPORTED"],
            ["Simulated-noise robustness", "Not applicable", "Stable in limited simulation", "INCONCLUSIVE"],
            ["External generalisation", "NOT SUPPORTED", "NOT SUPPORTED", "TRANSPORTABILITY FAILURE"],
            ["Cross-disease generalisation", "Stronger overall", "Mixed heart; poor diabetes", "NOT SUPPORTED"],
        ], columns=["Evidence dimension", "Classical", "Quantum", "Evidence verdict"])

    def validate_claim_registry(self) -> list[str]:
        errors: list[str] = []
        values = self.headline_values()
        for claim in self.claim_registry["claims"]:
            key = claim.get("value_key")
            if claim["allowed"] and key:
                if key not in values:
                    errors.append(f"{claim['claim_id']}: unknown value_key {key}")
                elif abs(float(claim["value"]) - float(values[key])) > 1e-9:
                    errors.append(f"{claim['claim_id']}: registry value drift")
            for claim_key, claim_value in claim.get("values", {}).items():
                if claim_key not in values:
                    errors.append(f"{claim['claim_id']}: unknown value key {claim_key}")
                elif abs(float(claim_value) - float(values[claim_key])) > 1e-9:
                    errors.append(f"{claim['claim_id']}: registry value drift for {claim_key}")
            if claim["allowed"] and not (self.root / claim["artifact"]).exists():
                errors.append(f"{claim['claim_id']}: missing artifact")
            for artifact in claim.get("artifacts", []):
                if not (self.root / artifact).exists():
                    errors.append(f"{claim['claim_id']}: missing supporting artifact {artifact}")
        return errors

    def evidence_report_markdown(self) -> str:
        h = self.headline_values()
        return f"""# Q-CARE Evidence Summary

## Research question

When does quantum machine learning remain competitive with classical machine learning on biomedical data, and how does that conclusion change under feature reduction, missingness, measurement perturbation, dataset shift, and computational constraints?

## Datasets and protocol

UCI CKD (400 records, 24 predictors) is the controlled primary benchmark. Cleveland Heart Disease and Pima Diabetes test methodology transfer. BD-KDD is a full-signature external CKD transfer stress test. All comparisons preserve matched feature budgets and training partitions; robustness and model selection exclude the locked test.

## Main CKD result

At eight variables, repeated development CV sensitivity was {h['qsvc_sensitivity']:.3f} for QSVC and {h['classical_sensitivity']:.3f} for RBF SVM. QSVC met the predefined 0.05 descriptive tolerance internally but did not outperform the classical model.

## Runtime

The exact-statevector QSVC was {h['runtime_ratio_8']:.1f}× slower at eight variables and {h['runtime_ratio_6']:.1f}× slower at six. These are simulator benchmarks, not quantum-hardware speed results.

## Robustness

Classical SVM was more robust to added missingness and numeric perturbation.

## External transportability

On the BD-KDD cross-cohort stress test, RBF SVM ROC-AUC was {h['external_classical_roc_auc']:.3f} [95% CI {h['external_classical_ci95_low']:.3f}-{h['external_classical_ci95_high']:.3f}] and QSVC ROC-AUC was {h['external_roc_auc']:.3f} [95% CI {h['external_qsvc_ci95_low']:.3f}-{h['external_qsvc_ci95_high']:.3f}]. Neither model demonstrated reliable better-than-random discrimination, and the paired difference was not distinguishable. Target comparability with UCI CKD was PARTIAL.

External transport failure reflected both target/cohort differences and changed feature–target relationships; therefore the experiment demonstrates transportability risk but cannot isolate pure conditional shift. Internal feature stability did not guarantee external feature transportability.

## Cross-disease evidence

Cleveland results were mixed and missed the full tolerance on specificity. Pima QSVC was not competitive. Pima represents an Arizona Native American population and is not an Indian-population dataset.

## Supported claim

Q-CARE is a reproducible, evidence-first quantum/classical biomedical benchmarking platform that exposes both positive and negative quantum results.

## Limitations

Small single-site primary data, missing values, very high internal benchmark performance, partial external target comparability, no prospective validation, and no real quantum-hardware evaluation. Research prototype only; not intended for diagnosis, treatment, clinical decision-making, or patient triage.
"""
