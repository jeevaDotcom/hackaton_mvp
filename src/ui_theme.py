"""Shared visual tokens for the Q-CARE Streamlit interface."""

from __future__ import annotations

import streamlit as st


ACCENT = "#315AD8"
TEXT_PRIMARY = "#191B20"
TEXT_SECONDARY = "#5C626C"
CHART_CLASSICAL = "#24272E"
CHART_QUANTUM = ACCENT


APPLE_HIG_CSS = """
<style>
:root {
  --bg: #F7F5EF;
  --surface: #F0EFEA;
  --surface-raised: #FFFDF8;
  --text-primary: #191B20;
  --text-secondary: #5C626C;
  --accent: #315AD8;
  --accent-hover: #2448B8;
  --border: #D9DAD5;
  --warning-bg: #F4EDDD;
  --warning-text: #71571A;
  --supported: #287058;
  --supported-bg: #E4F0EA;
  --mixed: #806019;
  --mixed-bg: #F4EDDD;
  --negative: #8A4B4B;
  --negative-bg: #F3E8E6;
  --neutral: #646A73;
  --neutral-bg: #ECECE8;
  --radius-sm: 12px;
  --radius: 16px;
  --radius-lg: 24px;
  --space-1: 8px;
  --space-2: 12px;
  --space-3: 16px;
  --space-4: 24px;
  --space-5: 32px;
  --space-6: 48px;
  --space-7: 64px;
}

html { color-scheme: light; }
.stApp {
  background: var(--bg);
  color: var(--text-primary);
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
  overflow-x: hidden;
}
.block-container {
  max-width: 1240px;
  padding: var(--space-6) var(--space-7) var(--space-7);
}
p, label, li { color: var(--text-primary); }
a { color: var(--accent) !important; text-underline-offset: 3px; }
h1, h2, h3 {
  color: var(--text-primary) !important;
  letter-spacing: -0.035em;
}
h1 { font-size: clamp(48px, 5vw, 64px) !important; line-height: 1 !important; font-weight: 700 !important; }
h2 { font-size: clamp(28px, 3vw, 36px) !important; line-height: 1.12 !important; font-weight: 650 !important; }
h3 { font-size: 24px !important; line-height: 1.2 !important; font-weight: 650 !important; }

/* Light, quiet navigation. */
[data-testid="stSidebar"] {
  background: var(--surface);
  border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top: var(--space-4); }
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
[data-testid="stSidebar"] .stRadio > label { display: none; }
[data-testid="stSidebar"] .stRadio label {
  min-height: 44px;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: 15px;
  transition: background-color 180ms ease-out, color 180ms ease-out;
}
[data-testid="stSidebar"] .stRadio label:hover { background: rgba(49, 90, 216, 0.07); }
[data-testid="stSidebar"] [aria-checked="true"] { background: rgba(49, 90, 216, 0.11); }
[data-testid="stSidebar"] [aria-checked="true"] p { color: var(--accent) !important; font-weight: 650; }
.sidebar-brand { margin: 0 0 var(--space-5); }
.sidebar-brand strong { display: block; font-size: 22px; letter-spacing: -0.04em; }
.sidebar-brand span { display: block; margin-top: var(--space-1); color: var(--text-secondary); font-size: 13px; line-height: 1.45; }
.sidebar-meta { margin-top: var(--space-6); padding-top: var(--space-4); border-top: 1px solid var(--border); }
.sidebar-meta b { display: block; margin-bottom: var(--space-1); font-size: 13px; font-weight: 650; }
.sidebar-meta span { display: block; color: var(--text-secondary); font-size: 12px; line-height: 1.5; }
.sidebar-workflow { display: grid; gap: var(--space-2); }
.sidebar-workflow b { margin-bottom: var(--space-1); color: var(--accent); font-size: 11px; letter-spacing: 0.08em; }
.sidebar-workflow span { color: var(--text-secondary); font-size: 13px; }

/* Page structure. */
.page-header { margin-bottom: var(--space-7); animation: qc-enter 220ms ease-out both; }
.page-context { margin-bottom: var(--space-2); color: var(--accent); font-size: 14px; font-weight: 650; }
.page-header h1 { max-width: 900px; margin: 0; }
.page-purpose { max-width: 760px; margin: var(--space-3) 0 0; color: var(--text-secondary); font-size: 19px; line-height: 1.55; }
.overview-support { max-width: 760px; margin: calc(-1 * var(--space-6)) 0 var(--space-7); color: var(--text-secondary); font-size: 19px; line-height: 1.55; }
.hero-statement { max-width: 920px; margin: 0 0 var(--space-6); font-size: clamp(36px, 5vw, 56px); font-weight: 650; letter-spacing: -0.045em; line-height: 1.04; }
.section-header { margin: var(--space-7) 0 var(--space-4); }
.section-header h2 { margin: 0 !important; }
.section-header p { max-width: 720px; margin: var(--space-2) 0 0; color: var(--text-secondary); font-size: 16px; line-height: 1.55; }

/* The primary comparison is one visual plane, not a card grid. */
.comparison-hero {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: var(--space-5);
  align-items: center;
  padding: var(--space-6);
  margin: 0 0 var(--space-5);
  background: var(--surface-raised);
  border-radius: var(--radius-lg);
  box-shadow: 0 12px 32px rgba(27, 30, 38, 0.05);
  animation: qc-enter 220ms 50ms ease-out both;
}
.comparison-side { min-width: 0; }
.comparison-side:last-child { text-align: right; }
.comparison-label { color: var(--text-secondary); font-size: 15px; font-weight: 600; }
.comparison-value { margin-top: var(--space-2); font-size: clamp(48px, 7vw, 76px); font-weight: 720; letter-spacing: -0.06em; line-height: 0.95; }
.comparison-detail { margin-top: var(--space-2); color: var(--text-secondary); font-size: 14px; line-height: 1.45; }
.comparison-arrow { color: var(--accent); font-size: 32px; font-weight: 400; }
.comparison-caption { margin: calc(-1 * var(--space-3)) 0 var(--space-6); color: var(--text-secondary); font-size: 14px; text-align: center; }

.hero-metric {
  padding: var(--space-5) 0;
  margin-bottom: var(--space-5);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  animation: qc-enter 220ms 50ms ease-out both;
}
.hero-metric-label { color: var(--text-secondary); font-size: 15px; font-weight: 600; }
.hero-metric-value { margin: var(--space-2) 0; font-size: clamp(48px, 7vw, 72px); font-weight: 720; letter-spacing: -0.06em; line-height: 0.95; }
.hero-metric-context { max-width: 720px; color: var(--text-secondary); font-size: 16px; line-height: 1.5; }

.metric-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 0 0 var(--space-7);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}
.metric-strip-item { padding: var(--space-4) var(--space-4) var(--space-4) 0; transition: background-color 180ms ease-out; }
.metric-strip-item + .metric-strip-item { padding-left: var(--space-4); border-left: 1px solid var(--border); }
.metric-strip-label { color: var(--text-secondary); font-size: 13px; line-height: 1.35; }
.metric-strip-value { margin-top: var(--space-2); font-size: 32px; font-weight: 700; letter-spacing: -0.045em; }
.metric-strip-note { margin-top: var(--space-1); color: var(--text-secondary); font-size: 12px; line-height: 1.45; }

/* Narrative and metadata primitives. */
.process-flow { display: grid; grid-template-columns: repeat(auto-fit, minmax(144px, 1fr)); margin: 0 0 var(--space-6); }
.process-step { position: relative; padding: var(--space-3) var(--space-4) var(--space-3) 0; color: var(--text-secondary); font-size: 14px; border-bottom: 1px solid var(--border); }
.process-step strong { display: block; margin-bottom: var(--space-1); color: var(--text-primary); font-size: 15px; }
.process-step:not(:last-child)::after { content: "→"; position: absolute; right: var(--space-2); top: var(--space-3); color: var(--accent); }
.metadata-list { margin-bottom: var(--space-5); }
.metadata-row { display: grid; grid-template-columns: 160px 1fr; gap: var(--space-4); padding: var(--space-3) 0; border-bottom: 1px solid var(--border); }
.metadata-row b { font-size: 14px; font-weight: 600; }
.metadata-row span { color: var(--text-secondary); font-size: 15px; line-height: 1.5; }
.feature-list { display: flex; flex-wrap: wrap; gap: var(--space-2); margin-bottom: var(--space-3); }
.feature-chip { padding: var(--space-2) var(--space-3); background: var(--surface); border-radius: var(--radius-sm); font-size: 14px; }
.feature-chip code { margin-right: var(--space-1); color: var(--accent); font-size: 12px; }

/* Evidence table with text verdicts; colour is supplementary. */
.evidence-table { margin-bottom: var(--space-6); }
.evidence-row {
  display: grid;
  grid-template-columns: 1.35fr 1fr 1fr 0.85fr;
  gap: var(--space-4);
  align-items: center;
  min-height: 64px;
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--border);
  font-size: 14px;
}
.evidence-row.header { min-height: auto; color: var(--text-secondary); font-size: 12px; font-weight: 650; }
.evidence-dimension { font-weight: 620; }
.evidence-copy { color: var(--text-secondary); line-height: 1.4; }
.verdict {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  min-height: 28px;
  padding: 0 var(--space-2);
  border-radius: var(--space-1);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  white-space: nowrap;
}
.verdict::before { content: ""; width: 6px; height: 6px; margin-right: var(--space-1); border-radius: 50%; background: currentColor; }
.verdict.supported { color: var(--supported); background: var(--supported-bg); }
.verdict.mixed { color: var(--mixed); background: var(--mixed-bg); }
.verdict.negative { color: var(--negative); background: var(--negative-bg); }
.verdict.neutral, .verdict.inconclusive { color: var(--neutral); background: var(--neutral-bg); }

.research-note, .limitation-callout {
  max-width: 880px;
  padding: var(--space-4);
  margin: var(--space-4) 0;
  border-radius: var(--radius);
  background: var(--surface);
}
.limitation-callout { color: var(--warning-text); background: var(--warning-bg); }
.research-note b, .limitation-callout b { display: block; margin-bottom: var(--space-1); font-size: 15px; }
.research-note span, .limitation-callout span { color: inherit; font-size: 14px; line-height: 1.55; }
.chart-caption { margin: var(--space-2) 0 var(--space-4); color: var(--text-secondary); font-size: 13px; line-height: 1.5; }

.disease-list { margin-bottom: var(--space-6); }
.disease-record { padding: var(--space-5) 0; border-bottom: 1px solid var(--border); transition: background-color 180ms ease-out; }
.disease-record:first-child { border-top: 1px solid var(--border); }
.disease-record-header { display: flex; justify-content: space-between; gap: var(--space-4); align-items: flex-start; }
.disease-record h3 { margin: 0 !important; }
.disease-origin { max-width: 720px; margin: var(--space-1) 0 var(--space-4); color: var(--text-secondary); font-size: 14px; }
.disease-metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-4); }
.disease-metric span { display: block; color: var(--text-secondary); font-size: 12px; }
.disease-metric b { display: block; margin-top: var(--space-1); font-size: 18px; letter-spacing: -0.02em; }
.disease-conclusion { margin: var(--space-4) 0 0; font-size: 15px; }

.replay-result { padding: var(--space-5); margin-top: var(--space-4); background: var(--surface-raised); border-radius: var(--radius-lg); }
.replay-header { display: flex; justify-content: space-between; gap: var(--space-4); align-items: center; margin-bottom: var(--space-4); }
.replay-header h3 { margin: 0 !important; }
.result-metrics { display: grid; grid-template-columns: repeat(4, 1fr); border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
.result-metric { padding: var(--space-3) var(--space-3) var(--space-3) 0; }
.result-metric + .result-metric { padding-left: var(--space-3); border-left: 1px solid var(--border); }
.result-metric span { display: block; color: var(--text-secondary); font-size: 12px; }
.result-metric b { display: block; margin-top: var(--space-1); font-size: 24px; }

.circuit {
  padding: var(--space-4);
  overflow: auto;
  border-radius: var(--radius);
  background: #20242C;
  color: #F3F4F6;
  font: 500 12px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace;
}

/* Additional live VQC research workflow. */
.research-boundary {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: var(--space-4);
  align-items: baseline;
  padding: var(--space-3) 0;
  margin: calc(-1 * var(--space-4)) 0 var(--space-6);
  border-top: 1px solid var(--accent);
  border-bottom: 1px solid var(--border);
}
.research-boundary b { color: var(--accent); font-size: 13px; letter-spacing: 0.06em; }
.research-boundary span { color: var(--text-secondary); font-size: 14px; line-height: 1.5; }
.live-result-plane {
  padding: var(--space-6);
  margin-bottom: var(--space-5);
  border-radius: var(--radius-lg);
  background: var(--surface-raised);
  box-shadow: 0 12px 32px rgba(27, 30, 38, 0.05);
  animation: qc-enter 220ms ease-out both;
}
.live-kicker { color: var(--accent); font-size: 13px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; }
.live-classification { max-width: 840px; margin: var(--space-3) 0 var(--space-5); font-size: clamp(38px, 5vw, 58px); font-weight: 700; letter-spacing: -0.05em; line-height: 1.02; }
.live-score-row { display: grid; grid-template-columns: 240px 1fr; gap: var(--space-5); align-items: end; padding-top: var(--space-4); border-top: 1px solid var(--border); }
.live-score-row span { display: block; color: var(--text-secondary); font-size: 13px; }
.live-score-row strong { display: block; margin-top: var(--space-1); font-size: 42px; letter-spacing: -0.05em; }
.live-score-note { padding-bottom: var(--space-1); color: var(--text-secondary); font-size: 14px; }
.live-caution { width: fit-content; margin-top: var(--space-4); padding: var(--space-1) var(--space-2); border-radius: 6px; color: var(--negative); background: var(--negative-bg); font-size: 12px; font-weight: 700; }
.influence-list { border-top: 1px solid var(--border); }
.influence-row { display: grid; grid-template-columns: 220px 1fr; gap: var(--space-4); padding: var(--space-3) 0; border-bottom: 1px solid var(--border); }
.influence-row b, .influence-row span { display: block; }
.influence-row span { margin-top: 3px; color: var(--text-secondary); font-size: 12px; text-transform: capitalize; }
.influence-row p { grid-column: 2; margin: calc(-1 * var(--space-2)) 0 0; color: var(--text-secondary); font-size: 12px; }
.influence-measure { align-self: center; }
.influence-track { height: 5px; overflow: hidden; border-radius: 5px; background: var(--border); }
.influence-track i { display: block; height: 100%; border-radius: inherit; background: var(--accent); }
.influence-measure small { display: block; margin-top: 6px; color: var(--text-secondary); text-align: right; }
.agreement-line { display: flex; justify-content: space-between; gap: var(--space-4); padding: var(--space-3) 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
.agreement-line span { color: var(--text-secondary); }
.agreement-line strong { color: var(--accent); }
.model-decision-row { display: grid; grid-template-columns: 160px 1fr; gap: var(--space-4); padding: var(--space-3) 0; border-bottom: 1px solid var(--border); }
.model-decision-row span { color: var(--text-secondary); }
.review-list { max-width: 880px; margin: 0; padding-left: 24px; }
.review-list li { padding: 0 0 var(--space-3) var(--space-1); border-bottom: 1px solid var(--border); line-height: 1.5; }

/* Single-page clinical research workstation. */
.workstation-hero { max-width: 1000px; margin: 0 0 var(--space-6); animation: qc-enter 240ms ease-out both; }
.workstation-brand { color: var(--text-primary); font-size: clamp(68px, 10vw, 118px); font-weight: 760; letter-spacing: -0.075em; line-height: 0.82; }
.workstation-hero h1 { max-width: 820px; margin: var(--space-4) 0 0; font-size: clamp(34px, 4vw, 52px) !important; font-weight: 650 !important; letter-spacing: -0.045em; line-height: 1.02 !important; }
.workstation-hero p { max-width: 700px; margin: var(--space-3) 0 0; color: var(--text-secondary); font-size: 19px; line-height: 1.5; }
.workstation-boundary { margin-top: 0; }
.vqc-honesty { display: grid; grid-template-columns: 230px 1fr; gap: var(--space-4); align-items: baseline; padding: var(--space-4) 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
.vqc-honesty b { width: fit-content; padding: 6px 10px; border-radius: 6px; color: var(--negative); background: var(--negative-bg); font-size: 12px; }
.vqc-honesty span { color: var(--text-secondary); font-size: 14px; line-height: 1.5; }
.workstation-score { display: grid; grid-template-columns: 1fr auto; gap: var(--space-2) var(--space-5); align-items: end; margin: var(--space-5) 0 0; padding: var(--space-4) 0; border-bottom: 1px solid var(--border); }
.workstation-score span { color: var(--text-secondary); font-size: 14px; }
.workstation-score strong { grid-row: span 2; font-size: 48px; letter-spacing: -0.055em; }
.workstation-score small { color: var(--text-secondary); font-size: 12px; }
.dataset-status { display: flex; justify-content: space-between; gap: var(--space-4); align-items: baseline; margin-bottom: var(--space-4); padding: var(--space-3) 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
.dataset-status span { color: var(--text-secondary); }
.dataset-status strong { color: var(--accent); letter-spacing: 0.02em; }
.dataset-status.review-required strong { color: var(--warning-text); }
.dataset-status.incompatible strong { color: var(--negative); }
.reduction-line { display: grid; grid-template-columns: auto 1fr auto auto 1fr; gap: var(--space-3); align-items: baseline; padding: var(--space-5) 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
.reduction-line strong { font-size: 58px; letter-spacing: -0.06em; }
.reduction-line span { color: var(--text-secondary); }
.reduction-line i { color: var(--accent); font-size: 28px; font-style: normal; }
.not-equal-statement { display: grid; grid-template-columns: 1fr auto 1fr; gap: var(--space-4); align-items: center; margin: var(--space-5) 0; padding: var(--space-5) 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); font-size: 22px; }
.not-equal-statement b { color: var(--accent); font-size: 38px; }
.not-equal-statement span:last-child { text-align: right; }
.final-evidence-list { margin-bottom: var(--space-5); border-top: 1px solid var(--border); }
.final-evidence-row { display: grid; grid-template-columns: 1fr 240px; gap: var(--space-4); padding: var(--space-3) 0; border-bottom: 1px solid var(--border); }
.final-evidence-row span { color: var(--text-secondary); }
.final-evidence-row strong { font-size: 13px; letter-spacing: 0.02em; text-align: right; }
.final-status { padding: var(--space-6) 0; border-top: 2px solid var(--text-primary); border-bottom: 2px solid var(--text-primary); }
.final-status span, .final-status b { display: block; color: var(--text-secondary); font-size: 13px; letter-spacing: 0.04em; text-transform: uppercase; }
.final-status strong { display: block; margin: var(--space-2) 0; font-size: clamp(38px, 6vw, 64px); letter-spacing: -0.055em; line-height: 1; }
.footer { margin-top: var(--space-7); padding-top: var(--space-4); border-top: 1px solid var(--border); color: var(--text-secondary); font-size: 13px; line-height: 1.6; }
.footer b { color: var(--text-primary); }

/* Native Streamlit controls. */
[data-testid="stDataFrame"] { overflow: hidden; border: 0; border-radius: var(--radius-sm); }
[data-testid="stMetric"] { padding: var(--space-3) 0; }
[data-testid="stMetricValue"] { color: var(--text-primary); letter-spacing: -0.04em; }
[data-testid="stExpander"] { margin-top: var(--space-2); border: 0; border-bottom: 1px solid var(--border); border-radius: 0; background: transparent; }
[data-testid="stExpander"] summary { min-height: 56px; font-weight: 650; }
[data-testid="stFileUploader"] { padding: var(--space-3) 0; }
div[data-testid="stDownloadButton"] > button, div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
  min-height: 44px;
  padding: 0 var(--space-3);
  border: 0;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: white;
  font-weight: 600;
  transition: background-color 180ms ease-out, transform 180ms ease-out;
}
div[data-testid="stDownloadButton"] > button:hover, div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover { background: var(--accent-hover); color: white; }
button:focus-visible, input:focus-visible, [role="radio"]:focus-visible, summary:focus-visible { outline: 3px solid rgba(49, 90, 216, 0.34) !important; outline-offset: 2px; }

@keyframes qc-enter { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; } }

@media (max-width: 960px) {
  .block-container { padding: var(--space-5) var(--space-4) var(--space-7); }
  .comparison-hero { padding: var(--space-5); }
  .metric-strip { grid-template-columns: repeat(2, 1fr); }
  .metric-strip-item:nth-child(3) { padding-left: 0; border-left: 0; border-top: 1px solid var(--border); }
  .metric-strip-item:nth-child(4) { border-top: 1px solid var(--border); }
  .process-flow { grid-template-columns: 1fr; }
  .process-step:not(:last-child)::after { content: "↓"; right: 0; }
  .evidence-row { grid-template-columns: 1.2fr 1fr 1fr 0.9fr; gap: var(--space-3); }
  .disease-metrics { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 640px) {
  .block-container { padding: var(--space-4) var(--space-3) var(--space-7); }
  .page-header { margin-bottom: var(--space-6); }
  .page-purpose { font-size: 17px; }
  .comparison-hero { grid-template-columns: 1fr; gap: var(--space-4); padding: var(--space-4); }
  .comparison-side:last-child { text-align: left; }
  .comparison-arrow { transform: rotate(90deg); }
  .metric-strip { grid-template-columns: 1fr; }
  .research-boundary, .live-score-row, .influence-row, .model-decision-row { grid-template-columns: 1fr; }
  .vqc-honesty, .final-evidence-row { grid-template-columns: 1fr; }
  .final-evidence-row strong { text-align: left; }
  .reduction-line { grid-template-columns: auto 1fr; }
  .reduction-line i { grid-column: 1 / -1; transform: rotate(90deg); width: fit-content; }
  .not-equal-statement { grid-template-columns: 1fr; }
  .not-equal-statement span:last-child { text-align: left; }
  .influence-row p { grid-column: 1; margin-top: 0; }
  .metric-strip-item, .metric-strip-item + .metric-strip-item { padding: var(--space-3) 0; border-left: 0; border-top: 1px solid var(--border); }
  .metric-strip-item:first-child { border-top: 0; }
  .metadata-row { grid-template-columns: 1fr; gap: var(--space-1); }
  .evidence-row { grid-template-columns: 1fr; gap: var(--space-2); padding: var(--space-4) 0; }
  .evidence-row.header { display: none; }
  .evidence-copy::before { display: block; color: var(--text-secondary); font-size: 11px; font-weight: 650; }
  .evidence-classical::before { content: "Classical"; }
  .evidence-quantum::before { content: "Quantum"; }
  .disease-record-header, .replay-header { display: block; }
  .disease-record-header .verdict, .replay-header .verdict { margin-top: var(--space-2); }
  .disease-metrics, .result-metrics { grid-template-columns: 1fr 1fr; }
  .result-metric:nth-child(3) { padding-left: 0; border-left: 0; border-top: 1px solid var(--border); }
  .result-metric:nth-child(4) { border-top: 1px solid var(--border); }
}
</style>
"""


def apply_theme() -> None:
    """Install the shared visual system once per Streamlit render."""
    st.markdown(APPLE_HIG_CSS, unsafe_allow_html=True)
