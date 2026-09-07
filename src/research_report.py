"""Deterministic Q-CARE research evidence PDF generation."""

from __future__ import annotations

import io
import textwrap
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from src.csv_batch import FEATURE_ORDER, summarize_results
from src.live_vqc import READABLE_NAMES, LiveVQCService
from src.results_repository import ResultsRepository


ACCENT = "#315AD8"
INK = "#191B20"
MUTED = "#5C626C"
PALE = "#F7F5EF"
GRID = "#D9DAD5"
A4 = (8.27, 11.69)


@dataclass(frozen=True)
class ReportIdentity:
    experiment_id: str
    generated_at: datetime


class ReportStateError(ValueError):
    """Raised when a report is requested before a completed experiment exists."""


def generate_experiment_id(now: datetime | None = None, suffix: str | None = None) -> str:
    moment = now or datetime.now()
    short_suffix = suffix or uuid.uuid4().hex[:4].upper()
    return f"QCARE-{moment:%Y%m%d-%H%M%S}-{short_suffix}"


def _identity(experiment_id: str | None, generated_at: datetime | None) -> ReportIdentity:
    moment = generated_at or datetime.now()
    return ReportIdentity(experiment_id or generate_experiment_id(moment), moment)


def _fig(title: str, subtitle: str, page: int) -> tuple[plt.Figure, float]:
    fig = plt.figure(figsize=A4, facecolor=PALE)
    fig.text(0.08, 0.955, "Q-CARE", fontsize=19, weight="bold", color=INK)
    fig.text(0.08, 0.925, "Hybrid Quantum-Classical Healthcare Research Platform", fontsize=8.5, color=MUTED)
    fig.text(0.08, 0.865, title, fontsize=19, weight="bold", color=INK)
    fig.text(0.08, 0.832, subtitle, fontsize=9.5, color=MUTED)
    fig.text(0.08, 0.035, "RESEARCH PROTOTYPE · NOT A CLINICAL DIAGNOSTIC REPORT", fontsize=7.5, color=MUTED)
    fig.text(0.92, 0.035, f"{page}", fontsize=8, color=MUTED, ha="right")
    return fig, 0.785


def _paragraph(fig: plt.Figure, text: str, x: float, y: float, width: int = 92, size: float = 9.5, color: str = INK, leading: float = 0.022) -> float:
    lines = []
    for paragraph in str(text).split("\n"):
        lines.extend(textwrap.wrap(paragraph, width=width) or [""])
    for line in lines:
        fig.text(x, y, line, fontsize=size, color=color, va="top")
        y -= leading
    return y


def _section(fig: plt.Figure, label: str, y: float) -> float:
    fig.text(0.08, y, label.upper(), fontsize=9, weight="bold", color=ACCENT)
    return y - 0.035


def _rows(fig: plt.Figure, rows: Sequence[tuple[str, str]], y: float, value_width: int = 42) -> float:
    for label, value in rows:
        fig.text(0.08, y, str(label), fontsize=9, color=MUTED, va="top")
        wrapped = textwrap.wrap(str(value), width=value_width) or [""]
        fig.text(0.43, y, wrapped[0], fontsize=9, color=INK, va="top")
        for continuation in wrapped[1:]:
            y -= 0.021
            fig.text(0.43, y, continuation, fontsize=9, color=INK, va="top")
        y -= 0.032
    return y


def _save(fig: plt.Figure, pdf: PdfPages) -> None:
    pdf.savefig(fig, facecolor=fig.get_facecolor())
    plt.close(fig)


def _performance(repo: ResultsRepository, service: LiveVQCService) -> pd.DataFrame:
    svm = repo.replay("clinical", 8, "RBF SVM")
    qsvc = repo.replay("clinical", 8, "QSVC")
    vqc = service.metrics["vqc"]
    return pd.DataFrame([
        {"Model": "RBF-SVM", "Sensitivity": svm.sensitivity, "Specificity": svm.specificity, "F1": svm.f1, "ROC-AUC": svm.roc_auc},
        {"Model": "QSVC", "Sensitivity": qsvc.sensitivity, "Specificity": qsvc.specificity, "F1": qsvc.f1, "ROC-AUC": qsvc.roc_auc},
        {"Model": "VQC", "Sensitivity": vqc["sensitivity"], "Specificity": vqc["specificity"], "F1": vqc["f1"], "ROC-AUC": vqc["roc_auc"]},
    ])


def _model_outputs(result: Mapping[str, Any]) -> list[tuple[str, str]]:
    return [
        (item.model, "CKD-like" if item.predicted_class else "non-CKD-like")
        for item in result["comparison"]["decisions"]
    ]


def _agreement_text(agreement: str) -> str:
    if agreement == "ALL AGREE":
        return "3 OF 3 AGREE. All three research models produced the same binary class output for this profile. Agreement does not establish clinical diagnosis."
    if agreement == "2 OF 3 AGREE":
        return "2 OF 3 AGREE. Two of the three research models produced the same class output. Model disagreement should be reviewed alongside model-specific evidence."
    return "DISAGREEMENT. The research outputs should be reviewed individually."


def _profile_rows(profile: Mapping[str, Any]) -> list[tuple[str, str]]:
    return [(READABLE_NAMES[feature], str(profile.get(feature, "Unavailable"))) for feature in FEATURE_ORDER]


def _common_evidence_pages(
    pdf: PdfPages,
    repo: ResultsRepository,
    service: LiveVQCService,
    identity: ReportIdentity,
    mode: str,
    result: Mapping[str, Any] | None,
    profile: Mapping[str, Any] | None,
    source_name: str | None = None,
    researcher_confirmed: bool = False,
    corrected_values: bool = False,
    batch: pd.DataFrame | None = None,
    mapping: Mapping[str, str | None] | None = None,
) -> None:
    performance = _performance(repo, service)
    if batch is None:
        fig, y = _fig("Q-CARE Research Evidence Report", "A deterministic summary of one completed frozen-model experiment.", 1)
        y = _section(fig, "Experiment information", y)
        y = _rows(fig, [
            ("Experiment ID", identity.experiment_id),
            ("Generated", identity.generated_at.isoformat(timespec="seconds")),
            ("Input mode", mode),
            ("Feature count", "8"),
            ("Model mode", "Compare All"),
        ], y)
        y -= 0.01
        y = _section(fig, "Confirmed 8-feature profile", y)
        y = _rows(fig, _profile_rows(profile or {}), y, value_width=36)
        if mode == "Report Scan":
            y = _paragraph(fig, f"Input source: AI-assisted / OCR-assisted report extraction ({source_name or 'local report'}). Researcher verification: CONFIRMED.", 0.08, y - 0.01, width=96, size=9)
            if corrected_values:
                y = _paragraph(fig, "Researcher-modified values were used for this experiment.", 0.08, y - 0.01, width=96, size=9, color=MUTED)
        y -= 0.01
        y = _section(fig, "Model outputs", y)
        y = _rows(fig, _model_outputs(result or {}), y)
        if result and result.get("score") is not None:
            y = _paragraph(fig, f"Experimental decision score (VQC): {float(result['score']):.3f}. NOT a calibrated disease probability.", 0.08, y, width=96, size=8.5, color=MUTED)
        y -= 0.01
        y = _section(fig, "Model agreement", y)
        _paragraph(fig, _agreement_text((result or {}).get("comparison", {}).get("agreement", "DISAGREEMENT")), 0.08, y, width=96)
        _save(fig, pdf)
    else:
        summary = summarize_results(batch)
        fig, y = _fig("Q-CARE Research Evidence Report", "CSV Batch research summary; row-level detail remains in the downloadable CSV.", 1)
        y = _section(fig, "Experiment information", y)
        y = _rows(fig, [
            ("Experiment ID", identity.experiment_id),
            ("Generated", identity.generated_at.isoformat(timespec="seconds")),
            ("Input mode", "CSV Batch"),
            ("Input filename", source_name or "CSV batch"),
            ("Total rows", summary["total_rows"]),
            ("Valid rows", summary["valid_rows"]),
            ("Invalid rows", summary["invalid_rows"]),
        ], y)
        y = _section(fig, "Mapping and validation", y - 0.01)
        mapped = sum(value is not None for value in (mapping or {}).values())
        y = _paragraph(fig, f"Reviewed canonical mappings: {mapped}/8. Invalid rows were isolated and received no model output. Detailed row-level results are available in the downloadable Q-CARE batch-results CSV.", 0.08, y, width=55)
        y = _section(fig, "Batch output summary", y - 0.02)
        rows = [
            ("RBF-SVM CKD-like / non-CKD-like", _counts(batch, "rbf_svm_prediction")),
            ("QSVC CKD-like / non-CKD-like", _counts(batch, "qsvc_prediction")),
            ("VQC CKD-like / non-CKD-like", _counts(batch, "vqc_prediction")),
            ("3/3 agreement", summary["three_of_three"]),
            ("2/3 agreement", summary["two_of_three"]),
            ("Disagreement", summary["disagreement"]),
        ]
        _rows(fig, rows, y)
        fig.text(0.67, 0.79, "BATCH DISTRIBUTIONS", fontsize=8.5, weight="bold", color=ACCENT)
        valid_count = summary["valid_rows"]
        invalid_count = summary["invalid_rows"]
        ax = fig.add_axes([0.68, 0.55, 0.22, 0.12])
        ax.bar(["Valid", "Invalid"], [valid_count, invalid_count], color=[ACCENT, MUTED])
        ax.set_title("Validation", fontsize=7, loc="left")
        ax.tick_params(labelsize=6)
        ax.grid(axis="y", color=GRID, alpha=0.7)
        ax.set_facecolor(PALE)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax = fig.add_axes([0.68, 0.35, 0.22, 0.13])
        model_names = ["SVM", "QSVC", "VQC"]
        model_values = [
            [int(batch[batch.validation_status == "VALID"][f"{model}_prediction"].value_counts().get(1, 0)) for model in ("rbf_svm", "qsvc", "vqc")],
            [int(batch[batch.validation_status == "VALID"][f"{model}_prediction"].value_counts().get(0, 0)) for model in ("rbf_svm", "qsvc", "vqc")],
        ]
        positions = np.arange(3)
        ax.bar(positions - 0.16, model_values[0], 0.32, label="CKD-like", color=ACCENT)
        ax.bar(positions + 0.16, model_values[1], 0.32, label="non-CKD-like", color=MUTED)
        ax.set_title("Model outputs", fontsize=7, loc="left")
        ax.set_xticks(positions, model_names)
        ax.tick_params(labelsize=6)
        ax.grid(axis="y", color=GRID, alpha=0.7)
        ax.set_facecolor(PALE)
        ax.legend(frameon=False, fontsize=5, loc="upper right")
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax = fig.add_axes([0.68, 0.12, 0.22, 0.13])
        ax.bar(["3/3", "2/3", "Disagree"], [summary["three_of_three"], summary["two_of_three"], summary["disagreement"]], color=ACCENT)
        ax.set_title("Agreement", fontsize=7, loc="left")
        ax.tick_params(labelsize=6)
        ax.grid(axis="y", color=GRID, alpha=0.7)
        ax.set_facecolor(PALE)
        for spine in ax.spines.values():
            spine.set_visible(False)
        _save(fig, pdf)

    fig, y = _fig("Frozen benchmark evidence", "Artifact-backed performance and computational cost; no training runs during report generation.", 2)
    y = _section(fig, "Model performance comparison", y)
    ax = fig.add_axes([0.10, 0.47, 0.82, 0.28])
    x = np.arange(len(performance))
    width = 0.18
    for index, metric in enumerate(("Sensitivity", "Specificity", "F1", "ROC-AUC")):
        ax.bar(x + (index - 1.5) * width, performance[metric], width, label=metric)
    ax.set_xticks(x, performance["Model"])
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Frozen evidence value")
    ax.grid(axis="y", color=GRID, alpha=0.7)
    ax.set_facecolor(PALE)
    ax.legend(frameon=False, fontsize=7, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.18))
    for spine in ax.spines.values():
        spine.set_visible(False)
    y = _paragraph(fig, "Values are sourced from the frozen ResultsRepository artifacts. VQC is a separate existing holdout protocol and is not interchangeable with repeated-CV estimates.", 0.08, 0.43, width=96, size=8.5, color=MUTED)
    y = _section(fig, "Computational cost", 0.36)
    ratio = repo.runtime_ratio(8)
    vqc_seconds = float(service.metrics["training_runtime_seconds"])
    _rows(fig, [
        ("RBF-SVM benchmark/reference runtime", f"{repo.replay('clinical', 8, 'RBF SVM').runtime_seconds:.6f} s"),
        ("QSVC frozen benchmark runtime / relative cost", f"{repo.replay('clinical', 8, 'QSVC').runtime_seconds:.6f} s / approximately {ratio:.0f}x slower"),
        ("VQC training runtime", f"{vqc_seconds:.2f} s"),
        ("Inference distinction", "Interactive inference is separate from training cost."),
    ], 0.315)
    _paragraph(fig, "Measured in the project's local exact-statevector benchmarking setup; not a hardware benchmark.", 0.08, 0.135, width=96, size=8.5, color=MUTED)
    _save(fig, pdf)

    fig, y = _fig("Feature and quantum evidence", "Actual stored artifacts and profile-specific evidence only.", 3)
    if result and result.get("factors") is not None:
        factors = result["factors"]
        y = _section(fig, "Factors influencing this model output", y)
        ax = fig.add_axes([0.22, 0.49, 0.68, 0.24])
        factors = factors.sort_values("Absolute score change", ascending=True)
        ax.barh(factors["Feature"], factors["Absolute score change"], color=ACCENT)
        ax.set_xlabel("Absolute VQC score change")
        ax.grid(axis="x", color=GRID, alpha=0.7)
        ax.set_facecolor(PALE)
        for spine in ax.spines.values():
            spine.set_visible(False)
        _paragraph(fig, "MODEL INFLUENCE — NOT BIOLOGICAL CAUSATION. These are local perturbation values from the evaluated profile.", 0.08, 0.43, width=96, size=8.5, color=MUTED)
    else:
        y = _section(fig, "Factors influencing this model output", y)
        _paragraph(fig, "No individual feature influence is included for this batch summary.", 0.08, y, width=96, size=9, color=MUTED)
    y = _section(fig, "Feature-budget evidence", 0.37)
    _paragraph(fig, "24 original CKD predictors\n↓\nLeakage-safe feature selection\n↓\n8-feature primary representation", 0.08, 0.33, width=96, size=9.5, leading=0.019)
    selected = ", ".join(f"{feature} ({READABLE_NAMES[feature]})" for feature in repo.primary_features)
    _paragraph(fig, f"Selected variables: {selected}", 0.08, 0.19, width=110, size=7.8, leading=0.018)
    _paragraph(fig, _efficiency_text(repo), 0.08, 0.125, width=110, size=7.8, leading=0.018)
    _save(fig, pdf)

    fig, y = _fig("Quantum, robustness, and transportability", "Frozen architecture and Phase 3C evidence boundaries.", 4)
    y = _section(fig, "Quantum model evidence", y)
    y = _paragraph(fig, "QSVC: 8 qubits · ZFeatureMap · reps = 1 · no entanglement · fidelity quantum kernel · C = 0.5. The quantum circuit creates a similarity representation that is used by the support-vector classifier.\n\nVQC: 8 qubits · ZFeatureMap · RealAmplitudes · linear entanglement · COBYLA · 40 evaluations · 34.57 seconds training. The VQC contains trainable quantum-circuit parameters optimized by a classical optimizer.\n\nVQC status: WEAK — DISPLAY WITH CAUTION. The VQC is retained as a trainable quantum-model research demonstration and was not the strongest predictive model.", 0.08, y, width=96, size=8.5)
    y = _section(fig, "Robustness & stress tests", y - 0.01)
    y = _paragraph(fig, "Frozen missingness, numeric perturbation, reduced training size, finite-shot, and simulated-noise summaries are included in the repository artifacts. Missingness, perturbation, and training-size comparisons apply to RBF-SVM and QSVC; finite-shot and simulated-noise findings apply only to tested QSVC settings. No VQC robustness values are invented.", 0.08, y, width=96, size=8.5)
    y = _section(fig, "External transportability", y - 0.01)
    h = repo.headline_values()
    y = _paragraph(fig, f"UCI internal: RBF SVM ROC-AUC {repo.reference_metric(8, 'classical_rbf_svm', 'roc_auc'):.3f}; QSVC ROC-AUC {repo.reference_metric(8, 'qsvc', 'roc_auc'):.3f}. BD-KDD stress test: RBF SVM {h['external_classical_roc_auc']:.3f} (95% CI {h['external_classical_ci95_low']:.3f}-{h['external_classical_ci95_high']:.3f}); QSVC {h['external_roc_auc']:.3f} (95% CI {h['external_qsvc_ci95_low']:.3f}-{h['external_qsvc_ci95_high']:.3f}). Neither model demonstrated reliable better-than-random discrimination on the BD-KDD cross-cohort stress test. Target comparability: PARTIAL. Internal feature stability did not guarantee external feature transportability.", 0.08, y, width=96, size=8.5)
    y = _section(fig, "CKD stage research status", y - 0.01)
    _paragraph(fig, "Binary CKD-like classification: AVAILABLE — RESEARCH ONLY. Stage 1–5 prediction: NOT VALIDATED / NOT AVAILABLE. Stage cannot be inferred from the current Q-CARE binary classifier.", 0.08, y, width=96, size=8.5)
    _save(fig, pdf)

    fig, y = _fig("AUTOMATED EVIDENCE SUMMARY", "Deterministic wording assembled from current outputs, frozen artifacts, and claim boundaries.", 5)
    agreement = _agreement_text((result or {}).get("comparison", {}).get("agreement", "DISAGREEMENT")) if batch is None else _batch_agreement_text(summarize_results(batch))
    summary_text = f"{agreement}\n\nQSVC was internally competitive in the frozen benchmark but did not demonstrate a practical quantum advantage. External transportability was not established. The current outputs are binary research classifications only; no CKD stage is produced. Claim registry consistency: {'PASS' if not repo.validate_claim_registry() else 'REVIEW REQUIRED'}."
    y = _paragraph(fig, summary_text, 0.08, y, width=96, size=10)
    y = _section(fig, "Limitations", y - 0.02)
    _paragraph(fig, "Small development cohort; development from a single benchmark cohort; missing-heavy clinical dataset; model decision scores are not calibrated disease probabilities; VQC is weak; QSVC has substantial computational cost; external transportability not demonstrated; target comparability with BD-KDD is partial; no Stage 1–5 validation; no clinical deployment validation; research use only.", 0.08, y, width=96, size=8.8)
    y = _section(fig, "Responsible use", 0.30)
    _paragraph(fig, "This report summarizes a Q-CARE research experiment. It is not a medical diagnosis, treatment recommendation, triage decision, validated disease probability, or clinically validated CKD staging result.", 0.08, 0.265, width=96, size=10, color=INK)
    _save(fig, pdf)


def _counts(frame: pd.DataFrame, column: str) -> str:
    values = frame[frame.validation_status == "VALID"][column].value_counts()
    return f"{int(values.get(1, 0))} / {int(values.get(0, 0))}"


def _batch_agreement_text(summary: Mapping[str, int]) -> str:
    return f"Batch agreement: {summary['three_of_three']} rows with 3/3 agreement, {summary['two_of_three']} rows with 2/3 agreement, and {summary['disagreement']} disagreements among valid rows."


def _efficiency_text(repo: ResultsRepository) -> str:
    frame = repo.feature_efficiency_table()
    pivot = frame.pivot(index="Metric", columns="Representation", values="Value")
    return "The 8-feature representation retained most of the tested internal predictive performance while using a smaller information budget. " + "; ".join(f"{metric}: 24 features {pivot.loc[metric, '24 features']:.3f}, 8 features {pivot.loc[metric, '8 features']:.3f}" for metric in ("Sensitivity", "Specificity", "F1", "ROC-AUC"))


def create_single_patient_report(
    repo: ResultsRepository,
    service: LiveVQCService,
    result: Mapping[str, Any] | None,
    *,
    mode: str = "Manual",
    source_name: str | None = None,
    researcher_confirmed: bool = False,
    corrected_values: bool = False,
    experiment_id: str | None = None,
    generated_at: datetime | None = None,
) -> bytes:
    if result is None or not result.get("comparison"):
        raise ReportStateError("A completed model experiment is required before generating a report.")
    identity = _identity(experiment_id, generated_at)
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        _common_evidence_pages(
            pdf, repo, service, identity, "Report Scan" if mode == "Report Scan" else "Manual",
            result, result.get("profile"), source_name, researcher_confirmed, corrected_values,
        )
    return buffer.getvalue()


def create_batch_report(
    repo: ResultsRepository,
    service: LiveVQCService,
    results: pd.DataFrame | None,
    *,
    source_name: str | None = None,
    mapping: Mapping[str, str | None] | None = None,
    experiment_id: str | None = None,
    generated_at: datetime | None = None,
) -> bytes:
    if results is None or results.empty:
        raise ReportStateError("A completed CSV batch experiment is required before generating a report.")
    identity = _identity(experiment_id, generated_at)
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        _common_evidence_pages(pdf, repo, service, identity, "CSV Batch", None, None, source_name, batch=results, mapping=mapping)
    return buffer.getvalue()
