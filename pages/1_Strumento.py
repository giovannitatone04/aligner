import time
import streamlit as st

st.set_page_config(
    page_title="Strumento",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
[data-testid="stSidebar"] {display: none;}
[data-testid="collapsedControl"] {display: none;}

.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 900px;
}

body {
    background: linear-gradient(180deg, #f4f8fc 0%, #eef4fb 100%);
}

.glass-card {
    background: rgba(255,255,255,0.55);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.35);
    border-radius: 22px;
    padding: 24px;
    margin-bottom: 18px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.section-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 8px;
}

.section-sub {
    font-size: 0.98rem;
    color: #475569;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

st.title("🧪 Strumento di predizione")
st.caption("Inserisci il materiale e il profilo di esposizione. I risultati verranno mostrati in una pagina dedicata.")

nav1, nav2, nav3, nav4 = st.columns(4)
with nav1:
    st.page_link("Home.py", label="🏠 Home")
with nav2:
    st.page_link("pages/1_Strumento.py", label="🧪 Strumento")
with nav3:
    st.page_link("pages/2_Risultati.py", label="📊 Risultati")
with nav4:
    st.page_link("pages/3_Fonti.py", label="📚 Fonti")

brands = [
    "Airnivol",
    "ALL IN",
    "Arc Angel",
    "ClearCorrect",
    "Duran",
    "Durasoft",
    "Erkoloc-Pro",
    "F22 Aligner",
    "F22 Evoflex",
    "Invisalign",
    "Minor Tooth Movement",
    "Nuvola",
]

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Profilo materiale</div>', unsafe_allow_html=True)
st.markdown('<div class="section-sub">Seleziona il sistema di aligner e il tempo di utilizzo considerato nel modello.</div>', unsafe_allow_html=True)

material_brand = st.selectbox("Materiale", brands)
wear_days = st.slider("Giorni di utilizzo", 1, 30, 14)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Abitudini giornaliere</div>', unsafe_allow_html=True)
st.markdown('<div class="section-sub">Inserisci il numero medio di esposizioni quotidiane ai principali agenti pigmentanti.</div>', unsafe_allow_html=True)

coffee_per_day = st.number_input("Caffè / giorno", 0, 20, 0, 1)
tea_per_day = st.number_input("Tè / giorno", 0, 20, 0, 1)
red_wine_per_day = st.number_input("Vino rosso / giorno", 0, 20, 0, 1)
cola_per_day = st.number_input("Cola / giorno", 0, 20, 0, 1)
cigarettes_per_day = st.number_input("Sigarette / giorno", 0, 60, 0, 1)

st.markdown("</div>", unsafe_allow_html=True)

if st.button("Calcola risultati", use_container_width=True):
    st.session_state["model_inputs"] = {
        "material_brand": material_brand,
        "wear_days": wear_days,
        "coffee_per_day": coffee_per_day,
        "tea_per_day": tea_per_day,
        "red_wine_per_day": red_wine_per_day,
        "cola_per_day": cola_per_day,
        "cigarettes_per_day": cigarettes_per_day,
    }

    progress_text = st.empty()
    progress_bar = st.progress(0)

    for i in range(1, 101):
        progress_bar.progress(i)
        if i < 25:
            progress_text.write("Analisi del materiale...")
        elif i < 50:
            progress_text.write("Valutazione della suscettibilità estetica...")
        elif i < 75:
            progress_text.write("Integrazione dei parametri meccanici e superficiali...")
        else:
            progress_text.write("Generazione del profilo finale...")
        time.sleep(0.01)

    progress_text.empty()
    progress_bar.empty()

    st.switch_page("pages/2_Risultati.py")
