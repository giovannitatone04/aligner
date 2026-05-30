from pathlib import Path

import pandas as pd
import streamlit as st

from components.ui import footer_buttons, inject_css, navbar, page_hero, section_title
from scoring_level2 import (
    DELTAE_SEVERE_THRESHOLD,
    MECH_RANGES,
    PIGMENT_LOAD_SATURATION,
    SCORING_WEIGHTS,
)

st.set_page_config(
    page_title="PolyStain · Fonti",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()
navbar(active="fonti")

page_hero(
    eyebrow="trasparenza metodologica",
    title="Fonti, dataset e parametri",
    subtitle="Tutti i dati primari, i criteri di calcolo e i parametri del modello.",
)

BASE = Path(__file__).resolve().parent.parent


def safe_csv(name: str) -> pd.DataFrame:
    try:
        return pd.read_csv(BASE / name)
    except Exception as e:
        st.error(f"Errore caricamento {name}: {e}")
        return pd.DataFrame()


materials  = safe_csv("materials_master_v2.csv")
staining   = safe_csv("staining_evidence_v2.csv")
mechanical = safe_csv("mechanical_evidence_v2.csv")
surface    = safe_csv("thermoforming_fit_surface_v2.csv")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Materiali", "Staining", "Meccanica", "Superficie", "Parametri modello",
])

with tab1:
    section_title("materials_master_v2.csv")
    cols = [c for c in ["brand", "polymer", "polymer_family", "structure", "source", "notes"]
            if c in materials.columns]
    st.dataframe(materials[cols] if cols else materials, use_container_width=True, hide_index=True)

with tab2:
    section_title("staining_evidence_v2.csv")
    cols = [c for c in ["brand", "polymer_family", "agent", "exposure_time", "deltaE", "source", "notes"]
            if c in staining.columns]
    st.dataframe(staining[cols] if cols else staining, use_container_width=True, hide_index=True)

with tab3:
    section_title("mechanical_evidence_v2.csv")
    cols = [c for c in ["brand", "polymer", "young_modulus_MPa", "yield_strength_MPa",
                         "stress_decay_day15_percent", "source", "notes"]
            if c in mechanical.columns]
    st.dataframe(mechanical[cols] if cols else mechanical, use_container_width=True, hide_index=True)

with tab4:
    section_title("thermoforming_fit_surface_v2.csv")
    cols = [c for c in ["brand", "polymer", "thickness_pre_mm", "thickness_post_mm", "gap_mm", "source", "notes"]
            if c in surface.columns]
    st.dataframe(surface[cols] if cols else surface, use_container_width=True, hide_index=True)
    st.markdown(
        '<div class="ap-card-sub" style="margin-top:12px;color:var(--yellow);">'
        '&#9888; I dati di spessore post-termoformatura e scarto di adattamento non sono disponibili '
        'per la maggior parte dei brand. Il rischio superficiale opera quindi in modalit&agrave; ridotta.'
        '</div>',
        unsafe_allow_html=True,
    )

with tab5:
    section_title("criteri di calcolo")
    st.markdown(
        '<div class="ap-card">'
        '<div class="ap-card-sub">'
        'I pesi qui sotto definiscono quanto ogni componente contribuisce al punteggio finale. '
        'Sono documentati nel file <code>scoring_level2.py</code>.'
        '</div></div>',
        unsafe_allow_html=True,
    )
    weights_df = pd.DataFrame([{"Parametro": k, "Valore": v} for k, v in SCORING_WEIGHTS.items()])
    st.dataframe(weights_df, use_container_width=True, hide_index=True)

    section_title("range di normalizzazione meccanica")
    ranges_df = pd.DataFrame([
        {"Parametro": k, "Min": v["min"], "Max": v["max"], "Fonte": "Albertini et al. 2022"}
        for k, v in MECH_RANGES.items()
    ])
    st.dataframe(ranges_df, use_container_width=True, hide_index=True)

    section_title("altri parametri")
    st.markdown(
        f'<div class="ap-card"><div class="ap-card-sub">'
        f'<strong style="color:var(--text);">Soglia variazione colore severa</strong> = {DELTAE_SEVERE_THRESHOLD}'
        f'&nbsp;&middot;&nbsp; usata per normalizzare il punteggio cromatico<br>'
        f'<strong style="color:var(--text);">Saturazione carico pigmentante</strong> = {PIGMENT_LOAD_SATURATION}'
        f'&nbsp;&middot;&nbsp; eventi totali necessari per raggiungere il massimo del carico<br><br>'
        f'<strong style="color:var(--yellow);">Nota:</strong> i secondi per evento '
        f'sono parametri interni usati per standardizzare le esposizioni in ore cumulative.'
        f'</div></div>',
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="ap-card-sub" style="margin-top:2rem;">'
    'Questa pagina consente di verificare direttamente i dataset che alimentano il modello '
    'e i parametri che governano il calcolo dei punteggi. Per qualsiasi uso accademico o clinico, '
    'fare riferimento alle fonti primarie indicate nella colonna <em>source</em>.'
    '</div>',
    unsafe_allow_html=True,
)

footer_buttons(
    primary_label="&rarr; Vai allo strumento",
    primary_page="/Strumento",
    secondary_label="&larr; Home",
    secondary_page="/",
)
