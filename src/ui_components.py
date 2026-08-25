"""Reusable presentation primitives for the Q-CARE research workspace."""

from __future__ import annotations

import html
from collections.abc import Iterable, Sequence

import streamlit as st


def _escape(value: object) -> str:
    return html.escape(str(value))


def page_header(title: str, purpose: str, context: str | None = None) -> None:
    context_html = f'<div class="page-context">{_escape(context)}</div>' if context else ""
    st.markdown(
        f'<header class="page-header">{context_html}<h1>{_escape(title)}</h1><p class="page-purpose">{_escape(purpose)}</p></header>',
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str | None = None) -> None:
    subtitle_html = f'<p>{_escape(subtitle)}</p>' if subtitle else ""
    st.markdown(f'<section class="section-header"><h2>{_escape(title)}</h2>{subtitle_html}</section>', unsafe_allow_html=True)


def hero_statement(text: str) -> None:
    st.markdown(f'<div class="hero-statement">{_escape(text)}</div>', unsafe_allow_html=True)


def hero_metric(label: str, value: str, context: str) -> None:
    st.markdown(
        f'<div class="hero-metric"><div class="hero-metric-label">{_escape(label)}</div><div class="hero-metric-value">{_escape(value)}</div><div class="hero-metric-context">{_escape(context)}</div></div>',
        unsafe_allow_html=True,
    )


def comparison_metric(
    left_label: str,
    left_value: str,
    left_detail: str,
    right_label: str,
    right_value: str,
    right_detail: str,
    caption: str,
) -> None:
    st.markdown(
        f"""<div class="comparison-hero">
        <div class="comparison-side"><div class="comparison-label">{_escape(left_label)}</div><div class="comparison-value">{_escape(left_value)}</div><div class="comparison-detail">{_escape(left_detail)}</div></div>
        <div class="comparison-arrow" aria-hidden="true">→</div>
        <div class="comparison-side"><div class="comparison-label">{_escape(right_label)}</div><div class="comparison-value">{_escape(right_value)}</div><div class="comparison-detail">{_escape(right_detail)}</div></div>
        </div><div class="comparison-caption">{_escape(caption)}</div>""",
        unsafe_allow_html=True,
    )


def metric_strip(items: Sequence[tuple[str, str, str]]) -> None:
    body = "".join(
        f'<div class="metric-strip-item"><div class="metric-strip-label">{_escape(label)}</div><div class="metric-strip-value">{_escape(value)}</div><div class="metric-strip-note">{_escape(note)}</div></div>'
        for label, value, note in items
    )
    st.markdown(f'<div class="metric-strip">{body}</div>', unsafe_allow_html=True)


def verdict_badge(verdict: str) -> str:
    normalized = verdict.upper()
    category = {
        "SUPPORTED": "supported",
        "SUPPORTED INTERNALLY": "supported",
        "MIXED": "mixed",
        "NOT SUPPORTED": "negative",
        "CLASSICAL STRONGER": "negative",
        "NO QSVC ADVANTAGE": "negative",
        "TRANSPORTABILITY FAILURE": "negative",
        "NEUTRAL": "neutral",
        "INCONCLUSIVE": "inconclusive",
        "REFERENCE": "neutral",
    }.get(normalized, "neutral")
    return f'<span class="verdict {category}">{_escape(normalized)}</span>'


def evidence_row(dimension: str, classical: str, quantum: str, verdict: str) -> str:
    return (
        '<div class="evidence-row">'
        f'<div class="evidence-dimension">{_escape(dimension)}</div>'
        f'<div class="evidence-copy evidence-classical">{_escape(classical)}</div>'
        f'<div class="evidence-copy evidence-quantum">{_escape(quantum)}</div>'
        f'<div>{verdict_badge(verdict)}</div>'
        '</div>'
    )


def evidence_table(rows: Iterable[tuple[str, str, str, str]]) -> None:
    header = '<div class="evidence-row header"><div>Evidence dimension</div><div>Classical</div><div>Quantum</div><div>Verdict</div></div>'
    body = "".join(evidence_row(*row) for row in rows)
    st.markdown(f'<div class="evidence-table">{header}{body}</div>', unsafe_allow_html=True)


def research_note(title: str, body: str) -> None:
    st.markdown(f'<div class="research-note"><b>{_escape(title)}</b><span>{_escape(body)}</span></div>', unsafe_allow_html=True)


def limitation_callout(title: str, body: str) -> None:
    st.markdown(f'<div class="limitation-callout"><b>{_escape(title)}</b><span>{_escape(body)}</span></div>', unsafe_allow_html=True)


def chart_caption(text: str, source: str | None = None) -> None:
    source_text = f' · Source: {_escape(source)}' if source else ""
    st.markdown(f'<div class="chart-caption">{_escape(text)}{source_text}</div>', unsafe_allow_html=True)


def process_flow(steps: Sequence[tuple[str, str]]) -> None:
    body = "".join(f'<div class="process-step"><strong>{_escape(title)}</strong>{_escape(detail)}</div>' for title, detail in steps)
    st.markdown(f'<div class="process-flow">{body}</div>', unsafe_allow_html=True)


def metadata_list(items: Sequence[tuple[str, str]]) -> None:
    body = "".join(f'<div class="metadata-row"><b>{_escape(label)}</b><span>{value}</span></div>' for label, value in items)
    st.markdown(f'<div class="metadata-list">{body}</div>', unsafe_allow_html=True)


def feature_chips(items: Sequence[tuple[str, str]]) -> None:
    body = "".join(f'<span class="feature-chip"><code>{_escape(code)}</code>{_escape(label)}</span>' for code, label in items)
    st.markdown(f'<div class="feature-list">{body}</div>', unsafe_allow_html=True)


def disease_record(
    title: str,
    origin: str,
    features: str,
    classical: str,
    quantum: str,
    runtime: str,
    verdict: str,
    conclusion: str,
) -> str:
    metrics = (
        ("Features", features),
        ("Classical sensitivity / AUC", classical),
        ("QSVC sensitivity / AUC", quantum),
        ("QSVC fit-time ratio", runtime),
    )
    metrics_html = "".join(f'<div class="disease-metric"><span>{_escape(label)}</span><b>{_escape(value)}</b></div>' for label, value in metrics)
    return f"""<article class="disease-record">
    <div class="disease-record-header"><h3>{_escape(title)}</h3>{verdict_badge(verdict)}</div>
    <div class="disease-origin">{_escape(origin)}</div>
    <div class="disease-metrics">{metrics_html}</div>
    <p class="disease-conclusion">{_escape(conclusion)}</p>
    </article>"""
