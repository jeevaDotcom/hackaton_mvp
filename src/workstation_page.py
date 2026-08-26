"""Single-page Q-CARE clinical research workstation."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from src.data_health import DataHealthResult, analyse_data_health
from src.live_vqc import READABLE_NAMES, UNITS, LiveVQCService, ModelDecision
from src.live_vqc_page import load_live_service
from src.results_repository import FEATURE_NAMES, ResultsRepository
from src.ui_components import (
    chart_caption,
    feature_chips,
    limitation_callout,
    metadata_list,
    metric_strip,
    process_flow,
    research_note,
    section_header,
)
from src.ui_theme import CHART_CLASSICAL, CHART_QUANTUM, TEXT_SECONDARY


WORKSTATION_KEYS = {feature: f"workstation_{feature}" for feature in ("hemo", "al", "dm", "sg", "pcv", "appet", "htn", "sc")}


def _set_profile(profile: dict[str, Any]) -> None:
    for feature, value in profile.items():
        st.session_state[WORKSTATION_KEYS[feature]] = value
    st.session_state.pop("workstation_analysis", None)


def _initialise_profile(service: LiveVQCService) -> None:
    for feature, value in service.presets["mixed"]["profile"].items():
        st.session_state.setdefault(WORKSTATION_KEYS[feature], value)


def _range_help(service: LiveVQCService, feature: str) -> str:
    low, high = service.observed_ranges[feature]
    return f"Observed UCI development-data range: {low:g}–{high:g} {UNITS[feature]}. Not a clinical reference range."


def _profile_form(service: LiveVQCService) -> tuple[bool, dict[str, Any]]:
    with st.form("workstation_profile_form"):
        left, middle, right = st.columns(3, gap="large")
        with left:
            hemo = st.number_input("Haemoglobin (g/dL)", step=0.1, format="%.1f", key=WORKSTATION_KEYS["hemo"], help=_range_help(service, "hemo"))
            sg = st.number_input("Specific gravity", step=0.005, format="%.3f", key=WORKSTATION_KEYS["sg"], help=_range_help(service, "sg"))
            pcv = st.number_input("Packed cell volume (%)", step=1.0, format="%.1f", key=WORKSTATION_KEYS["pcv"], help=_range_help(service, "pcv"))
        with middle:
            al = st.selectbox("Albumin (dataset ordinal grade)", [0.0, 1.0, 2.0, 3.0, 4.0, 5.0], key=WORKSTATION_KEYS["al"], help="Observed UCI coding: 0–5; not a clinical reference range.")
            sc = st.number_input("Serum creatinine (mg/dL)", step=0.1, format="%.2f", key=WORKSTATION_KEYS["sc"], help=_range_help(service, "sc"))
            appet = st.selectbox("Appetite", ["good", "poor"], key=WORKSTATION_KEYS["appet"])
        with right:
            dm = st.selectbox("Diabetes mellitus", ["no", "yes"], key=WORKSTATION_KEYS["dm"])
            htn = st.selectbox("Hypertension", ["no", "yes"], key=WORKSTATION_KEYS["htn"])
            st.caption("Categories reproduce benchmark coding; Q-CARE does not infer them.")
        submitted = st.form_submit_button("ANALYSE PROFILE", type="primary", use_container_width=True)
    return submitted, {"hemo": hemo, "al": al, "dm": dm, "sg": sg, "pcv": pcv, "appet": appet, "htn": htn, "sc": sc}


def _worker_safe_qsvc_decision(service: LiveVQCService, profile: dict[str, Any]) -> ModelDecision:
    """Run the frozen QSVC analytically, including in older long-lived app sessions."""

    bundle = service.qsvc_bundle
    model = bundle["model"]
    raw = service._profile_frame(profile)  # noqa: SLF001 - shared frozen service contract
    query = np.asarray(bundle["preprocessor"].transform(raw[bundle["features"]]), dtype=float)
    training = np.asarray(
        bundle["preprocessor"].transform(service.reference_records[bundle["features"]]),
        dtype=float,
    )
    support_vectors = training[np.asarray(model.support_, dtype=int)]
    kernel = np.prod(np.cos(query[:, None, :] - support_vectors[None, :, :]) ** 2, axis=2)
    decision = kernel @ np.asarray(model.dual_coef_[0], dtype=float) + float(model.intercept_[0])
    predicted = int(np.asarray(model.classes_, dtype=int)[int(decision[0] > 0.0)])
    return ModelDecision("QSVC", predicted, service.display_class(predicted))


def _run_worker_safe_analysis(service: LiveVQCService, profile: dict[str, Any]) -> dict[str, Any]:
    vqc = service.vqc_decision(profile)
    qsvc = _worker_safe_qsvc_decision(service, profile)
    classical = service._comparator_decision(service.classical_bundle, "RBF SVM", profile)  # noqa: SLF001
    decisions = [vqc, qsvc, classical]
    positives = sum(item.predicted_class for item in decisions)
    agreement = "ALL AGREE" if positives in {0, 3} else "2 OF 3 AGREE"
    return {
        "profile": dict(profile),
        "classification": vqc.display,
        "predicted_class": vqc.predicted_class,
        "score": service.vqc_score(profile),
        "factors": service.perturbation_explanation(profile),
        "similar_records": service.similar_records(profile),
        "comparison": {"agreement": agreement, "decisions": decisions},
        "checklist": service.clinician_review_checklist(profile),
    }


def _patient_entry(service: LiveVQCService) -> None:
    section_header("Patient input", "Eight frozen UCI variables; observed ranges are descriptive and are not clinical reference ranges.")
    st.caption("Dataset demonstration profiles · each preset is an actual complete UCI development record.")
    columns = st.columns(3, gap="small")
    for column, key in zip(columns, ("ckd_like", "non_ckd_like", "mixed"), strict=True):
        preset = service.presets[key]
        with column:
            st.button(preset["label"], key=f"workstation_preset_{key}", on_click=_set_profile, args=(preset["profile"],), use_container_width=True, help=preset["source"])
    submitted, profile = _profile_form(service)
    if submitted:
        with st.spinner("Running frozen three-model assessment…"):
            st.session_state["workstation_analysis"] = _run_worker_safe_analysis(service, profile)


def _dataset_entry(service: LiveVQCService) -> None:
    section_header("Dataset upload", "Upload a CSV, select its target, and run schema and data-health checks. No model is trained or run automatically.")
    uploaded = st.file_uploader("Upload biomedical CSV", type=["csv"], key="workstation_dataset_upload")
    if uploaded is None:
        research_note("Awaiting CSV", "Q-CARE will detect columns only after a local CSV is supplied. Uploaded data is processed in this running application session.")
        return
    try:
        frame = pd.read_csv(uploaded)
    except Exception as error:  # pragma: no cover - Streamlit-facing parse boundary
        st.error(f"CSV could not be parsed: {error}")
        return
    if frame.empty or not len(frame.columns):
        st.error("The uploaded CSV contains no usable rows or columns.")
        return
    st.caption(f"Detected {len(frame):,} rows and {len(frame.columns):,} columns.")
    target = st.selectbox("Select target column", list(frame.columns), key="workstation_target")
    if st.button("RUN DATA HEALTH CHECK", type="primary", key="run_data_health"):
        try:
            st.session_state["workstation_data_health"] = analyse_data_health(frame, str(target), service.observed_ranges)
        except ValueError as error:
            st.error(str(error))


def _model_table(result: dict[str, Any]) -> tuple[pd.DataFrame, str]:
    decisions = {item.model: item for item in result["comparison"]["decisions"]}
    rows = [
        ("RBF SVM", decisions["RBF SVM"], "Classical", "Strong benchmark"),
        ("QSVC", decisions["QSVC"], "Quantum kernel", "Competitive internally"),
        ("VQC", decisions["VQC"], "Variational QML", "Weak experimental model"),
    ]
    table = pd.DataFrame([
        {"Model": name, "Prediction": "CKD-like" if item.predicted_class else "non-CKD-like", "Model type": model_type, "Evidence status": status}
        for name, item, model_type, status in rows
    ])
    agreement = "3 OF 3 AGREE" if result["comparison"]["agreement"] == "ALL AGREE" else "2 OF 3 AGREE"
    return table, agreement


def _factor_panel(factors: pd.DataFrame) -> None:
    maximum = max(float(factors["Absolute score change"].max()), 1e-12)
    rendered: list[str] = []
    for _, row in factors.iterrows():
        width = max(2.0, 100.0 * float(row["Absolute score change"]) / maximum)
        rendered.append(
            f'<div class="influence-row"><div><b>{html.escape(str(row["Feature"]))}</b><span>{html.escape(str(row["Model influence"]))}</span></div>'
            f'<div class="influence-measure"><div class="influence-track"><i style="width:{width:.1f}%"></i></div><small>score change {float(row["Absolute score change"]):.3f}</small></div>'
            f'<p>{html.escape(str(row["Direction"]))}</p></div>'
        )
    st.markdown(f'<div class="influence-list">{"".join(rendered)}</div>', unsafe_allow_html=True)
    st.caption("Local perturbation moves one entered value to the UCI development median or mode while all other inputs remain fixed.")


def _live_assessment(service: LiveVQCService) -> None:
    section_header("Live model assessment", "The same entered profile is evaluated by the frozen RBF SVM, QSVC, and VQC.")
    result = st.session_state.get("workstation_analysis")
    if result is None:
        research_note("Awaiting profile analysis", "Enter a profile above and select ANALYSE PROFILE. No training occurs during this interaction.")
        st.markdown('<div class="agreement-line"><span>Model agreement</span><strong>AWAITING PROFILE</strong></div>', unsafe_allow_html=True)
    else:
        table, agreement = _model_table(result)
        st.dataframe(table, hide_index=True, width="stretch")
        st.markdown(f'<div class="agreement-line"><span>Model agreement</span><strong>{agreement}</strong></div>', unsafe_allow_html=True)
        if agreement != "3 OF 3 AGREE":
            limitation_callout("Model disagreement", "Model disagreement indicates uncertainty. This research output must not be interpreted as diagnosis.")
        else:
            st.caption("Agreement among research models does not establish diagnosis or clinical validity.")

    section_header("VQC performance transparency", "The live trainable quantum model is shown honestly alongside stronger frozen comparators.")
    vqc = service.metrics["vqc"]
    metric_strip([
        ("Sensitivity", f'{vqc["sensitivity"]:.3f}', "Existing 80-record holdout"),
        ("Specificity", f'{vqc["specificity"]:.3f}', "Existing 80-record holdout"),
        ("F1", f'{vqc["f1"]:.3f}', "Existing 80-record holdout"),
        ("ROC-AUC", f'{vqc["roc_auc"]:.3f}', "Uncalibrated circuit score"),
    ])
    st.markdown('<div class="vqc-honesty"><b>WEAK — DISPLAY WITH CAUTION</b><span>The VQC is included as a live trainable quantum-model demonstration. It is not the strongest predictive model in Q-CARE.</span></div>', unsafe_allow_html=True)

    if result is None:
        return
    st.markdown(f'<div class="workstation-score"><span>VQC research model score</span><strong>{float(result["score"]):.3f}</strong><small>Not a calibrated disease probability</small></div>', unsafe_allow_html=True)
    section_header("Factors influencing this model output", "Ranked model sensitivity—not causes, diagnosis, or clinical attribution.")
    _factor_panel(result["factors"])

    section_header("Similar historical benchmark records", "Nearest UCI records after the same frozen preprocessing used by the VQC.")
    if result["similar_records"].empty:
        research_note("No close historical benchmark matches found", "The entered profile lies beyond the stored similarity threshold.")
    else:
        columns = ["Rank", "Similarity", "Recorded dataset class", "Serum creatinine", "Haemoglobin", "Albumin", "Specific gravity", "Packed cell volume", "Diabetes", "Appetite", "Hypertension"]
        st.dataframe(result["similar_records"][columns], hide_index=True, width="stretch")
    st.caption("Similarity to historical benchmark records does not establish diagnosis.")

    section_header("Clinician review checklist", "Generic research-support prompts; no treatment advice or automatic clinical action.")
    checklist = [
        "Verify entered measurements and units.",
        "Review kidney-function trends where available.",
        "Review diabetes and hypertension context.",
        "Compare findings with the approved local CKD pathway.",
        "Use qualified clinical judgement.",
        "Consider further investigation only according to clinical protocol.",
    ]
    st.markdown('<ol class="review-list">' + "".join(f"<li>{html.escape(item)}</li>" for item in checklist) + "</ol>", unsafe_allow_html=True)


def _data_health_disclosure(result: DataHealthResult | None) -> None:
    with st.expander("Data health check", expanded=False):
        section_header("Data health check", "Compatibility is assessed before any frozen CKD model evaluation is considered.")
        if result is None:
            research_note("No dataset checked", "Choose Upload biomedical dataset above, supply a CSV, select its target, and run the data-health check.")
            return
        st.markdown(f'<div class="dataset-status {result.status.lower().replace(" ", "-")}"><span>Dataset status</span><strong>{result.status}</strong></div>', unsafe_allow_html=True)
        metric_strip([
            ("Samples", f"{result.samples:,}", "Uploaded rows"),
            ("Features", str(result.features), "Excluding selected target"),
            ("Missing values", f"{result.missing_values:,}", f"{result.missing_fraction:.1%} of cells"),
            ("Required coverage", f"{result.required_coverage}/{result.required_total}", "Frozen CKD variables"),
        ])
        checks = pd.DataFrame([
            ("Target", result.target),
            ("Target classes", str(result.target_classes)),
            ("Class balance", result.class_balance),
            ("Duplicates", str(result.duplicates)),
            ("Feature types", f"{result.numeric_features} numeric / {result.categorical_features} categorical"),
            ("Range anomalies", str(result.range_anomalies)),
            ("Likely dataset shift", "Review indicated" if result.likely_shift else "No simple flag"),
        ], columns=["Check", "Observed"])
        st.dataframe(checks, hide_index=True, width="stretch")
        for note in result.notes:
            st.markdown(f"- {note}")
        if not result.can_evaluate_frozen_ckd_models:
            limitation_callout("Model evaluation blocked", "Dataset compatibility must be reviewed before model evaluation.")
        else:
            research_note("Schema ready", "The automated check passed. This does not establish target comparability, clinical validity, or permission to train a quantum model.")


def _feature_engineering(repo: ResultsRepository) -> None:
    with st.expander("Feature engineering", expanded=False):
        section_header("Feature reduction", "Wrapper RFE reduced the original UCI CKD predictors inside the development workflow.")
        st.markdown('<div class="reduction-line"><strong>24</strong><span>original CKD predictors</span><i>→</i><strong>8</strong><span>selected variables</span></div>', unsafe_allow_html=True)
        metadata_list([("Selection method", "Wrapper RFE"), ("Evidence boundary", "Stable within the UCI development cohort")])
        feature_chips([(feature, FEATURE_NAMES[feature]) for feature in repo.primary_features])
        st.dataframe(repo.feature_stability_table(), hide_index=True, width="stretch")
        st.caption("Internal feature stability ≠ external feature transportability.")


def _three_model_benchmark(repo: ResultsRepository, service: LiveVQCService) -> None:
    with st.expander("Classical / quantum benchmark", expanded=False):
        section_header("Three-model comparison", "Same eight input variables; protocols are labelled because VQC and repeated-CV estimates are not interchangeable.")
        svm = repo.replay("clinical", 8, "RBF SVM")
        qsvc = repo.replay("clinical", 8, "QSVC")
        vqc = service.metrics["vqc"]
        rows = [
            {"Model": "RBF SVM", "Model type": "Classical", "Sensitivity": svm.sensitivity, "Specificity": svm.specificity, "F1": svm.f1, "ROC-AUC": svm.roc_auc, "Runtime (s)": svm.runtime_seconds, "Evidence": "Strongest overall benchmark", "Protocol": "Repeated development CV"},
            {"Model": "QSVC", "Model type": "Quantum kernel", "Sensitivity": qsvc.sensitivity, "Specificity": qsvc.specificity, "F1": qsvc.f1, "ROC-AUC": qsvc.roc_auc, "Runtime (s)": qsvc.runtime_seconds, "Evidence": "Competitive internally; much slower", "Protocol": "Repeated development CV"},
            {"Model": "VQC", "Model type": "Trainable quantum", "Sensitivity": vqc["sensitivity"], "Specificity": vqc["specificity"], "F1": vqc["f1"], "ROC-AUC": vqc["roc_auc"], "Runtime (s)": service.metrics["training_runtime_seconds"], "Evidence": "Weak experimental model", "Protocol": "Existing 80-record holdout"},
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        limitation_callout("Evidence interpretation", "Classical is the strongest benchmark. QSVC was competitive internally but hundreds of times slower. VQC demonstrates trainable QML but has weaker predictive performance.")


def _quantum_circuits(repo: ResultsRepository, service: LiveVQCService) -> None:
    with st.expander("Actual quantum circuits", expanded=False):
        section_header("QSVC circuit", "A non-trainable quantum representation used to construct a fidelity kernel for a classical SVM.")
        metadata_list([("Architecture", "ZFeatureMap · 8 qubits · reps 1 · no entanglement"), ("Role", "Quantum similarity/kernel representation")])
        st.code(repo.circuit_text(), language="text")
        section_header("VQC circuit", "A trainable parameterised circuit whose weights were learned by a classical optimiser.")
        metadata_list([("Architecture", "8-qubit ZFeatureMap + RealAmplitudes · linear entanglement"), ("Optimiser", "COBYLA · 40 evaluations")])
        st.code(service.circuit_text(), language="text")


def _robustness(repo: ResultsRepository) -> None:
    with st.expander("Robustness", expanded=False):
        section_header("Frozen robustness experiments", "RBF SVM and QSVC only. No VQC robustness values are invented.")
        tabs = st.tabs(["Missingness", "Perturbation", "Training size", "Finite shots", "Simulated noise"])
        with tabs[0]:
            st.dataframe(repo.missingness_summary(), hide_index=True, width="stretch")
        with tabs[1]:
            st.dataframe(repo.perturbation_summary(), hide_index=True, width="stretch")
        with tabs[2]:
            st.dataframe(repo.training_size_summary(), hide_index=True, width="stretch")
        with tabs[3]:
            finite = repo.finite_shots.groupby("shots")[["sensitivity", "specificity", "f1", "roc_auc"]].mean().reset_index()
            st.dataframe(finite.rename(columns={"shots": "Shots", "sensitivity": "Sensitivity", "specificity": "Specificity", "f1": "F1", "roc_auc": "ROC-AUC"}), hide_index=True, width="stretch")
        with tabs[4]:
            noise = repo.noise.groupby("condition")[["sensitivity", "specificity", "f1", "roc_auc"]].mean().reset_index()
            st.dataframe(noise.rename(columns={"condition": "Condition", "sensitivity": "Sensitivity", "specificity": "Specificity", "f1": "F1", "roc_auc": "ROC-AUC"}), hide_index=True, width="stretch")
        chart_caption("Classical SVM was more robust to added missingness and perturbation. Finite-shot and simulated-noise findings apply only to the tested QSVC settings.", "Frozen Phase 3 artifacts")


def _feature_transport_chart(repo: ResultsRepository) -> None:
    frame = repo.feature_transportability_table()
    chart = alt.Chart(frame).mark_point(filled=True, size=95).encode(
        x=alt.X("feature:N", sort=repo.primary_features, title="Frozen feature"),
        y=alt.Y("Signed AUC:Q", scale=alt.Scale(domain=[0, 1]), title="Signed univariate ROC-AUC"),
        color=alt.Color("Dataset:N", scale=alt.Scale(domain=["UCI", "BD-KDD"], range=[CHART_CLASSICAL, CHART_QUANTUM])),
        xOffset="Dataset:N",
        tooltip=["Feature:N", "Dataset:N", alt.Tooltip("Signed AUC:Q", format=".3f")],
    )
    chance = alt.Chart(pd.DataFrame({"chance": [0.5]})).mark_rule(color=TEXT_SECONDARY, strokeDash=[6, 5]).encode(y="chance:Q")
    st.altair_chart((chart + chance).properties(height=330).configure_view(stroke=None), width="stretch")


def _transportability(repo: ResultsRepository) -> None:
    with st.expander("Dataset compatibility & transportability", expanded=False):
        section_header("External transportability", "Frozen UCI models applied without retraining to the BD-KDD cross-cohort stress test.")
        st.dataframe(repo.external_transport_table(), hide_index=True, width="stretch")
        limitation_callout("Neither model demonstrated reliable better-than-random discrimination.", "Target comparability was PARTIAL. External transport failure reflected both target/cohort differences and changed feature–target relationships; therefore the experiment demonstrates transportability risk but cannot isolate pure conditional shift.")
        metric_strip([
            ("RBF SVM", "0.511", "95% CI 0.475–0.546"),
            ("QSVC", "0.525", "95% CI 0.489–0.561"),
            ("Target comparability", "PARTIAL", "UCI CKD versus BD-KDD"),
            ("External conclusion", "NOT DEMONSTRATED", "Both intervals include 0.5"),
        ])
        section_header("Feature transportability", "Features strongly discriminative inside UCI flattened toward chance-level discrimination in BD-KDD.")
        _feature_transport_chart(repo)
        st.markdown('<div class="not-equal-statement"><span>Internal feature stability</span><b>≠</b><span>External feature transportability</span></div>', unsafe_allow_html=True)
        st.dataframe(repo.feature_transportability_table()[["Feature", "Dataset", "Signed AUC", "CI low", "CI high"]], hide_index=True, width="stretch")
        section_header("Serum creatinine example", "Serum creatinine separated the UCI labels strongly but barely separated BD-KDD labels.")
        st.dataframe(repo.creatinine_median_table(), hide_index=True, width="stretch")
        st.caption("UCI medians: CKD 2.25 / non-CKD 0.90 mg/dL. BD-KDD medians: CKD 7.71 / non-CKD 7.10 mg/dL. No disease stage is inferred.")


def _final_evidence_report(repo: ResultsRepository) -> None:
    with st.expander("Q-CARE model evidence report", expanded=False):
        section_header("Q-CARE model evidence report", "A concise end-state assembled from the frozen claim registry and experiment artifacts.")
        statuses = [
            ("Internal predictive performance", "STRONG"),
            ("Feature stability", "STRONG INTERNALLY"),
            ("QSVC competitiveness", "SUPPORTED INTERNALLY"),
            ("VQC predictive strength", "WEAK"),
            ("Quantum runtime advantage", "NOT SUPPORTED"),
            ("Robustness advantage", "NOT SUPPORTED"),
            ("External transportability", "NOT DEMONSTRATED"),
            ("Dataset compatibility", "PARTIAL"),
            ("Quantum advantage", "NOT DEMONSTRATED"),
            ("Clinical validation", "NOT ESTABLISHED"),
        ]
        rows = "".join(f'<div class="final-evidence-row"><span>{html.escape(label)}</span><strong>{html.escape(status)}</strong></div>' for label, status in statuses)
        st.markdown(f'<div class="final-evidence-list">{rows}</div><div class="final-status"><span>Final status</span><strong>RESEARCH EVIDENCE ONLY</strong><b>NOT A CLINICAL DIAGNOSTIC SYSTEM</b></div>', unsafe_allow_html=True)
        errors = repo.validate_claim_registry()
        st.caption("Claim registry consistency: PASS — zero errors." if not errors else f"Claim registry requires review: {len(errors)} errors.")


def workstation_page(root: Path, repo: ResultsRepository) -> None:
    """Render the complete Q-CARE workflow on one Streamlit page."""

    service = load_live_service(str(root))
    _initialise_profile(service)
    st.markdown(
        '<header class="workstation-hero"><div class="workstation-brand">Q-CARE</div><h1>Hybrid Quantum Clinical Research Platform</h1><p>Live experimental assessment with classical and quantum evidence checks.</p></header>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="research-boundary workstation-boundary"><b>RESEARCH PROTOTYPE</b><span>Q-CARE is not a medical device and is not intended to diagnose, treat, triage, or replace clinical judgement.</span></div>', unsafe_allow_html=True)
    process_flow([
        ("Input", "Profile or CSV"), ("Data health", "Compatibility first"), ("Assessment", "Three frozen models"),
        ("Evidence", "Robustness and transfer"), ("Verdict", "Research boundary"),
    ])

    entry = st.segmented_control("Entry path", ["Enter patient readings", "Upload biomedical dataset"], default="Enter patient readings", key="workstation_entry_path", width="stretch")
    if entry == "Upload biomedical dataset":
        _dataset_entry(service)
    else:
        _patient_entry(service)

    _live_assessment(service)
    _data_health_disclosure(st.session_state.get("workstation_data_health"))
    _feature_engineering(repo)
    _three_model_benchmark(repo, service)
    _quantum_circuits(repo, service)
    _robustness(repo)
    _transportability(repo)
    _final_evidence_report(repo)
