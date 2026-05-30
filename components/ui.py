"""Shared UI components for Aligner Predictor — PolyStain design system."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

_ASSETS = Path(__file__).resolve().parent.parent / "assets"

PLOTLY_THEME: dict[str, Any] = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor":  "rgba(0,0,0,0)",
    "font":          {"family": "DM Mono, monospace", "color": "#c8bfb0", "size": 12},
    "margin":        {"l": 0, "r": 0, "t": 30, "b": 0},
    "colorway":      ["rgba(210,185,140,1)", "#4ade80", "#fbbf24", "#fb923c", "#f87171"],
    "xaxis":         {"gridcolor": "rgba(255,255,255,0.18)", "linecolor": "rgba(255,255,255,0.22)",
                      "tickfont": {"color": "#c8bfb0", "size": 11}},
    "yaxis":         {"gridcolor": "rgba(255,255,255,0.18)", "linecolor": "rgba(255,255,255,0.22)",
                      "tickfont": {"color": "#c8bfb0", "size": 11}},
}


def _detect_theme() -> str:
    try:
        base = st.get_option("theme.base")
        if isinstance(base, str) and base == "light":
            return "light"
    except Exception:
        pass
    return "dark"


def inject_css() -> None:
    css_path = _ASSETS / "style.css"
    try:
        css = css_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        css = ""
    theme = _detect_theme()
    st.markdown(
        f'<style>{css}</style>'
        f'<div class="ap-theme" data-theme="{theme}" style="display:none"></div>',
        unsafe_allow_html=True,
    )


def navbar(active: str = "home") -> None:
    pages = [
        ("home",      "/",           "/ home"),
        ("strumento", "/Strumento",  "/ strumento"),
        ("risultati", "/Risultati",  "/ risultati"),
        ("fonti",     "/Fonti",      "/ fonti"),
    ]
    links = "".join(
        f'<a href="{path}" class="{"active" if key == active else ""}">{label}</a>'
        for key, path, label in pages
    )
    st.markdown(f'<nav class="ap-nav">{links}</nav>', unsafe_allow_html=True)


def disclaimer(text: str = (
    "⚑ Strumento esplorativo — i punteggi si basano su dati di letteratura e stime del modello. "
    "Non sostituisce la valutazione clinica."
)) -> None:
    st.markdown(
        f'<div class="ap-disclaimer">{text}</div>',
        unsafe_allow_html=True,
    )


def page_hero(eyebrow: str, title: str, subtitle: str = "") -> None:
    sub_html = (
        f'<p>{subtitle}</p>' if subtitle else ""
    )
    st.markdown(
        f"""<div class="ap-hero">
          <div class="ap-hero-eyebrow">{eyebrow}</div>
          <h1>{title}</h1>
          {sub_html}
        </div>""",
        unsafe_allow_html=True,
    )


def section_title(text: str) -> None:
    st.markdown(
        f'<div class="ap-section">'
        f'<span class="ap-section-label">{text}</span>'
        f'<span class="ap-section-line"></span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def score_card(
    label: str,
    value: float | None,
    risk_class: str,
    note: str = "",
) -> None:
    css_class = _risk_css(risk_class)
    bar_pct = int(min(100, max(0, value or 0)))
    bar_color = _risk_bar_color(risk_class)
    val_str = f"{value:.1f}" if value is not None else "N/A"

    st.markdown(
        f"""<div class="ap-card {css_class}">
          <div class="ap-card-label">{label}</div>
          <div class="ap-card-value">{val_str}</div>
          <div class="ap-card-sub">{risk_class}</div>
          <div class="ap-bar-track">
            <div class="ap-bar-fill" style="width:{bar_pct}%;background:{bar_color};"></div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )
    if note:
        with st.popover("ℹ️ dettagli"):
            st.markdown(note)


def step_list(steps: list[dict[str, str]]) -> None:
    """
    steps: list of dicts with keys: tag, title, body
    """
    items = ""
    for i, step in enumerate(steps, 1):
        items += (
            f'<div class="ap-step">'
            f'<div class="ap-step-num">{i:02d}</div>'
            f'<div class="ap-step-content">'
            f'<div class="ap-step-tag">{step.get("tag", "")}</div>'
            f'<div class="ap-step-title">{step.get("title", "")}</div>'
            f'<div class="ap-step-body">{step.get("body", "")}</div>'
            f'</div></div>'
        )
    st.markdown(f'<div class="ap-steps">{items}</div>', unsafe_allow_html=True)


def footer_buttons(
    primary_label: str,
    primary_page: str,
    secondary_label: str = "",
    secondary_page: str = "",
) -> None:
    secondary_html = (
        f'<a class="ap-footer-btn" href="{secondary_page}">{secondary_label}</a>'
        if secondary_label and secondary_page else ""
    )
    st.markdown(
        f'<div class="ap-footer-btns">'
        f'<a class="ap-footer-btn" href="{primary_page}">{primary_label}</a>'
        f'{secondary_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _risk_css(risk_class: str) -> str:
    mapping = {
        "basso":        "low",
        "moderato":     "mid",
        "moderato-alto": "high-mid",
        "alto":         "high",
    }
    return mapping.get(risk_class.lower() if risk_class else "", "mid")


def _risk_bar_color(risk_class: str) -> str:
    mapping = {
        "basso":        "var(--green)",
        "moderato":     "var(--yellow)",
        "moderato-alto": "var(--orange)",
        "alto":         "var(--red)",
    }
    return mapping.get(risk_class.lower() if risk_class else "", "var(--accent)")
