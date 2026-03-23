import streamlit as st

st.set_page_config(
    page_title="Aligner Predictor",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
[data-testid="stSidebar"] {display: none;}
[data-testid="collapsedControl"] {display: none;}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1100px;
}

body {
    background: linear-gradient(180deg, #f4f8fc 0%, #eef4fb 100%);
}

.hero {
    background: rgba(255,255,255,0.58);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.4);
    border-radius: 24px;
    padding: 28px;
    margin-bottom: 18px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.card {
    background: rgba(255,255,255,0.58);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.4);
    border-radius: 20px;
    padding: 18px;
    margin-bottom: 14px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.small {
    color: #5f6b7a;
    font-size: 0.95rem;
}
</style>
""", unsafe_allow_html=True)

st.title("🦷 Aligner Aesthetic & Material Predictor")

nav1, nav2, nav3 = st.columns(3)
with nav1:
    st.page_link("Home.py", label="🏠 Home")
with nav2:
    st.page_link("pages/1_Strumento.py", label="🧪 Strumento")
with nav3:
    st.page_link("pages/3_Fonti.py", label="📚 Fonti")

st.markdown('<div class="hero">', unsafe_allow_html=True)
st.subheader("Una webapp per stimare la suscettibilità estetica dei materiali per aligner")
st.write(
    "Questa applicazione integra un motore a due livelli. "
    "Il **livello 1** usa dati strutturati dalla letteratura peer-reviewed per collegare "
    "materiale, polimero, agente pigmentante e proprietà del materiale. "
    "Il **livello 2** sintetizza questi risultati in score esplorativi più facili da leggere."
)
st.markdown(
    '<p class="small">L’obiettivo non è sostituire la misura sperimentale, ma organizzare e rendere interpretabili '
    'i dati disponibili su staining, proprietà meccaniche e caratteristiche superficiali.</p>',
    unsafe_allow_html=True
)

b1, b2 = st.columns(2)
with b1:
    st.page_link("pages/1_Strumento.py", label="Vai allo strumento", icon="🧪")
with b2:
    st.page_link("pages/3_Fonti.py", label="Vai alle fonti", icon="📚")
st.markdown("</div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("1. Input")
    st.write(
        "L’utente inserisce materiale, giorni di utilizzo e numero di esposizioni giornaliere "
        "a caffè, tè, vino rosso, cola e fumo di sigaretta."
    )
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("2. Livello 1")
    st.write(
        "Il motore evidence-based restituisce ΔE stimato dai dati quantitativi disponibili, "
        "polimero, famiglia polimerica, profilo meccanico e profilo superficiale."
    )
    st.markdown("</div>", unsafe_allow_html=True)

with c3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("3. Livello 2")
    st.write(
        "Gli output del livello 1 vengono trasformati in una sintesi numerica: "
        "staining score, mechanical risk, surface risk, global risk e confidence."
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("Come leggere i risultati")
st.write(
    "Il cuore scientifico del sistema resta il livello 1, che si appoggia ai dati presenti nei dataset. "
    "Il livello 2 non aggiunge nuovi dati sperimentali: li sintetizza in modo trasparente per rendere "
    "il confronto tra materiali e profili di esposizione più semplice e intuitivo."
)
st.markdown("</div>", unsafe_allow_html=True)