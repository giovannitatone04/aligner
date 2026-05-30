import time
import streamlit as st
from components.ui import inject_css, navbar, page_hero, section_title

st.set_page_config(
    page_title="PolyStain · Strumento",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()
navbar(active="strumento")

page_hero(
    eyebrow="strumento di predizione",
    title="Profilo materiale &amp; esposizione",
    subtitle="Inserisci il sistema di aligner e le abitudini del paziente.",
)

brands = [
    "Airnivol", "ALL IN", "Arc Angel", "ClearCorrect", "Duran",
    "Durasoft", "Erkoloc-Pro", "F22 Aligner", "F22 Evoflex",
    "Invisalign", "Minor Tooth Movement", "Nuvola",
]

section_title("materiale")
material_brand = st.selectbox("Sistema aligner", brands, label_visibility="collapsed")
wear_days = st.slider("Giorni di utilizzo", 1, 30, 14,
                      help="Durata stimata dell'utilizzo continuo dell'aligner")

section_title("esposizione giornaliera")
st.markdown(
    '<div class="ap-card-sub" style="margin-bottom:12px;">'
    'Numero medio di esposizioni quotidiane ai principali agenti coloranti.'
    '</div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)
with col1:
    coffee_per_day = st.number_input("Caffè / die", 0, 20, 0, 1)
    tea_per_day = st.number_input("Tè / die", 0, 20, 0, 1)
    red_wine_per_day = st.number_input("Vino rosso / die", 0, 20, 0, 1)
with col2:
    cola_per_day = st.number_input("Cola / die", 0, 20, 0, 1)
    cigarettes_per_day = st.number_input("Sigarette / die", 0, 60, 0, 1)

st.markdown("<br>", unsafe_allow_html=True)

if st.button("→ Calcola risultati", use_container_width=True):
    st.session_state["model_inputs"] = {
        "material_brand":     material_brand,
        "wear_days":          wear_days,
        "coffee_per_day":     coffee_per_day,
        "tea_per_day":        tea_per_day,
        "red_wine_per_day":   red_wine_per_day,
        "cola_per_day":       cola_per_day,
        "cigarettes_per_day": cigarettes_per_day,
    }

    progress_text = st.empty()
    progress_bar = st.progress(0)
    messages = [
        "Analisi del materiale...",
        "Valutazione suscettibilità estetica...",
        "Integrazione parametri meccanici...",
        "Generazione profilo finale...",
    ]
    for i in range(1, 101):
        progress_bar.progress(i)
        progress_text.markdown(
            f'<span style="font-family:var(--font-ui);font-size:0.78rem;color:var(--accent);">'
            f'{messages[min(i // 25, 3)]}</span>',
            unsafe_allow_html=True,
        )
        time.sleep(0.008)

    progress_text.empty()
    progress_bar.empty()
    st.switch_page("pages/2_Risultati.py")

