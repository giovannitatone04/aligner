from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.ui import (
    PLOTLY_THEME,
    footer_buttons,
    inject_css,
    navbar,
    page_hero,
    score_card,
    section_title,
)
from predictor_level1_v2 import EvidenceDB, Level1Predictor, UserHabits
from scoring_level2 import build_level2_scores

st.set_page_config(
    page_title="PolyStain · Risultati",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()
navbar(active="risultati")

BASE_DIR  = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _risk_color_hex(risk_class: str) -> str:
    m = {
        "basso":         "#4ade80",
        "moderato":      "#fbbf24",
        "moderato-alto": "#fb923c",
        "alto":          "#f87171",
    }
    return m.get((risk_class or "").lower(), "rgba(210,185,140,1)")


@st.cache_resource
def load_model():
    db = EvidenceDB()
    return db, Level1Predictor(db)


def run_model(predictor, inputs):
    habits = UserHabits(
        material_brand=inputs["material_brand"],
        wear_days=inputs["wear_days"],
        coffee_per_day=inputs["coffee_per_day"],
        tea_per_day=inputs["tea_per_day"],
        red_wine_per_day=inputs["red_wine_per_day"],
        cola_per_day=inputs["cola_per_day"],
        cigarettes_per_day=inputs["cigarettes_per_day"],
    )
    l1 = predictor.predict(habits)
    l2 = build_level2_scores(l1)
    return l1, l2


def choose_aligner_image(risk_class: str | None) -> Path:
    mapping = {
        "basso":         ASSETS_DIR / "aligner_clear.png",
        "moderato":      ASSETS_DIR / "aligner_low.png",
        "moderato-alto": ASSETS_DIR / "aligner_mid.png",
        "alto":          ASSETS_DIR / "aligner_high.png",
    }
    return mapping.get((risk_class or "").lower(), ASSETS_DIR / "aligner_clear.png")


def agents_df(l1) -> pd.DataFrame:
    rows = []
    for r in l1.get("agent_predictions", []):
        tipo = r.get("matched_on", "")
        tipo_label = {
            "brand":               "Dato diretto",
            "polymer_family_proxy": "Stima analogia",
            "none":                "Assente",
        }.get(tipo, tipo)
        rows.append({
            "Agente":             r.get("agent"),
            "Esposizioni/giorno": r.get("events_per_day"),
            "Ore totali":         r.get("total_exposure_hours"),
            "Variaz. colore":     r.get("estimated_deltaE"),
            "Intensità":          r.get("severity"),
            "Tipo dato":          tipo_label,
        })
    return pd.DataFrame(rows)


def scores_df(l2) -> pd.DataFrame:
    return pd.DataFrame([
        {"Indice": "Cromatico",    "Score": l2["staining_summary"].get("staining_score"),         "Classe": l2["staining_summary"].get("staining_risk_class")},
        {"Indice": "Meccanico",    "Score": l2["mechanical_summary"].get("mechanical_risk_score"), "Classe": l2["mechanical_summary"].get("mechanical_risk_class")},
        {"Indice": "Superficiale", "Score": l2["surface_summary"].get("surface_risk_score"),       "Classe": l2["surface_summary"].get("surface_risk_class")},
        {"Indice": "Globale",      "Score": l2["global_summary"].get("global_risk_score"),         "Classe": l2["global_summary"].get("global_risk_class")},
        {"Indice": "Affidabilità", "Score": l2["confidence_summary"].get("confidence_score"),      "Classe": l2["confidence_summary"].get("confidence_level")},
    ])


# ── Charts ────────────────────────────────────────────────────────────────────

def plot_agents(l1):
    rows = [
        (r["agent"], float(r["estimated_deltaE"]))
        for r in l1.get("agent_predictions", [])
        if r.get("estimated_deltaE") is not None
    ]
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["Agente", "Variaz. colore"])
    fig = px.bar(df, x="Agente", y="Variaz. colore",
                 color_discrete_sequence=["rgba(210,185,140,1)"])
    layout = dict(PLOTLY_THEME)
    layout["title"] = "Variazione di colore per agente"
    layout["showlegend"] = False
    fig.update_layout(**layout)
    fig.update_traces(marker_line_width=0)
    return fig


def plot_radar(l2):
    cats = ["Cromatico", "Meccanico", "Superficiale", "Globale", "Affidabilità"]
    vals = [
        l2["staining_summary"].get("staining_score") or 0,
        l2["mechanical_summary"].get("mechanical_risk_score") or 0,
        l2["surface_summary"].get("surface_risk_score") or 0,
        l2["global_summary"].get("global_risk_score") or 0,
        l2["confidence_summary"].get("confidence_score") or 0,
    ]
    vals_closed = vals + [vals[0]]
    cats_closed = cats + [cats[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals_closed, theta=cats_closed,
        fill="toself",
        fillcolor="rgba(210,185,140,0.06)",
        line=dict(color="rgba(210,185,140,1)", width=1.5),
        name="Score",
    ))
    radar_layout = dict(PLOTLY_THEME)
    radar_layout["polar"] = dict(
        bgcolor="rgba(0,0,0,0)",
        radialaxis=dict(range=[0, 100],
                        gridcolor="rgba(255,255,255,0.2)",
                        tickfont=dict(color="#c8bfb0", size=10)),
        angularaxis=dict(gridcolor="rgba(255,255,255,0.2)",
                         tickfont=dict(color="#c8bfb0", size=12)),
    )
    fig.update_layout(**radar_layout)
    return fig


def plot_bar_scores(l2):
    df = scores_df(l2).dropna(subset=["Score"])
    colors = [_risk_color_hex(r) for r in df["Classe"]]
    fig = px.bar(df, x="Indice", y="Score")
    layout = dict(PLOTLY_THEME)
    layout["title"] = "Punteggi (0–100)"
    layout["showlegend"] = False
    layout["yaxis"] = dict(range=[0, 100], gridcolor="rgba(255,255,255,0.2)",
                           tickfont=dict(color="#c8bfb0", size=11))
    fig.update_layout(**layout)
    fig.update_traces(marker_color=colors, marker_line_width=0)
    return fig


def _interpretation(g_class: str, staining_class: str, mech_class: str, g_score: float | None) -> str:
    score = g_score or 0
    dominant = ""
    if staining_class in ("alto", "moderato-alto") and mech_class in ("basso", "moderato"):
        dominant = " Il fattore principale è il rischio cromatico, legato alle abitudini del paziente."
    elif mech_class in ("alto", "moderato-alto") and staining_class in ("basso", "moderato"):
        dominant = " Il fattore principale è la resistenza meccanica del materiale nel tempo."

    messages = {
        "basso": (
            f"Con un punteggio di {score:.0f}/100 il materiale mostra una buona tenuta nelle condizioni indicate."
            f" Il rischio di scolorimento significativo è contenuto.{dominant}"
        ),
        "moderato": (
            f"Punteggio {score:.0f}/100: alcune abitudini contribuiscono a un rischio estetico moderato."
            f" Ridurre l'esposizione ai principali agenti coloranti può migliorare il risultato.{dominant}"
        ),
        "moderato-alto": (
            f"Punteggio {score:.0f}/100: rischio rilevante nelle condizioni inserite."
            f" Si raccomanda di limitare caffè, tè e vino durante il periodo di utilizzo.{dominant}"
        ),
        "alto": (
            f"Punteggio {score:.0f}/100: rischio elevato di scolorimento e degradazione."
            f" Valutare la scelta del materiale e una revisione delle abitudini del paziente.{dominant}"
        ),
    }
    return messages.get((g_class or "").lower(), f"Punteggio globale: {score:.0f}/100.")


# ── CSV export ────────────────────────────────────────────────────────────────

def build_export_csv(l1, l2, inputs) -> bytes:
    rows = []
    rows.append({"sezione": "input", "chiave": "materiale", "valore": inputs["material_brand"]})
    rows.append({"sezione": "input", "chiave": "giorni",    "valore": inputs["wear_days"]})
    for k in ["coffee_per_day", "tea_per_day", "red_wine_per_day", "cola_per_day", "cigarettes_per_day"]:
        rows.append({"sezione": "input", "chiave": k, "valore": inputs[k]})
    rows.append({"sezione": "level1", "chiave": "polimero",       "valore": l1.get("polymer")})
    rows.append({"sezione": "level1", "chiave": "polymer_family", "valore": l1.get("polymer_family")})
    rows.append({"sezione": "level1", "chiave": "deltaE_euclidean",
                 "valore": l2["staining_summary"].get("deltae_euclidean")})
    for name, key in [
        ("staining",   "staining_score"),
        ("mechanical", "mechanical_risk_score"),
        ("surface",    "surface_risk_score"),
        ("global",     "global_risk_score"),
        ("confidence", "confidence_score"),
    ]:
        sub = f"{name}_summary"
        rows.append({"sezione": "level2", "chiave": f"{name}_score", "valore": l2[sub].get(key)})
        cls_key = f"{name}_risk_class" if name != "confidence" else "confidence_level"
        rows.append({"sezione": "level2", "chiave": f"{name}_class", "valore": l2[sub].get(cls_key)})
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


# ── Main ──────────────────────────────────────────────────────────────────────

if "model_inputs" not in st.session_state:
    page_hero(
        eyebrow="risultati",
        title="Nessun dato disponibile",
        subtitle="Compila prima il profilo paziente nello Strumento.",
    )
    footer_buttons(
        primary_label="&rarr; Vai allo strumento",
        primary_page="/Strumento",
        secondary_label="&larr; Home",
        secondary_page="/",
    )
    st.stop()

try:
    db, predictor = load_model()
    l1, l2 = run_model(predictor, st.session_state["model_inputs"])
except Exception as e:
    st.error(f"Errore nel caricamento del modello: {e}")
    st.stop()

inputs  = st.session_state["model_inputs"]
g_score = l2["global_summary"].get("global_risk_score")
g_class = l2["global_summary"].get("global_risk_class")
g_color = _risk_color_hex(g_class)

score_str = f"{g_score:.0f}" if g_score is not None else "—"

# ── Hero ──────────────────────────────────────────────────────────────────────
page_hero(
    eyebrow=f"{inputs['material_brand']} · {l1.get('polymer')} · {inputs['wear_days']} giorni",
    title=f'Rischio globale <em style="color:{g_color};">{score_str} / 100</em>',
    subtitle=(
        f"Classe: {(g_class or '').capitalize()} &nbsp;·&nbsp; "
        f"Affidabilità: {l2['confidence_summary'].get('confidence_score')} "
        f"({l2['confidence_summary'].get('confidence_level')})"
    ),
)

with st.popover("ℹ️ Come si calcola il punteggio globale"):
    st.markdown(
        "Il **punteggio globale** (da 0 a 100) combina il rischio cromatico (50%), "
        "meccanico (25%) e superficiale (25%). "
        "Più alto è il valore, maggiore è la suscettibilità al deterioramento estetico."
    )

mech_class = l2["mechanical_summary"].get("mechanical_risk_class")
staining_class = l2["staining_summary"].get("staining_risk_class")
interp_text = _interpretation(g_class, staining_class, mech_class, g_score)
st.markdown(
    f'<div class="ap-card-sub" style="margin-bottom:2rem;">{interp_text}</div>',
    unsafe_allow_html=True,
)

# ── Score cards 2×2 ──────────────────────────────────────────────────────────
section_title("punteggi di rischio")

staining_class = l2["staining_summary"].get("staining_risk_class")
img_path = choose_aligner_image(staining_class)

img_col, cards_col = st.columns([1, 1])

with img_col:
    if img_path.exists():
        st.image(str(img_path), caption="Aspetto stimato dell'aligner", use_container_width=True)

with cards_col:
    col_a, col_b = st.columns(2)
    with col_a:
        score_card(
            "Macchia cromatica",
            l2["staining_summary"].get("staining_score"),
            l2["staining_summary"].get("staining_risk_class"),
            l2["staining_summary"].get("note", ""),
        )
        score_card(
            "Superficie",
            l2["surface_summary"].get("surface_risk_score"),
            l2["surface_summary"].get("surface_risk_class"),
            l2["surface_summary"].get("note", ""),
        )
    with col_b:
        score_card(
            "Meccanica",
            l2["mechanical_summary"].get("mechanical_risk_score"),
            l2["mechanical_summary"].get("mechanical_risk_class"),
            l2["mechanical_summary"].get("note", ""),
        )
        score_card(
            "Affidabilità",
            l2["confidence_summary"].get("confidence_score"),
            l2["confidence_summary"].get("confidence_level"),
            l2["confidence_summary"].get("note", ""),
        )

# ── Radar + bar ───────────────────────────────────────────────────────────────
section_title("analisi visiva")

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(plot_radar(l2), use_container_width=True)
with c2:
    st.plotly_chart(plot_bar_scores(l2), use_container_width=True)

# ── Agent detail ──────────────────────────────────────────────────────────────
section_title("agenti coloranti")

fig_agents = plot_agents(l1)
if fig_agents:
    st.plotly_chart(fig_agents, use_container_width=True)

st.dataframe(agents_df(l1), use_container_width=True, hide_index=True)

with st.popover("ℹ️ Come leggere la tabella"):
    st.markdown(
        "**Dato diretto**: misure reali sul materiale specifico. "
        "**Stima analogia**: dati di materiali simili usati come proxy. "
        "**Assente**: nessun dato disponibile in letteratura."
    )

# ── Profili meccanico e superficiale ─────────────────────────────────────────
with st.expander("Proprietà meccaniche e superficiali", expanded=False):
    mech = l1.get("mechanical_profile") or {}
    surf = l1.get("surface_profile") or {}
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f'<div class="ap-card">'
            f'<div class="ap-card-label">propriet&agrave; meccaniche · {l1.get("mechanical_profile_match")}</div>'
            f'<div class="ap-card-sub">'
            f'Rigidit&agrave; (E): <strong style="color:var(--text);">{mech.get("young_modulus_MPa", "N/A")} MPa</strong><br>'
            f'Resistenza max: <strong style="color:var(--text);">{mech.get("yield_strength_MPa", "N/A")} MPa</strong><br>'
            f'Rilassamento a 15 gg: <strong style="color:var(--text);">{mech.get("stress_decay_day15_percent", "N/A")} %</strong>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="ap-card">'
            f'<div class="ap-card-label">caratteristiche superficiali · {l1.get("surface_profile_match")}</div>'
            f'<div class="ap-card-sub">'
            f'Spessore iniziale: <strong style="color:var(--text);">{surf.get("thickness_pre_mm", "N/A")} mm</strong><br>'
            f'Spessore finale: <strong style="color:var(--text);">{surf.get("thickness_post_mm", "N/A")} mm</strong><br>'
            f'Scarto di adattamento: <strong style="color:var(--text);">{surf.get("gap_mm", "N/A")} mm</strong>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    smoke = l2.get("smoke_profile", {})
    if smoke.get("cigarettes_per_day", 0) > 0:
        st.markdown(
            f'<div class="ap-card" style="margin-top:4px;">'
            f'<div class="ap-card-label">rischio da fumo</div>'
            f'<div class="ap-card-sub">'
            f'Sigarette/giorno: <strong style="color:var(--text);">{smoke.get("cigarettes_per_day")}</strong>&nbsp;&nbsp;'
            f'Livello: <strong style="color:var(--text);">{smoke.get("smoke_surface_risk_level")}</strong>&nbsp;&nbsp;'
            f'Punteggio: <strong style="color:var(--text);">{smoke.get("smoke_surface_risk_score")}</strong>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

# ── Drivers + affidabilità ────────────────────────────────────────────────────
section_title("fattori determinanti")

drivers  = l2.get("drivers", [])
penalties = l2["confidence_summary"].get("penalties", [])

col1, col2 = st.columns(2)
with col1:
    drivers_html = "".join(
        f'<div class="ap-card-sub" style="margin-bottom:4px;">&rarr; {d}</div>'
        for d in drivers
    ) or '<div class="ap-card-sub">Nessun fattore critico.</div>'
    st.markdown(
        f'<div class="ap-card"><div class="ap-card-label">fattori principali</div>{drivers_html}</div>',
        unsafe_allow_html=True,
    )

with col2:
    pen_html = "".join(
        f'<div class="ap-card-sub" style="margin-bottom:4px;">&darr; {p}</div>'
        for p in penalties
    ) or '<div class="ap-card-sub">Nessuna penalità.</div>'
    st.markdown(
        f'<div class="ap-card"><div class="ap-card-label">limiti sull\'affidabilit&agrave;</div>{pen_html}</div>',
        unsafe_allow_html=True,
    )

# ── Note metodologiche ────────────────────────────────────────────────────────
with st.expander("Note sul calcolo", expanded=False):
    notes_html = "".join(
        f'<div class="ap-card-sub" style="margin-bottom:6px;">&bull; {note}</div>'
        for note in l2.get("level2_notes", [])
    )
    st.markdown(f'<div class="ap-card">{notes_html}</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
footer_buttons(
    primary_label="&larr; Modifica parametri",
    primary_page="/Strumento",
    secondary_label="&rarr; Esplora le fonti",
    secondary_page="/Fonti",
)
