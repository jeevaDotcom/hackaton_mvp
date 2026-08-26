from __future__ import annotations

import html
import math
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from src.results_repository import DATASETS, FEATURE_NAMES, ResultsRepository
from src.live_vqc_page import live_assessment_page
from src.ui_components import (
    chart_caption,
    comparison_metric,
    disease_record,
    evidence_table,
    feature_chips,
    hero_metric,
    hero_statement,
    limitation_callout,
    metadata_list,
    metric_strip,
    page_header,
    process_flow,
    research_note,
    section_header,
    verdict_badge,
)
from src.ui_theme import CHART_CLASSICAL, CHART_QUANTUM, TEXT_PRIMARY, TEXT_SECONDARY, apply_theme
from src.workstation_page import workstation_page


ROOT = Path(__file__).resolve().parent
st.set_page_config(
    page_title="Q-CARE | Evidence-First QML Benchmarking",
    page_icon="◌",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_theme()


@st.cache_resource
def repository() -> ResultsRepository:
    return ResultsRepository(ROOT)


repo = repository()


def _display_auc(value: float) -> str:
    """Match the frozen three-decimal reporting convention without rounding to 1.000."""
    return f"{math.floor(value * 1000) / 1000:.3f}"


def show_table(frame: pd.DataFrame, formats: dict[str, str] | None = None, height: int | None = None) -> None:
    config = {column: st.column_config.NumberColumn(format=fmt) for column, fmt in (formats or {}).items()}
    options: dict[str, object] = {"hide_index": True, "width": "stretch", "column_config": config}
    if height is not None:
        options["height"] = height
    st.dataframe(frame, **options)


def evidence_line_chart(frame: pd.DataFrame, x: str, y: str, sort: list[str] | None = None) -> None:
    """Render light, directly labelled experiment lines from the frozen long-form tables."""
    x_type = "ordinal" if sort else "quantitative"
    if sort:
        endpoint = frame[frame[x] == sort[-1]].copy()
    else:
        endpoint = frame.sort_values(x).groupby("Model", as_index=False).tail(1)

    shared = {
        "x": alt.X(x, type=x_type, sort=sort, title=x),
        "y": alt.Y(y, type="quantitative", scale=alt.Scale(zero=False), title=y),
        "color": alt.Color(
            "Model:N",
            scale=alt.Scale(domain=["RBF SVM", "QSVC"], range=[CHART_CLASSICAL, CHART_QUANTUM]),
            legend=None,
        ),
    }
    lines = alt.Chart(frame).mark_line(point=alt.OverlayMarkDef(filled=True, size=52), strokeWidth=2.5).encode(
        **shared,
        tooltip=[alt.Tooltip(x, type=x_type), "Model:N", alt.Tooltip(y, type="quantitative", format=".3f")],
    )
    labels = alt.Chart(endpoint).mark_text(align="left", dx=8, fontSize=12, fontWeight=600).encode(
        **shared,
        text="Model:N",
    )
    chart = (
        (lines + labels)
        .properties(height=320)
        .configure(background="transparent")
        .configure_view(stroke=None)
        .configure_axis(
            domain=False,
            gridColor="#E1E1DC",
            gridOpacity=0.75,
            labelColor=TEXT_SECONDARY,
            titleColor=TEXT_PRIMARY,
            labelFontSize=12,
            titleFontSize=13,
            titlePadding=12,
        )
    )
    st.altair_chart(chart, width="stretch")


def feature_transportability_chart(frame: pd.DataFrame) -> None:
    """Show signed within-cohort AUC without reversing low-oriented UCI signals."""
    feature_order = repo.primary_features
    cohort_scale = alt.Scale(
        domain=["UCI", "BD-KDD"],
        range=[CHART_CLASSICAL, CHART_QUANTUM],
    )
    shared_x = alt.X("feature:N", sort=feature_order, title="Frozen feature")
    intervals = alt.Chart(frame).mark_rule(strokeWidth=2).encode(
        x=shared_x,
        xOffset=alt.XOffset("Dataset:N"),
        y=alt.Y("CI low:Q", scale=alt.Scale(domain=[0, 1]), title="Signed univariate ROC-AUC"),
        y2="CI high:Q",
        color=alt.Color("Dataset:N", scale=cohort_scale, legend=alt.Legend(title="Cohort")),
    )
    points = alt.Chart(frame).mark_point(filled=True, size=115).encode(
        x=shared_x,
        xOffset=alt.XOffset("Dataset:N"),
        y=alt.Y("Signed AUC:Q", scale=alt.Scale(domain=[0, 1]), title="Signed univariate ROC-AUC"),
        color=alt.Color("Dataset:N", scale=cohort_scale, legend=alt.Legend(title="Cohort")),
        tooltip=[
            alt.Tooltip("Feature:N"),
            alt.Tooltip("Dataset:N", title="Cohort"),
            alt.Tooltip("Signed AUC:Q", format=".3f"),
            alt.Tooltip("CI low:Q", title="CI low", format=".3f"),
            alt.Tooltip("CI high:Q", title="CI high", format=".3f"),
        ],
    )
    chance = alt.Chart(pd.DataFrame({"chance": [0.5]})).mark_rule(
        color=TEXT_SECONDARY,
        strokeDash=[6, 5],
        strokeWidth=1.5,
    ).encode(y="chance:Q")
    chart = (
        (intervals + points + chance)
        .properties(height=360)
        .configure(background="transparent")
        .configure_view(stroke=None)
        .configure_axis(
            domain=False,
            gridColor="#E1E1DC",
            gridOpacity=0.75,
            labelColor=TEXT_SECONDARY,
            titleColor=TEXT_PRIMARY,
            labelFontSize=12,
            titleFontSize=13,
            titlePadding=12,
        )
        .configure_legend(labelColor=TEXT_SECONDARY, titleColor=TEXT_PRIMARY)
    )
    st.altair_chart(chart, width="stretch")


def overview_page() -> None:
    h = repo.headline_values()
    internal_qsvc_auc = _display_auc(repo.reference_metric(8, "qsvc", "roc_auc"))
    page_header(
        "Q-CARE",
        "Evidence-First Hybrid Quantum Healthcare Benchmarking",
        "Overview",
    )
    st.markdown('<p class="overview-support">Testing where quantum ML remains competitive — and where the evidence breaks.</p>', unsafe_allow_html=True)
    hero_statement("Internal feature stability did not guarantee external feature transportability.")
    comparison_metric(
        "Internal UCI CKD",
        f"1.000 / {internal_qsvc_auc}",
        "RBF SVM / QSVC ROC-AUC",
        "BD-KDD stress test",
        f"{h['external_classical_roc_auc']:.3f} / {h['external_roc_auc']:.3f}",
        "RBF SVM / QSVC ROC-AUC · both intervals include 0.5",
        "Target comparability was PARTIAL; neither model retained reliable discrimination.",
    )
    metric_strip(
        [
            ("Target comparability", "PARTIAL", "UCI CKD versus BD-KDD"),
            ("External RBF SVM", f"{h['external_classical_roc_auc']:.3f}", f"95% CI {h['external_classical_ci95_low']:.3f}-{h['external_classical_ci95_high']:.3f}"),
            ("External QSVC", f"{h['external_roc_auc']:.3f}", f"95% CI {h['external_qsvc_ci95_low']:.3f}-{h['external_qsvc_ci95_high']:.3f}"),
            ("Paired AUC difference", f"{h['external_paired_auc_delta']:+.3f}", f"95% CI {h['external_paired_delta_ci95_low']:+.3f} to {h['external_paired_delta_ci95_high']:+.3f}"),
        ]
    )
    section_header("Research question", "The platform keeps performance, resource cost, robustness, and transfer evidence in the same review surface.")
    research_note(
        "What Q-CARE asks",
        "When does quantum machine learning remain competitive with classical machine learning on biomedical data, and how does that conclusion change under feature reduction, missingness, measurement perturbation, dataset shift, and computational constraints?",
    )
    limitation_callout(
        "Core finding",
        "External transport failure reflected both target/cohort differences and changed feature–target relationships; therefore the experiment demonstrates transportability risk but cannot isolate pure conditional shift.",
    )


def replay_component() -> None:
    section_header("Experiment replay", "Choose a frozen Phase 2 result. The interface performs a lookup and never retrains a quantum model.")
    a, b, c, d = st.columns(4)
    with a:
        st.selectbox("Dataset", ["UCI CKD"], disabled=True)
    with b:
        representation_label = st.selectbox("Representation", ["8 clinical features", "6 clinical features", "8 PCA", "6 PCA"])
    with c:
        model = st.selectbox("Model", ["RBF SVM", "QSVC"])
    with d:
        st.selectbox("Execution", ["Precomputed · offline"], disabled=True)

    budget = int(representation_label.split()[0])
    representation = "pca" if "PCA" in representation_label else "clinical"
    result = repo.replay(representation, budget, model)
    metrics = (
        ("Sensitivity", result.sensitivity),
        ("Specificity", result.specificity),
        ("F1", result.f1),
        ("ROC-AUC", result.roc_auc),
    )
    metric_html = "".join(
        f'<div class="result-metric"><span>{html.escape(label)}</span><b>{value:.3f}</b></div>' for label, value in metrics
    )
    category = result.tolerance
    st.markdown(
        f"""<div class="replay-result">
        <div class="replay-header"><h3>{html.escape(model)} · {budget} {html.escape(representation)}</h3>{verdict_badge(category)}</div>
        <div class="result-metrics">{metric_html}</div></div>""",
        unsafe_allow_html=True,
    )
    metric_strip(
        [
            ("Mean runtime", f"{result.runtime_seconds:.4f} s", "Frozen training measurement"),
            ("Qubits", str(result.qubits) if result.qubits else "N/A", "Quantum models only"),
            ("Circuit depth", str(result.circuit_depth) if result.circuit_depth else "N/A", "Quantum models only"),
            ("Execution", "Offline", "Artifact lookup"),
        ]
    )
    chart_caption(result.protocol, result.source_artifact)


def ckd_page() -> None:
    h = repo.headline_values()
    page_header(
        "Controlled CKD comparison",
        "The primary experiment fixes feature budget, preprocessing boundaries, folds, and classifier regularisation before comparing kernels.",
        "CKD Benchmark",
    )
    hero_metric(
        "Stable clinical representation",
        f"{h['features_original']} → {h['features_primary']}",
        "Training-partition selection reduced the UCI CKD benchmark from 24 predictors to a stable eight-variable primary signature.",
    )
    process_flow(
        [
            ("Dataset", "400 UCI CKD records"),
            ("Feature reduction", "24 to 8 variables"),
            ("Matched models", "RBF SVM and QSVC"),
            ("Performance", "Repeated paired CV"),
            ("Interpretation", "Tolerance and runtime"),
        ]
    )

    section_header("Dataset", "Verified provenance and study shape are kept next to the benchmark evidence.")
    ckd = DATASETS["ckd"]
    metadata_list(
        [
            ("Source", f'<a href="{html.escape(ckd["url"])}">{html.escape(ckd["name"])}</a>'),
            ("Reported origin", html.escape(ckd["population"])),
            ("Study shape", f'{ckd["records"]} records · {ckd["original_features"]} predictors · binary CKD label'),
        ]
    )

    section_header("Feature reduction", "Eight readable clinical variables form the primary signature; six remains the compact secondary benchmark.")
    feature_chips([(code, FEATURE_NAMES[code]) for code in repo.primary_features])
    chart_caption("Codes and labels follow the UCI CKD metadata. The six-variable signature removes hypertension and serum creatinine.")
    with st.expander("View feature-stability evidence"):
        show_table(repo.feature_stability_table(), {"Selection frequency": "%.2f", "Mean rank": "%.1f", "Jaccard stability": "%.3f"})
        chart_caption("Wrapper-RFE eight-variable signature: mean pairwise Jaccard 0.912 across outer training partitions.")

    section_header("Classical vs quantum", "Repeated development-only evaluation at identical six- and eight-variable budgets.")
    show_table(repo.ckd_reference_table(), {"Sensitivity": "%.3f", "Specificity": "%.3f", "F1": "%.3f", "ROC-AUC": "%.3f", "Runtime (s)": "%.4f"})
    chart_caption("Development-only 5-fold CV repeated 10 times.", "artifacts/phase3/reference_cv_summary.csv")
    metric_strip(
        [
            ("QSVC sensitivity", f"{h['qsvc_sensitivity']:.3f}", "Eight variables"),
            ("Classical sensitivity", f"{h['classical_sensitivity']:.3f}", "Eight variables"),
            ("QSVC runtime", f"{h['runtime_ratio_8']:.0f}× slower", "Eight variables"),
            ("Tolerance", "Supported", "Internal descriptive rule"),
        ]
    )

    section_header("Feature-budget evidence", "The four-variable representation remains a stress test; selected clinical variables are compared with PCA at matched dimensions.")
    show_table(repo.phase2_budget_table("clinical"), {"Sensitivity": "%.3f", "Specificity": "%.3f", "F1": "%.3f", "ROC-AUC": "%.3f", "Runtime (s)": "%.4f"})
    limitation_callout(
        "Four variables are not retained",
        "The eight-variable representation is primary. Six remains an optional compact benchmark; four is a stress test only.",
    )
    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        show_table(repo.phase2_budget_table("pca"), {"Sensitivity": "%.3f", "Specificity": "%.3f", "F1": "%.3f", "ROC-AUC": "%.3f", "Runtime (s)": "%.4f"})
        chart_caption("Selected clinical variables were consistently stronger than PCA for the frozen QSVC, especially in specificity.")
    with right:
        st.image(
            str(ROOT / "reports/quantum/figures/03_selected_vs_pca.png"),
            caption="Measured Phase 2 comparison · selected clinical variables vs PCA",
            width="stretch",
        )
    replay_component()
    limitation_callout(
        "Interpretation boundary",
        "A reduced statistical feature budget does not establish that six or eight clinical tests are sufficient for care.",
    )


def robustness_page() -> None:
    h = repo.headline_values()
    internal_qsvc_auc = _display_auc(repo.reference_metric(8, "qsvc", "roc_auc"))
    page_header(
        "Robustness & shift",
        "Missing values, input variability, reduced training data, and a cross-cohort stress test show what survives beyond the clean benchmark.",
        "Robustness & Shift",
    )
    hero_statement("Internal feature stability did not guarantee external feature transportability.")
    process_flow(
        [
            ("Internal UCI", f"RBF 1.000 · QSVC {internal_qsvc_auc}"),
            ("Stress testing", "Missingness · perturbation · sample size"),
            ("BD-KDD", f"RBF {h['external_classical_roc_auc']:.3f} · QSVC {h['external_roc_auc']:.3f}"),
            ("Interpretation", "Partial target comparability"),
        ]
    )
    comparison_metric(
        "Internal UCI CKD",
        f"1.000 / {internal_qsvc_auc}",
        "RBF SVM / QSVC ROC-AUC",
        "BD-KDD cross-cohort stress test",
        f"{h['external_classical_roc_auc']:.3f} / {h['external_roc_auc']:.3f}",
        "RBF SVM / QSVC ROC-AUC",
        "Neither model demonstrated reliable better-than-random discrimination.",
    )
    metric_strip(
        [
            ("Target comparability", "PARTIAL", "Not like-for-like clinical validation"),
            ("RBF SVM 95% CI", f"{h['external_classical_ci95_low']:.3f}-{h['external_classical_ci95_high']:.3f}", "Includes chance discrimination"),
            ("QSVC 95% CI", f"{h['external_qsvc_ci95_low']:.3f}-{h['external_qsvc_ci95_high']:.3f}", "Includes chance discrimination"),
            ("Paired difference", f"{h['external_paired_auc_delta']:+.3f}", f"95% CI {h['external_paired_delta_ci95_low']:+.3f} to {h['external_paired_delta_ci95_high']:+.3f}"),
        ]
    )
    limitation_callout(
        "Statistical finding",
        "Neither the classical SVM nor QSVC demonstrated reliable better-than-random discrimination on BD-KDD, and their external AUC difference was not statistically distinguishable.",
    )

    section_header("Internal versus cross-cohort discrimination", "Both frozen models are shown with equal visual weight; the small external point-estimate difference is not interpreted as superiority.")
    show_table(repo.external_transport_table(), {"BD-KDD ROC-AUC": "%.3f"})
    research_note(
        "Primary external finding",
        "External transport failure reflected both target/cohort differences and changed feature–target relationships; therefore the experiment demonstrates transportability risk but cannot isolate pure conditional shift.",
    )

    feature_transport = repo.feature_transportability_table()
    section_header("Feature transportability", "Signed within-cohort AUC tests whether each frozen feature retained its label-ranking relationship.")
    feature_transportability_chart(feature_transport)
    chart_caption(
        "All eight internally predictive UCI features flattened toward chance-level discrimination in BD-KDD.",
        "reports/root_cause/univariate_auc.csv",
    )
    research_note(
        "How to read signed AUC",
        "Values far below 0.5 can still represent strong discrimination in the opposite direction; values close to 0.5 indicate weak ranking signal.",
    )

    section_header("Serum-creatinine cohort comparison", "Medians are reported in the documented mg/dL units; no CKD stage is inferred.")
    show_table(repo.creatinine_median_table(), {"UCI median (mg/dL)": "%.2f", "BD-KDD median (mg/dL)": "%.2f"})
    chart_caption(
        "Serum creatinine strongly separated CKD/non-CKD labels in UCI but barely separated the two BD-KDD labels.",
        "reports/root_cause/per_label_feature_profiles.csv",
    )

    missing = repo.missingness_summary()
    section_header("Missingness stress", "Added missing cells were introduced after folds were fixed; imputation was learned from each corrupted training partition.")
    evidence_line_chart(missing, "Additional missingness", "Sensitivity")
    chart_caption("Classical SVM retained higher sensitivity through 20% additional missingness.", "artifacts/phase3/missingness.csv")
    with st.expander("View missingness values"):
        show_table(missing, {"Sensitivity": "%.3f", "Specificity": "%.3f", "ROC-AUC": "%.3f"})

    perturb = repo.perturbation_summary()
    section_header("Measurement perturbation", "Gaussian noise was scaled to each numeric training-feature standard deviation; categorical inputs were unchanged.")
    evidence_line_chart(perturb, "Perturbation", "Flip rate", ["Low · 1% SD", "Medium · 5% SD", "High · 10% SD"])
    chart_caption("QSVC showed the higher prediction flip rate at the strongest tested perturbation.", "artifacts/phase3/perturbation.csv")
    with st.expander("View perturbation values"):
        show_table(perturb, {"Flip rate": "%.3f", "Sensitivity Δ": "%+.3f", "ROC-AUC Δ": "%+.3f"})

    training = repo.training_size_summary()
    section_header("Training-size experiment", "Performance at 25%, 50%, 75%, and 100% of outer-training data tests the small-sample hypothesis.")
    evidence_line_chart(training, "Training data", "Sensitivity")
    chart_caption("No QSVC small-sample advantage was observed.", "artifacts/quantum_training_size_results.csv")
    with st.expander("View training-size values"):
        show_table(training, {"Sensitivity": "%.3f", "ROC-AUC": "%.3f", "Runtime (s)": "%.4f"})

    section_header("Frozen external operating metrics", "Sensitivity, specificity, F1, ROC-AUC, and PR-AUC remain descriptive outputs of the cross-cohort stress test.")
    external = repo.external.rename(columns={"model": "Model", "sensitivity": "Sensitivity", "specificity": "Specificity", "f1": "F1", "roc_auc": "ROC-AUC", "pr_auc": "PR-AUC"})
    show_table(external[["Model", "Sensitivity", "Specificity", "F1", "ROC-AUC", "PR-AUC"]], {"Sensitivity": "%.3f", "Specificity": "%.3f", "F1": "%.3f", "ROC-AUC": "%.3f", "PR-AUC": "%.3f"})
    chart_caption("Frozen 8/8 cross-cohort stress test; target comparability was PARTIAL and no external retraining occurred.")


def cross_disease_page() -> None:
    page_header(
        "Cross-disease validation",
        "Cleveland and Pima test whether the benchmarking methodology travels beyond CKD; they are not patient-level transfers of the CKD model.",
        "Cross-Disease",
    )
    hero_statement("Methodological generalisation was inconsistent across datasets.")
    cross = repo.cross_disease_summary()
    heart = cross[(cross.disease == "Cleveland heart disease") & (cross.budget == 8)].set_index("model")
    diabetes = cross[(cross.disease.str.startswith("Pima")) & (cross.budget == 8)].set_index("model")
    heart_ratio = heart.loc["qsvc", "fit_seconds"] / heart.loc["classical_rbf_svm", "fit_seconds"]
    diabetes_ratio = diabetes.loc["qsvc", "fit_seconds"] / diabetes.loc["classical_rbf_svm", "fit_seconds"]
    h = repo.headline_values()
    records = [
        disease_record(
            "Chronic kidney disease",
            DATASETS["ckd"]["population"],
            "24 → 8",
            f"{h['classical_sensitivity']:.3f} / {repo.reference_metric(8, 'classical_rbf_svm', 'roc_auc'):.3f}",
            f"{h['qsvc_sensitivity']:.3f} / {_display_auc(repo.reference_metric(8, 'qsvc', 'roc_auc'))}",
            f"{h['runtime_ratio_8']:.0f}×",
            "SUPPORTED",
            "QSVC met the descriptive 0.05 tolerance internally; no superiority was demonstrated.",
        ),
        disease_record(
            "Cleveland heart disease",
            DATASETS["heart"]["population"],
            "13 → 8",
            f"{heart.loc['classical_rbf_svm', 'sensitivity']:.3f} / {heart.loc['classical_rbf_svm', 'roc_auc']:.3f}",
            f"{heart.loc['qsvc', 'sensitivity']:.3f} / {heart.loc['qsvc', 'roc_auc']:.3f}",
            f"{heart_ratio:.0f}×",
            "MIXED",
            "Sensitivity and ROC-AUC were close, but the full tolerance was missed on specificity.",
        ),
        disease_record(
            "Pima diabetes",
            DATASETS["diabetes"]["population"],
            "8 used",
            f"{diabetes.loc['classical_rbf_svm', 'sensitivity']:.3f} / {diabetes.loc['classical_rbf_svm', 'roc_auc']:.3f}",
            f"{diabetes.loc['qsvc', 'sensitivity']:.3f} / {diabetes.loc['qsvc', 'roc_auc']:.3f}",
            f"{diabetes_ratio:.0f}×",
            "NOT SUPPORTED",
            "QSVC sensitivity collapsed and the descriptive tolerance was not met.",
        ),
    ]
    st.markdown(f'<div class="disease-list">{"".join(records)}</div>', unsafe_allow_html=True)
    limitation_callout(
        "Population wording matters",
        "Pima Indians Diabetes represents an Arizona Native American population and is not an Indian-population dataset.",
    )
    with st.expander("View dataset provenance"):
        for key in ("ckd", "heart", "diabetes", "external"):
            item = DATASETS[key]
            st.markdown(f'- [{item["name"]}]({item["url"]}) — {item["population"]}; {item["records"]} records.')
    research_note("Interpretation", "Metrics are not averaged across diseases. Each dataset retains its own population, task, and verdict.")


def quantum_page() -> None:
    page_header(
        "Quantum evidence",
        "Each claim remains attached to its measured artifact, comparator, execution mode, and limitation—without a composite score.",
        "Quantum Evidence",
    )
    matrix = repo.evidence_matrix()
    rows = [tuple(row) for row in matrix[["Evidence dimension", "Classical", "Quantum", "Evidence verdict"]].itertuples(index=False, name=None)]
    evidence_table(rows)
    research_note(
        "External transportability",
        "Neither model retained meaningful label discrimination under the BD-KDD cross-cohort stress test.",
    )

    section_header("Frozen circuit", "The selected feature map is intentionally simple and shown exactly as executed.")
    left, right = st.columns([1.2, 0.8], gap="large")
    with left:
        st.markdown(f'<pre class="circuit">{html.escape(repo.circuit_text())}</pre>', unsafe_allow_html=True)
        chart_caption("Actual Qiskit ZFeatureMap after one decomposition: eight qubits, depth 2, 16 gates, no entanglement.", "artifacts/qsvc_z_reps1_8_circuit.txt")
    with right:
        research_note(
            "What it does",
            "Each selected clinical variable is encoded into a quantum rotation. The resulting states are compared through a fidelity kernel used by a support-vector classifier.",
        )
        limitation_callout(
            "Why no entanglement?",
            "More complex circuits did not produce better evidence in this experiment. This does not show that entanglement is unnecessary generally.",
        )

    h = repo.headline_values()
    primary_qsvc = next(item for item in repo.manifest["models"] if item["model"] == "qsvc" and item["budget"] == 8)
    resources = primary_qsvc["quantum_resources"]
    section_header("Runtime transparency", "Resource cost is displayed beside the predictive evidence, not relegated to a footnote.")
    metric_strip(
        [
            ("Classical SVM", "Baseline", "Matched Phase 2 CPU training time"),
            ("QSVC · 8 variables", f"{h['runtime_ratio_8']:.0f}× slower", "Exact statevector kernel"),
            ("QSVC · 6 variables", f"{h['runtime_ratio_6']:.0f}× slower", "Exact statevector kernel"),
            ("Primary circuit", f"Depth {resources['circuit_depth']}", f"{resources['qubit_count']} qubits · no entanglement"),
        ]
    )
    limitation_callout(
        "Simulator timing only",
        "Exact statevector kernel evaluation does not represent a demonstrated quantum-hardware speed-up.",
    )

    section_header("Finite-shot and simulated-noise evidence", "Shot stability and the limited noise experiment remain separate from the exact-statevector reference.")
    finite = repo.finite_shots[repo.finite_shots["mode"].isin(["ideal_qsvc", "finite_shot_qsvc"])].groupby("shots", dropna=False)[["sensitivity", "specificity", "roc_auc"]].mean().reset_index()
    finite["shots"] = finite.shots.map(lambda value: "Ideal" if value == 0 else f"{int(value):,}")
    show_table(finite.rename(columns={"shots": "Shots", "sensitivity": "Sensitivity", "specificity": "Specificity", "roc_auc": "ROC-AUC"}), {"Sensitivity": "%.3f", "Specificity": "%.3f", "ROC-AUC": "%.3f"})
    chart_caption("Finite-shot stability was supported only in the tested local simulation. The separate noise experiment used 48 training and 24 validation cases.")

    section_header("Final evidence summary")
    research_note(
        "Frozen verdict",
        "QSVC remained competitive on the internal CKD benchmark with reduced feature budgets, but no quantum performance, runtime, robustness, or generalisation advantage was demonstrated.",
    )
    errors = repo.validate_claim_registry()
    if errors:
        st.error("Claim registry validation failed. Display is blocked until artifact drift is resolved.")
    else:
        st.success("Claim registry validated against frozen artifacts.")
    st.download_button("Download Evidence Summary", data=repo.evidence_report_markdown(), file_name="qcare_evidence_summary.md", mime="text/markdown")


def footer() -> None:
    st.markdown(
        """<div class="footer"><b>Research prototype</b><br>Not intended for diagnosis, treatment, clinical decision-making, or patient triage. Limitations: small single-site primary dataset; missing data; unusually high internal benchmark performance; partial external target comparability; no prospective validation; no real quantum-hardware evaluation.</div>""",
        unsafe_allow_html=True,
    )


def live_page() -> None:
    live_assessment_page(ROOT)


with st.sidebar:
    st.markdown('<div class="sidebar-brand"><strong>Q-CARE</strong><span>Single-page clinical research workstation</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-workflow"><b>WORKFLOW</b><span>Input</span><span>Data health</span><span>Live assessment</span><span>Explanation</span><span>Benchmark</span><span>Robustness</span><span>Transportability</span><span>Evidence verdict</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-meta"><b>Execution</b><span>Frozen artifacts · deterministic · offline</span></div>', unsafe_allow_html=True)
    st.download_button(
        "Download Evidence Summary",
        data=repo.evidence_report_markdown(),
        file_name="qcare_evidence_summary.md",
        mime="text/markdown",
        key="sidebar_download",
    )


workstation_page(ROOT, repo)
footer()
