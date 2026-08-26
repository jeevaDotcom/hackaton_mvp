"""Streamlit presentation for the separate live VQC research demonstration."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.live_vqc import READABLE_NAMES, UNITS, LiveVQCService
from src.ui_components import limitation_callout, metadata_list, page_header, research_note, section_header


WIDGET_KEYS = {
    "hemo": "live_hemo",
    "al": "live_al",
    "dm": "live_dm",
    "sg": "live_sg",
    "pcv": "live_pcv",
    "appet": "live_appet",
    "htn": "live_htn",
    "sc": "live_sc",
}


@st.cache_resource
def load_live_service(root: str) -> LiveVQCService:
    return LiveVQCService(Path(root))


def _set_profile(profile: dict[str, Any]) -> None:
    for feature, value in profile.items():
        st.session_state[WIDGET_KEYS[feature]] = value
    st.session_state.pop("live_vqc_analysis", None)


def _initialise_profile(service: LiveVQCService) -> None:
    default = service.presets["mixed"]["profile"]
    for feature, value in default.items():
        st.session_state.setdefault(WIDGET_KEYS[feature], value)


def _number_help(service: LiveVQCService, feature: str) -> str:
    low, high = service.observed_ranges[feature]
    return f"Observed UCI development-data range: {low:g}–{high:g} {UNITS[feature]}. This is not a clinical reference range."


def _profile_form(service: LiveVQCService) -> tuple[bool, dict[str, Any]]:
    with st.form("live_vqc_profile"):
        left, middle, right = st.columns(3, gap="large")
        with left:
            hemo = st.number_input(
                "Haemoglobin (g/dL)", step=0.1, format="%.1f", key=WIDGET_KEYS["hemo"], help=_number_help(service, "hemo")
            )
            sg = st.number_input(
                "Specific gravity", step=0.005, format="%.3f", key=WIDGET_KEYS["sg"], help=_number_help(service, "sg")
            )
            pcv = st.number_input(
                "Packed cell volume (%)", step=1.0, format="%.1f", key=WIDGET_KEYS["pcv"], help=_number_help(service, "pcv")
            )
        with middle:
            al = st.selectbox(
                "Albumin (dataset ordinal grade)", options=[0.0, 1.0, 2.0, 3.0, 4.0, 5.0], key=WIDGET_KEYS["al"],
                help="Observed UCI dataset coding: 0–5. This is not a clinical reference range.",
            )
            sc = st.number_input(
                "Serum creatinine (mg/dL)", step=0.1, format="%.2f", key=WIDGET_KEYS["sc"], help=_number_help(service, "sc")
            )
            appet = st.selectbox("Appetite", options=["good", "poor"], key=WIDGET_KEYS["appet"])
        with right:
            dm = st.selectbox("Diabetes mellitus", options=["no", "yes"], key=WIDGET_KEYS["dm"])
            htn = st.selectbox("Hypertension", options=["no", "yes"], key=WIDGET_KEYS["htn"])
            st.caption("Categories reproduce the UCI benchmark coding and are not clinical findings inferred by Q-CARE.")
        submitted = st.form_submit_button("Analyse with frozen VQC", type="primary", use_container_width=True)
    profile = {
        "hemo": hemo,
        "al": al,
        "dm": dm,
        "sg": sg,
        "pcv": pcv,
        "appet": appet,
        "htn": htn,
        "sc": sc,
    }
    return submitted, profile


def _result_panel(service: LiveVQCService, result: dict[str, Any]) -> None:
    score = float(result["score"])
    decision = html.escape(result["classification"])
    performance = html.escape(str(service.metrics["performance_decision"]))
    st.markdown(
        f"""<section class="live-result-plane">
        <div class="live-kicker">Experimental model classification</div>
        <div class="live-classification">{decision}</div>
        <div class="live-score-row"><div><span>VQC model score</span><strong>{score:.3f}</strong></div>
        <div class="live-score-note">Model score — not a calibrated disease probability</div></div>
        <div class="live-caution">{performance}</div>
        </section>""",
        unsafe_allow_html=True,
    )
    metadata_list(
        [
            ("Model", "Variational Quantum Classifier"),
            ("Qubits", str(service.metadata["qubits"])),
            ("Feature map", f"{service.metadata['feature_map']} · reps {service.metadata['feature_map_reps']}"),
            ("Ansatz", f"{service.metadata['ansatz']} · reps {service.metadata['ansatz_reps']} · {service.metadata['ansatz_entanglement']} entanglement"),
        ]
    )


def _factor_panel(factors: pd.DataFrame) -> None:
    maximum = max(float(factors["Absolute score change"].max()), 1e-12)
    rows: list[str] = []
    for _, row in factors.iterrows():
        width = max(2.0, 100.0 * float(row["Absolute score change"]) / maximum)
        rows.append(
            f"""<div class="influence-row"><div><b>{html.escape(str(row['Feature']))}</b>
            <span>{html.escape(str(row['Model influence']))}</span></div>
            <div class="influence-measure"><div class="influence-track"><i style="width:{width:.1f}%"></i></div>
            <small>score change {float(row['Absolute score change']):.3f}</small></div>
            <p>{html.escape(str(row['Direction']))}</p></div>"""
        )
    st.markdown(f'<div class="influence-list">{"".join(rows)}</div>', unsafe_allow_html=True)
    st.caption("Local perturbation: one entered value is moved to its UCI development-data median or modal category while all other inputs remain fixed.")


def _comparison_panel(comparison: dict[str, Any]) -> None:
    rows = "".join(
        f'<div class="model-decision-row"><b>{html.escape(item.model)}</b><span>{html.escape(item.display)}</span></div>'
        for item in comparison["decisions"]
    )
    st.markdown(
        f'<div class="agreement-line"><span>Agreement</span><strong>{html.escape(comparison["agreement"])}</strong></div>{rows}',
        unsafe_allow_html=True,
    )
    if comparison["agreement"] != "ALL AGREE":
        limitation_callout(
            "Model disagreement",
            "Model disagreement indicates uncertainty and should not be interpreted as a clinical conclusion.",
        )
    else:
        st.caption("Agreement among research models does not establish a diagnosis or clinical validity.")


def live_assessment_page(root: Path) -> None:
    service = load_live_service(str(root))
    _initialise_profile(service)
    page_header(
        "Live Research Assessment",
        "Explore how a trained variational quantum classifier responds to a clinical feature profile.",
        "Additional VQC Demonstration",
    )
    st.markdown(
        '<div class="research-boundary"><b>RESEARCH PROTOTYPE</b><span>Q-CARE is not a medical device and is not intended to diagnose, treat, triage, or replace clinical judgement.</span></div>',
        unsafe_allow_html=True,
    )

    section_header("Patient profile", "Enter the eight measurements used by the frozen UCI VQC. Dataset ranges are descriptive—not clinical reference ranges.")
    st.caption("Dataset demonstration profiles · each preset comes from an actual complete UCI development record.")
    preset_columns = st.columns(3, gap="small")
    for column, key in zip(preset_columns, ("ckd_like", "non_ckd_like", "mixed"), strict=True):
        preset = service.presets[key]
        with column:
            st.button(
                preset["label"],
                key=f"preset_{key}",
                on_click=_set_profile,
                args=(preset["profile"],),
                use_container_width=True,
                help=preset["source"],
            )

    submitted, profile = _profile_form(service)
    if submitted:
        with st.spinner("Running frozen VQC inference…"):
            st.session_state["live_vqc_analysis"] = service.analyse(profile)

    result = st.session_state.get("live_vqc_analysis")
    if result is None:
        research_note(
            "Ready for analysis",
            "Choose a dataset demonstration profile or enter a feature profile, then run the frozen VQC. No training occurs on this page.",
        )
        return

    section_header("Experimental classification", "The circuit score is an uncalibrated research-model output and must not be read as disease probability.")
    _result_panel(service, result)

    section_header("Factors influencing this model output", "Local perturbations describe model sensitivity to the entered profile; they are not causes of CKD.")
    _factor_panel(result["factors"])

    section_header("Similar benchmark records", "Nearest records are retrieved after the same frozen preprocessing used for VQC training.")
    if result["similar_records"].empty:
        research_note("No close historical benchmark matches found", "The entered profile lies beyond the stored similarity threshold for the UCI development records.")
    else:
        columns = [
            "Rank", "Similarity", "Recorded dataset class", "Serum creatinine", "Haemoglobin",
            "Albumin", "Specific gravity", "Packed cell volume", "Diabetes", "Appetite", "Hypertension",
        ]
        st.dataframe(result["similar_records"][columns], hide_index=True, width="stretch")
    st.caption("These are similar records from the research dataset. They are not clinical precedents and do not establish diagnosis.")

    section_header("Model comparison", "VQC, the existing QSVC, and the matched classical SVM classify the same profile; raw scores are not compared across model families.")
    _comparison_panel(result["comparison"])

    section_header("Clinician review checklist", "Generic review prompts only; Q-CARE does not order tests, treatment, or referral.")
    checklist = "".join(f"<li>{html.escape(item)}</li>" for item in result["checklist"])
    st.markdown(f'<ol class="review-list">{checklist}</ol>', unsafe_allow_html=True)

    section_header("Limitations", "The live workflow demonstrates inference mechanics, not clinical readiness.")
    limitation_callout(
        "Clinical review required",
        "Experimental VQC output only. The model was trained on 320 UCI development records and evaluated on a previously used 80-record holdout. Its score is uncalibrated, performance is weak, external transportability was not demonstrated, and it cannot diagnose, guide treatment, triage, or replace qualified judgement.",
    )

    with st.expander("How the quantum model works"):
        st.markdown(
            """
1. Entered readings are transformed by the frozen development-data preprocessor.
2. The eight values are encoded into quantum rotations with a ZFeatureMap.
3. A trainable RealAmplitudes circuit processes the encoded state with linear entanglement.
4. COBYLA learned the circuit parameters during the one offline training run.
5. Exact statevector class weights are converted into the experimental class score.

QSVC uses a non-trainable quantum feature map, a fidelity kernel, and a classical SVM. This VQC instead learns the parameters of a variational quantum circuit with a classical optimizer.
            """
        )
        st.code(service.circuit_text(), language="text")
