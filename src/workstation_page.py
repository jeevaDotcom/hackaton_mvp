"""Single-page Q-CARE clinical research workstation."""

from __future__ import annotations

import hashlib
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
from src.report_scanner import (
    FEATURE_NAMES as SCANNER_FEATURE_NAMES,
    FEATURE_ORDER as SCANNER_FEATURE_ORDER,
    ExtractionResult,
    ProfileConfirmationError,
    ReportValidationError,
    confirm_profile,
    extract_report,
    profile_health,
    review_defaults,
    review_table,
)
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
MODEL_LABELS = {"RBF-SVM": "RBF SVM", "QSVC": "QSVC", "VQC": "VQC"}
MODEL_COLOURS = [CHART_CLASSICAL, CHART_QUANTUM, "#8A4B4B"]
OCR_REVIEW_KEYS = {feature: f"ocr_review_{feature}" for feature in SCANNER_FEATURE_ORDER}


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
            st.markdown('<div class="input-group-label">Blood markers</div>', unsafe_allow_html=True)
            hemo = st.number_input("Haemoglobin (g/dL)", step=0.1, format="%.1f", key=WORKSTATION_KEYS["hemo"], help=_range_help(service, "hemo"))
            pcv = st.number_input("Packed cell volume (%)", step=1.0, format="%.1f", key=WORKSTATION_KEYS["pcv"], help=_range_help(service, "pcv"))
            sc = st.number_input("Serum creatinine (mg/dL)", step=0.1, format="%.2f", key=WORKSTATION_KEYS["sc"], help=_range_help(service, "sc"))
        with middle:
            st.markdown('<div class="input-group-label">Urine markers</div>', unsafe_allow_html=True)
            al = st.selectbox("Albumin (dataset ordinal grade)", [0.0, 1.0, 2.0, 3.0, 4.0, 5.0], key=WORKSTATION_KEYS["al"], help="Observed UCI coding: 0–5; not a clinical reference range.")
            sg = st.number_input("Specific gravity", step=0.005, format="%.3f", key=WORKSTATION_KEYS["sg"], help=_range_help(service, "sg"))
        with right:
            st.markdown('<div class="input-group-label">Clinical factors</div>', unsafe_allow_html=True)
            dm = st.selectbox("Diabetes mellitus", ["no", "yes"], key=WORKSTATION_KEYS["dm"], help="Recorded yes/no category from the UCI benchmark; Q-CARE does not infer diabetes.")
            htn = st.selectbox("Hypertension", ["no", "yes"], key=WORKSTATION_KEYS["htn"], help="Recorded yes/no category from the UCI benchmark; Q-CARE does not infer hypertension.")
            appet = st.selectbox("Appetite", ["good", "poor"], key=WORKSTATION_KEYS["appet"], help="Recorded good/poor benchmark category; not a clinical assessment.")
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


def _store_ocr_extraction(result: ExtractionResult, fingerprint: str) -> None:
    """Reset confirmation whenever the source document changes."""

    st.session_state["ocr_extraction"] = result
    st.session_state["ocr_source_fingerprint"] = fingerprint
    st.session_state.pop("ocr_confirmed_profile", None)
    st.session_state.pop("ocr_profile_health", None)
    st.session_state.pop("workstation_analysis", None)
    defaults = review_defaults(result)
    for feature, value in defaults.items():
        distinct = {
            str(item.normalized_value)
            for item in result.candidates.get(feature, [])
            if item.normalized_value is not None
        }
        if feature in {"dm", "htn", "appet", "al"} or len(distinct) > 1:
            st.session_state[OCR_REVIEW_KEYS[feature]] = value
        else:
            st.session_state[OCR_REVIEW_KEYS[feature]] = "" if value is None else str(value)


def _extract_source(data: bytes, filename: str) -> None:
    fingerprint = hashlib.sha256(data).hexdigest()
    if st.session_state.get("ocr_source_fingerprint") == fingerprint:
        return
    try:
        with st.spinner("Extracting only the eight Q-CARE research features…"):
            result = extract_report(data, filename)
    except ReportValidationError as error:
        st.error(str(error))
        return
    _store_ocr_extraction(result, fingerprint)


def _render_source_evidence(result: ExtractionResult) -> None:
    section_header("Source evidence", "Every suggestion remains traceable to its detected label, source line, page, and extraction method.")
    for feature in SCANNER_FEATURE_ORDER:
        candidates = result.candidates.get(feature, [])
        if not candidates:
            continue
        with st.expander(f"Show source · {SCANNER_FEATURE_NAMES[feature]}", expanded=False):
            for index, candidate in enumerate(candidates, start=1):
                if len(candidates) > 1:
                    st.markdown(f"**Candidate {index}**")
                st.markdown(
                    f'<div class="ocr-source"><b>{html.escape(candidate.detected_label)}</b>'
                    f'<strong>{html.escape(candidate.raw_value)} {html.escape(candidate.original_unit)}</strong>'
                    f'<span>Page {candidate.page} · {html.escape(candidate.method)} · {html.escape(candidate.confidence)}</span>'
                    f'<p>“{html.escape(candidate.source)}”</p></div>',
                    unsafe_allow_html=True,
                )
                if candidate.reason:
                    st.caption(candidate.reason)


def _ocr_review_form(result: ExtractionResult) -> None:
    defaults = review_defaults(result)
    automatically_ready = [feature for feature in SCANNER_FEATURE_ORDER if defaults[feature] is not None]
    needs_completion = [feature for feature in SCANNER_FEATURE_ORDER if defaults[feature] is None]
    section_header("Verify extracted profile", "OCR suggestions are editable. Models remain blocked until a researcher confirms all eight dataset-compatible values.")
    if needs_completion:
        st.markdown(
            '<div class="manual-completion"><b>Manual completion required</b><span>'
            + html.escape(", ".join(SCANNER_FEATURE_NAMES[feature] for feature in needs_completion))
            + "</span></div>",
            unsafe_allow_html=True,
        )

    values: dict[str, Any] = {}
    with st.form("ocr_profile_review_form"):
        for title, features in (
            ("Extracted values · review or correct", automatically_ready),
            ("Missing or unresolved · complete manually", needs_completion),
        ):
            if not features:
                continue
            st.markdown(f'<div class="input-group-label">{html.escape(title)}</div>', unsafe_allow_html=True)
            columns = st.columns(min(3, len(features)), gap="large")
            for index, feature in enumerate(features):
                with columns[index % len(columns)]:
                    options = result.candidates.get(feature, [])
                    distinct = {str(item.normalized_value) for item in options if item.normalized_value is not None}
                    if len(distinct) > 1:
                        choices: list[Any] = [None] + [item.normalized_value for item in options if item.normalized_value is not None]
                        values[feature] = st.selectbox(
                            f"{SCANNER_FEATURE_NAMES[feature]} · select source value",
                            choices,
                            key=OCR_REVIEW_KEYS[feature],
                            format_func=lambda value: "Select…" if value is None else str(value),
                        )
                        st.caption("Multiple values detected; select one after reviewing page provenance.")
                    elif feature == "al":
                        values[feature] = st.selectbox(
                            "Albumin · dataset ordinal grade",
                            [None, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
                            key=OCR_REVIEW_KEYS[feature],
                            format_func=lambda value: "Select…" if value is None else f"{int(value)}",
                            help="Select only after verifying a dataset-compatible urinary ordinal grade. Serum albumin is not mapped automatically.",
                        )
                    elif feature in {"dm", "htn"}:
                        values[feature] = st.selectbox(
                            SCANNER_FEATURE_NAMES[feature], [None, "no", "yes"], key=OCR_REVIEW_KEYS[feature],
                            format_func=lambda value: "Select…" if value is None else str(value).title(),
                        )
                    elif feature == "appet":
                        values[feature] = st.selectbox(
                            "Appetite · dataset category", [None, "good", "poor"], key=OCR_REVIEW_KEYS[feature],
                            format_func=lambda value: "Select…" if value is None else str(value).title(),
                        )
                    else:
                        values[feature] = st.text_input(
                            f"{SCANNER_FEATURE_NAMES[feature]} · {UNITS[feature]}", key=OCR_REVIEW_KEYS[feature]
                        )
        st.caption("By confirming, the researcher asserts that values and units were checked against the source report. This is not clinical validation.")
        confirmed = st.form_submit_button("CONFIRM FEATURE PROFILE", type="primary", use_container_width=True)

    if confirmed:
        try:
            profile = confirm_profile(values)
        except ProfileConfirmationError as error:
            st.error(str(error))
        else:
            _set_profile(profile)
            st.session_state["ocr_confirmed_profile"] = profile
            st.success("Feature profile confirmed. Frozen model evaluation is now available as a separate action.")


def _ocr_profile_health(service: LiveVQCService) -> None:
    profile = st.session_state.get("ocr_confirmed_profile")
    if profile is None:
        return
    health = profile_health(profile, service.observed_ranges)
    st.session_state["ocr_profile_health"] = health
    section_header("Confirmed profile data health", "Compatibility checks describe the frozen model input contract, not medical normality.")
    metric_strip([
        ("Feature completeness", health["FEATURE COMPLETENESS"], "Required frozen inputs"),
        ("Unit review", health["UNIT REVIEW"], "Researcher-confirmed units"),
        ("Development-range check", health["DEVELOPMENT-RANGE CHECK"], "Descriptive UCI ranges"),
        ("Model input status", health["MODEL INPUT STATUS"], "Structure only"),
    ])
    if health["outside_features"]:
        limitation_callout(
            "Development-distribution warning",
            f'Outside training range: {health["outside_features"]}. This is a model-input compatibility warning, not medical advice.',
        )
    if st.button("RUN EXPERIMENT", type="primary", key="ocr_run_experiment", use_container_width=True):
        with st.spinner("Running the three frozen, crash-safe model paths…"):
            st.session_state["workstation_analysis"] = _run_worker_safe_analysis(service, profile)


def _report_scanner_entry(root: Path, service: LiveVQCService) -> None:
    section_header("Scan report", "AI-assisted report extraction identifies only Q-CARE inputs; a researcher must verify every value before model evaluation.")
    st.markdown(
        '<div class="scanner-flow"><span>REPORT UPLOAD</span><i>↓</i><span>FIELD MAPPING</span><i>↓</i><span>RESEARCHER REVIEW</span><i>↓</i><span>CONFIRM</span><i>↓</i><span>RUN Q-CARE</span></div>',
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "Drop a PDF or report image here",
        type=["pdf", "png", "jpg", "jpeg", "webp"],
        key="ocr_report_upload",
        help="PDF, PNG, JPG/JPEG, or WEBP; maximum 10 MB; up to 8 PDF pages.",
    )
    sample_col, button_col = st.columns([1.4, 1], gap="small")
    with sample_col:
        sample_name = st.selectbox(
            "Offline demo document",
            ["Clean digital laboratory PDF", "Photo-style report image"],
            key="ocr_sample_choice",
        )
    with button_col:
        st.markdown('<div class="sample-button-spacer"></div>', unsafe_allow_html=True)
        load_sample = st.button("TRY SAMPLE REPORT", key="ocr_sample_report", use_container_width=True)
    if load_sample:
        sample_path = root / "artifacts/ocr_demo" / ("sample_digital_report.pdf" if sample_name.startswith("Clean") else "sample_photo_report.png")
        if sample_path.exists():
            _extract_source(sample_path.read_bytes(), sample_path.name)
        else:
            st.error("The bundled sample report is missing. Manual entry remains available.")
    elif uploaded is not None:
        _extract_source(uploaded.getvalue(), uploaded.name)

    result = st.session_state.get("ocr_extraction")
    if result is None:
        research_note("Awaiting report", "Use the bundled fictional sample or upload a supported local report. No document is sent to an external service.")
        return
    for warning in result.warnings:
        st.warning(warning)
    st.markdown(
        f'<div class="extraction-status"><span>EXTRACTING RESEARCH FEATURES</span><strong>{result.detected_count} of 8 values detected</strong><small>{html.escape(result.method)} · {result.page_count} page(s)</small></div>',
        unsafe_allow_html=True,
    )
    section_header("AI / OCR extracted values", "Real deterministic extraction results; unresolved or conflicting fields are never filled silently.")
    st.dataframe(pd.DataFrame(review_table(result, service.observed_ranges)), hide_index=True, width="stretch")
    _render_source_evidence(result)
    _ocr_review_form(result)
    _ocr_profile_health(service)


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


def _model_table(result: dict[str, Any], model_mode: str, selected_model: str) -> tuple[pd.DataFrame, str]:
    decisions = {item.model: item for item in result["comparison"]["decisions"]}
    rows = [
        ("RBF SVM", decisions["RBF SVM"], "Classical", "Strong benchmark"),
        ("QSVC", decisions["QSVC"], "Quantum kernel", "Competitive internally"),
        ("VQC", decisions["VQC"], "Variational QML", "Weak experimental model"),
    ]
    if model_mode == "Single Model":
        expected = MODEL_LABELS[selected_model]
        rows = [row for row in rows if row[0] == expected]
    table = pd.DataFrame([
        {"Model": name, "Prediction": "CKD-like" if item.predicted_class else "non-CKD-like", "Model type": model_type, "Evidence status": status}
        for name, item, model_type, status in rows
    ])
    agreement = "3 OF 3 AGREE" if result["comparison"]["agreement"] == "ALL AGREE" else "2 OF 3 AGREE"
    return table, agreement


def _factor_panel(factors: pd.DataFrame) -> None:
    frame = factors.copy()
    bars = alt.Chart(frame).mark_bar(color=CHART_QUANTUM, cornerRadiusEnd=5, height=22).encode(
        x=alt.X("Absolute score change:Q", title="Absolute VQC score change"),
        y=alt.Y("Feature:N", sort="-x", title=None),
        tooltip=["Feature:N", "Model influence:N", "Direction:N", alt.Tooltip("Absolute score change:Q", format=".4f")],
    )
    labels = alt.Chart(frame).mark_text(align="left", dx=6, color=TEXT_SECONDARY, fontSize=12).encode(
        x="Absolute score change:Q",
        y=alt.Y("Feature:N", sort="-x"),
        text=alt.Text("Absolute score change:Q", format=".3f"),
    )
    chart = (bars + labels).properties(height=max(230, len(frame) * 42)).configure_view(stroke=None).configure_axis(
        domain=False, gridColor="#E1E1DC", labelColor=TEXT_SECONDARY, titleColor=TEXT_SECONDARY
    )
    st.altair_chart(chart, width="stretch")
    chart_caption(
        "These values indicate model sensitivity to each input, not medical causation. One value is moved to the UCI development median or mode while all others remain fixed.",
        "Frozen VQC local perturbation",
    )


def _performance_visual(repo: ResultsRepository, service: LiveVQCService) -> None:
    section_header("Classical vs quantum performance", "Frozen internal results at the same eight-feature input budget; protocol differences are shown explicitly.")
    svm = repo.replay("clinical", 8, "RBF SVM")
    qsvc = repo.replay("clinical", 8, "QSVC")
    vqc = service.metrics["vqc"]
    values = {
        "RBF SVM": (svm.sensitivity, svm.specificity, svm.f1, svm.roc_auc, "Repeated development CV"),
        "QSVC": (qsvc.sensitivity, qsvc.specificity, qsvc.f1, qsvc.roc_auc, "Repeated development CV"),
        "VQC": (vqc["sensitivity"], vqc["specificity"], vqc["f1"], vqc["roc_auc"], "Existing 80-record holdout"),
    }
    rows = []
    for model, (*scores, protocol) in values.items():
        for metric, value in zip(("Sensitivity", "Specificity", "F1", "ROC-AUC"), scores, strict=True):
            rows.append({"Model": model, "Metric": metric, "Value": float(value), "Protocol": protocol})
    frame = pd.DataFrame(rows)
    encoding = {
        "x": alt.X("Metric:N", sort=["Sensitivity", "Specificity", "F1", "ROC-AUC"], title=None),
        "xOffset": alt.XOffset("Model:N", sort=["RBF SVM", "QSVC", "VQC"]),
        "y": alt.Y("Value:Q", scale=alt.Scale(domain=[0, 1.03]), title="Score"),
        "color": alt.Color("Model:N", scale=alt.Scale(domain=["RBF SVM", "QSVC", "VQC"], range=MODEL_COLOURS), legend=alt.Legend(orient="top")),
    }
    bars = alt.Chart(frame).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        **encoding,
        tooltip=["Model:N", "Metric:N", alt.Tooltip("Value:Q", format=".3f"), "Protocol:N"],
    )
    labels = alt.Chart(frame).mark_text(dy=-8, fontSize=11, color=TEXT_SECONDARY).encode(
        **encoding,
        text=alt.Text("Value:Q", format=".3f"),
    )
    chart = (bars + labels).properties(height=340).configure_view(stroke=None).configure_axis(
        domain=False, gridColor="#E1E1DC", labelColor=TEXT_SECONDARY, titleColor=TEXT_SECONDARY
    )
    st.altair_chart(chart, width="stretch")
    chart_caption(
        "Research finding: QSVC remained internally competitive, while VQC was weaker in this experiment. VQC holdout metrics and repeated-CV estimates are not interchangeable.",
        "Frozen Phase 2 and live VQC artifacts",
    )
    st.markdown('<div class="vqc-honesty"><b>WEAK — DISPLAY WITH CAUTION</b><span>The VQC is retained as a transparent trainable quantum-model demonstration, not as the strongest predictor.</span></div>', unsafe_allow_html=True)


def _runtime_visual(repo: ResultsRepository, service: LiveVQCService) -> None:
    section_header("Computational cost", "Lower is better. Training/runtime measurements are separated from interactive inference.")
    svm = repo.replay("clinical", 8, "RBF SVM")
    qsvc = repo.replay("clinical", 8, "QSVC")
    ratio = repo.runtime_ratio(8)
    frame = pd.DataFrame([
        {"Model": "RBF SVM", "Relative cost": 1.0, "Label": "1×", "Measured training wall time": svm.runtime_seconds},
        {"Model": "QSVC", "Relative cost": ratio, "Label": f"{ratio:.0f}×", "Measured training wall time": qsvc.runtime_seconds},
    ])
    bars = alt.Chart(frame).mark_bar(cornerRadiusEnd=5, height=30).encode(
        x=alt.X("Relative cost:Q", scale=alt.Scale(type="log", domain=[1, 700]), title="Relative repeated-CV training wall time (log scale; RBF SVM = 1×)"),
        y=alt.Y("Model:N", sort=["RBF SVM", "QSVC"], title=None),
        color=alt.Color("Model:N", scale=alt.Scale(domain=["RBF SVM", "QSVC"], range=[CHART_CLASSICAL, CHART_QUANTUM]), legend=None),
        tooltip=["Model:N", "Label:N", alt.Tooltip("Measured training wall time:Q", format=".6f", title="Mean wall time (s)")],
    )
    labels = alt.Chart(frame).mark_text(align="left", dx=7, fontSize=13, fontWeight=600).encode(
        x="Relative cost:Q", y=alt.Y("Model:N", sort=["RBF SVM", "QSVC"]), text="Label:N"
    )
    chart = (bars + labels).properties(height=145).configure_view(stroke=None).configure_axis(
        domain=False, gridColor="#E1E1DC", labelColor=TEXT_SECONDARY, titleColor=TEXT_SECONDARY
    )
    st.altair_chart(chart, width="stretch")
    chart_caption(
        "QSVC achieved competitive internal performance but required substantially more computation in our local exact-statevector experiment.",
        "Frozen matched eight-feature development CV",
    )
    metric_strip([
        ("VQC training time", f'{service.metrics["training_runtime_seconds"]:.2f} s', "One existing frozen training run"),
        ("COBYLA evaluations", str(service.metadata["optimizer_evaluations"]), "Training objective evaluations"),
        ("Live VQC inference", "Separate", "NumPy statevector; no retraining"),
        ("Runtime claim", "NOT SUPPORTED", "No quantum speed advantage"),
    ])


def _live_assessment(
    service: LiveVQCService,
    repo: ResultsRepository,
    model_mode: str,
    selected_model: str,
    awaiting_copy: str = "Enter a profile above and select ANALYSE PROFILE. No training occurs during this interaction.",
) -> None:
    section_header("Model consensus", "The same entered profile is evaluated through frozen, crash-safe inference paths.")
    result = st.session_state.get("workstation_analysis")
    if result is None:
        research_note("Awaiting profile analysis", awaiting_copy)
        st.markdown('<div class="agreement-line"><span>Model agreement</span><strong>AWAITING PROFILE</strong></div>', unsafe_allow_html=True)
    else:
        table, agreement = _model_table(result, model_mode, selected_model)
        rows = "".join(
            f'<div class="consensus-row"><b>{html.escape(str(row.Model))}</b><span>{html.escape(str(row.Prediction))}</span><small>{html.escape(str(row["Evidence status"]))}</small></div>'
            for _, row in table.iterrows()
        )
        st.markdown(f'<div class="consensus-table">{rows}</div>', unsafe_allow_html=True)
        if model_mode == "Compare All":
            st.markdown(f'<div class="agreement-line"><span>Model agreement</span><strong>{agreement}</strong></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="agreement-line"><span>Display mode</span><strong>SINGLE MODEL</strong></div>', unsafe_allow_html=True)
            st.caption("Switch to Compare All to view cross-model agreement for the same entered profile.")
        if model_mode == "Compare All" and agreement != "3 OF 3 AGREE":
            limitation_callout("Model disagreement", "Models do not completely agree. Review model-specific evidence and input quality before interpreting this research output. It must not be interpreted as diagnosis.")
        else:
            st.caption("Agreement among research models does not establish diagnosis or clinical validity.")

    _performance_visual(repo, service)
    _runtime_visual(repo, service)

    if result is None:
        return
    if model_mode == "Compare All" or selected_model == "VQC":
        st.markdown(f'<div class="workstation-score"><span>VQC research model score</span><strong>{float(result["score"]):.3f}</strong><small>Not a calibrated disease probability</small></div>', unsafe_allow_html=True)
    section_header("What influenced this model output?", "Existing VQC local perturbation evidence ranked for the current entered profile.")
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


def _feature_efficiency(repo: ResultsRepository) -> None:
    section_header("Can 8 features retain most of the 24-feature performance?", "Matched RBF-SVM repeated development CV; feature selection remained inside the leakage-safe workflow.")
    st.markdown(
        '<div class="feature-proof-flow"><div><strong>24</strong><span>original predictors</span></div><i>↓</i><div><b>Leakage-safe RFE</b><span>selection inside development folds</span></div><i>↓</i><div><strong>8</strong><span>stable UCI-development features</span></div></div>',
        unsafe_allow_html=True,
    )
    feature_chips([(feature, FEATURE_NAMES[feature]) for feature in repo.primary_features])
    frame = repo.feature_efficiency_table()
    encoding = {
        "x": alt.X("Metric:N", sort=["Sensitivity", "Specificity", "F1", "ROC-AUC"], title=None),
        "xOffset": alt.XOffset("Representation:N", sort=["24 features", "8 features"]),
        "y": alt.Y("Value:Q", scale=alt.Scale(domain=[0, 1.02]), title="Repeated-CV score"),
        "color": alt.Color("Representation:N", scale=alt.Scale(domain=["24 features", "8 features"], range=[CHART_CLASSICAL, CHART_QUANTUM]), legend=alt.Legend(orient="top")),
    }
    bars = alt.Chart(frame).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        **encoding, tooltip=["Representation:N", "Metric:N", alt.Tooltip("Value:Q", format=".4f")]
    )
    labels = alt.Chart(frame).mark_text(dy=-8, fontSize=11, color=TEXT_SECONDARY).encode(
        **encoding, text=alt.Text("Value:Q", format=".3f")
    )
    st.altair_chart(
        (bars + labels).properties(height=310).configure_view(stroke=None).configure_axis(
            domain=False, gridColor="#E1E1DC", labelColor=TEXT_SECONDARY, titleColor=TEXT_SECONDARY
        ),
        width="stretch",
    )
    pivot = frame.pivot(index="Metric", columns="Representation", values="Value")
    retention = 100 * pivot["8 features"] / pivot["24 features"]
    metric_strip([
        (metric, f"{retention[metric]:.1f}%", "8-feature / 24-feature score")
        for metric in ("Sensitivity", "Specificity", "F1", "ROC-AUC")
    ])
    research_note("Feature-efficiency finding", "The 8-feature representation retained most of the tested internal predictive performance with a smaller information budget. These descriptive ratios do not establish equivalence.")


def _model_explainers() -> None:
    section_header("How the models work", "Three compact explanations for the classical baseline and two distinct quantum approaches.")
    cards = [
        (
            "RBF-SVM",
            "Classical nonlinear classifier.",
            "Uses an RBF kernel to measure similarity and form a decision boundary.",
            "Strong classical baseline.",
            "Strongest internal benchmark.",
        ),
        (
            "QSVC",
            "Quantum-kernel support vector classifier.",
            "Encodes eight features into quantum states and computes state similarity using a fidelity kernel.",
            "Most direct quantum counterpart to the classical SVM.",
            "Internally competitive but substantially slower.",
        ),
        (
            "VQC",
            "Trainable variational quantum classifier.",
            "ZFeatureMap encodes inputs; RealAmplitudes supplies trainable parameters; COBYLA optimises them.",
            "Demonstrates a genuinely trainable quantum model.",
            "Weak predictive performance; retained for transparent research comparison.",
        ),
    ]
    body = "".join(
        f'<details class="model-explainer"><summary><b>{html.escape(name)}</b><span>{html.escape(what)}</span></summary>'
        f'<div><strong>How?</strong><p>{html.escape(how)}</p><strong>Why included?</strong><p>{html.escape(why)}</p><strong>Our result</strong><p>{html.escape(result)}</p></div></details>'
        for name, what, how, why, result in cards
    )
    st.markdown(f'<div class="model-explainer-grid">{body}</div>', unsafe_allow_html=True)


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
        section_header("Quantum proof", "Validated architecture, stored fidelity matrix, real circuits, and the frozen VQC optimisation trace.")
        st.markdown(
            '<div class="quantum-proof-grid">'
            '<article><b>QSVC</b><p>8 inputs → ZFeatureMap → 8-qubit state → fidelity kernel → QSVC</p><span>8 qubits · reps 1 · no entanglement · C 0.5</span></article>'
            f'<article><b>VQC</b><p>8 features → ZFeatureMap → RealAmplitudes → measurement → COBYLA → output</p><span>8 qubits · linear entanglement · {service.metadata["optimizer_evaluations"]} evaluations · {service.metrics["training_runtime_seconds"]:.2f} s training</span></article>'
            '</div>',
            unsafe_allow_html=True,
        )
        kernel = np.load(repo.root / "artifacts/quantum/kernels/clinical_8_z_reps1.npz")["kernel"]
        preview = kernel[::2, ::2]
        heatmap = pd.DataFrame({
            "Row": np.repeat(np.arange(preview.shape[0]), preview.shape[1]),
            "Column": np.tile(np.arange(preview.shape[1]), preview.shape[0]),
            "Fidelity": preview.ravel(),
        })
        kernel_chart = alt.Chart(heatmap).mark_rect().encode(
            x=alt.X("Column:O", axis=None),
            y=alt.Y("Row:O", axis=None, sort="descending"),
            color=alt.Color("Fidelity:Q", scale=alt.Scale(domain=[0, 1], range=["#F0EFEA", CHART_QUANTUM]), title="Fidelity"),
            tooltip=["Row:O", "Column:O", alt.Tooltip("Fidelity:Q", format=".3f")],
        ).properties(height=320).configure_view(stroke=None)
        trace = pd.read_csv(service.artifact_dir / "training_trace.csv")
        trace_chart = alt.Chart(trace).mark_line(point=alt.OverlayMarkDef(filled=True, size=42), color=CHART_QUANTUM, strokeWidth=2.5).encode(
            x=alt.X("evaluation:Q", title="COBYLA objective evaluation"),
            y=alt.Y("objective:Q", scale=alt.Scale(zero=False), title="Training objective"),
            tooltip=["evaluation:Q", alt.Tooltip("objective:Q", format=".4f")],
        ).properties(height=320).configure_view(stroke=None).configure_axis(
            domain=False, gridColor="#E1E1DC", labelColor=TEXT_SECONDARY, titleColor=TEXT_SECONDARY
        )
        kernel_column, trace_column = st.columns(2, gap="large")
        with kernel_column:
            section_header("Quantum similarity matrix", "Sampled view of the stored 80 × 80 exact-statevector fidelity kernel.")
            st.altair_chart(kernel_chart, width="stretch")
        with trace_column:
            section_header("VQC training trace", "Stored optimisation history; no training runs in this app.")
            st.altair_chart(trace_chart, width="stretch")
        section_header("QSVC circuit", "Validated non-trainable ZFeatureMap circuit text from the frozen artifact.")
        st.code(repo.circuit_text(), language="text")
        section_header("VQC circuit", "Validated trainable ZFeatureMap + RealAmplitudes circuit text from the frozen artifact.")
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
        headline = repo.headline_values()
        transport = pd.DataFrame([
            {"Model": "RBF SVM", "Cohort": "Internal UCI", "ROC-AUC": repo.reference_metric(8, "classical_rbf_svm", "roc_auc")},
            {"Model": "RBF SVM", "Cohort": "BD-KDD stress test", "ROC-AUC": headline["external_classical_roc_auc"]},
            {"Model": "QSVC", "Cohort": "Internal UCI", "ROC-AUC": repo.reference_metric(8, "qsvc", "roc_auc")},
            {"Model": "QSVC", "Cohort": "BD-KDD stress test", "ROC-AUC": headline["external_roc_auc"]},
        ])
        lines = alt.Chart(transport).mark_line(point=alt.OverlayMarkDef(filled=True, size=90), strokeWidth=3).encode(
            x=alt.X("Cohort:N", sort=["Internal UCI", "BD-KDD stress test"], title=None),
            y=alt.Y("ROC-AUC:Q", scale=alt.Scale(domain=[0.45, 1.02]), title="ROC-AUC"),
            color=alt.Color("Model:N", scale=alt.Scale(domain=["RBF SVM", "QSVC"], range=[CHART_CLASSICAL, CHART_QUANTUM]), legend=alt.Legend(orient="top")),
            tooltip=["Model:N", "Cohort:N", alt.Tooltip("ROC-AUC:Q", format=".3f")],
        )
        chance = alt.Chart(pd.DataFrame({"chance": [0.5]})).mark_rule(color=TEXT_SECONDARY, strokeDash=[6, 5]).encode(y="chance:Q")
        st.altair_chart(
            (lines + chance).properties(height=330).configure_view(stroke=None).configure_axis(
                domain=False, gridColor="#E1E1DC", labelColor=TEXT_SECONDARY, titleColor=TEXT_SECONDARY
            ),
            width="stretch",
        )
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
    with st.expander("Q-CARE model evidence report", expanded=True):
        section_header("Q-CARE model evidence report", "A concise end-state assembled from the frozen claim registry and experiment artifacts.")
        statuses = [
            ("Internal SVM performance", "STRONG"),
            ("QSVC internal competitiveness", "SUPPORTED"),
            ("VQC performance", "WEAK / EXPERIMENTAL"),
            ("Feature efficiency", "SUPPORTED INTERNALLY"),
            ("Runtime advantage", "NOT SUPPORTED"),
            ("Robustness advantage", "NOT SUPPORTED"),
            ("External transportability", "NOT DEMONSTRATED"),
            ("Dataset comparability", "PARTIAL"),
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
        '<header class="workstation-hero"><div class="workstation-brand">Q-CARE</div><h1>Hybrid Quantum-Classical Healthcare Research Platform</h1><p>Compare classical and quantum models on the same biomedical inputs — with performance, explainability, runtime and evidence checks.</p><div class="hero-badges"><span>CKD</span><span>8 Features</span><span>3 Models</span><span>Research Prototype</span></div></header>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="research-boundary workstation-boundary"><b>RESEARCH PROTOTYPE</b><span>Q-CARE is not a medical device and is not intended to diagnose, treat, triage, or replace clinical judgement.</span></div>', unsafe_allow_html=True)
    process_flow([
        ("INPUT", "Profile, report or CSV"), ("PREDICT", "Three frozen models"), ("EXPLAIN", "Local influence"),
        ("COMPARE", "Performance and cost"), ("TRUST", "Evidence boundary"),
    ])

    section_header("New research experiment", "Choose a manual profile, a human-verified report scan, or a dataset health check.")
    entry_column, mode_column = st.columns([1.25, 1], gap="large")
    with entry_column:
        entry = st.segmented_control(
            "Entry path",
            ["Enter manually", "Scan report", "Upload biomedical dataset"],
            default="Enter manually",
            key="workstation_entry_path",
            width="stretch",
        )
    with mode_column:
        model_mode = st.segmented_control("MODEL MODE", ["Compare All", "Single Model"], default="Compare All", key="workstation_model_mode", width="stretch")
        selected_model = "VQC"
        if model_mode == "Single Model":
            selected_model = st.selectbox("Frozen model", list(MODEL_LABELS), key="workstation_selected_model")
    if entry == "Upload biomedical dataset":
        _dataset_entry(service)
    elif entry == "Scan report":
        if "ocr_confirmed_profile" not in st.session_state:
            st.session_state.pop("workstation_analysis", None)
        _report_scanner_entry(root, service)
    else:
        _patient_entry(service)

    awaiting = (
        "Extract, review, and confirm all eight report-derived values, then select RUN EXPERIMENT. OCR never runs a model automatically."
        if entry == "Scan report" else
        "Enter a profile above and select ANALYSE PROFILE. No training occurs during this interaction."
    )
    _live_assessment(service, repo, model_mode, selected_model, awaiting)
    _feature_efficiency(repo)
    _model_explainers()
    _data_health_disclosure(st.session_state.get("workstation_data_health"))
    _feature_engineering(repo)
    _three_model_benchmark(repo, service)
    _quantum_circuits(repo, service)
    _robustness(repo)
    _transportability(repo)
    _final_evidence_report(repo)
