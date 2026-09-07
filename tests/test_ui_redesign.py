from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_required_ui_components_are_centralised() -> None:
    source = (ROOT / "src/ui_components.py").read_text()
    required = [
        "def page_header(",
        "def section_header(",
        "def hero_metric(",
        "def comparison_metric(",
        "def evidence_row(",
        "def verdict_badge(",
        "def research_note(",
        "def limitation_callout(",
        "def chart_caption(",
    ]
    assert all(component in source for component in required)


def test_theme_uses_shared_tokens_and_spacing_scale() -> None:
    source = (ROOT / "src/ui_theme.py").read_text()
    for token in ("--bg", "--surface", "--text-primary", "--text-secondary", "--accent", "--border", "--radius", "--space-1", "--space-7"):
        assert token in source
    assert "--space-1: 8px" in source
    assert "--space-7: 64px" in source


def test_theme_includes_accessibility_and_reduced_motion_guards() -> None:
    source = (ROOT / "src/ui_theme.py").read_text()
    assert ":focus-visible" in source
    assert "prefers-reduced-motion" in source
    assert "min-height: 44px" in source
    assert ".verdict::before" in source


def test_current_streamlit_buttons_have_explicit_contrast_states() -> None:
    source = (ROOT / "src/ui_theme.py").read_text()
    assert 'button[data-testid="stBaseButton-secondary"]' in source
    assert 'button[data-variant="segmented_control"]' in source
    assert '[aria-checked="true"]' in source
    assert ":is(p, span) { color: inherit !important; }" in source
    assert "background: var(--surface-raised) !important" in source
    assert "color: white !important" in source


def test_responsive_layout_has_tablet_and_mobile_breakpoints() -> None:
    source = (ROOT / "src/ui_theme.py").read_text()
    assert "@media (max-width: 960px)" in source
    assert "@media (max-width: 640px)" in source
    assert "overflow-x: hidden" in source
    assert ".comparison-hero { grid-template-columns: 1fr" in source


def test_app_consumes_shared_presentation_system() -> None:
    source = (ROOT / "app.py").read_text()
    assert "from src.ui_components import" in source
    assert "from src.ui_theme import" in source
    assert "apply_theme()" in source
    assert "<style>" not in source
    assert "evidence-grid" not in source
    assert "disease-grid" not in source


def test_redesign_preserves_five_pages_and_transportability_hero() -> None:
    source = (ROOT / "app.py").read_text()
    navigation = ["Overview", "CKD Benchmark", "Robustness & Shift", "Cross-Disease", "Quantum Evidence"]
    assert all(f'"{page}"' in source for page in navigation)
    assert "Internal feature stability did not guarantee external feature transportability." in source
    assert "Neither model demonstrated reliable better-than-random discrimination." in source
    assert "metric_strip(" in source
