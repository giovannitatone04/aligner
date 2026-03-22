
import streamlit as st

st.set_page_config(
    page_title="Aligner Predictor",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
.hero {
    background: linear-gradient(135deg, #f8fbff 0%, #eef4fb 100%);
    border: 1px solid #e6edf5;
    border-radius: 22px;
    padding: 28px;
    margin-bottom: 18px;
}
.card {
    background: #ffffff;
    border: 1px solid #e8edf5;
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.small {
    color: #5f6b7a;
    font-size: 0.95rem;
}
</style>
""", unsafe_allow_html=True)

st.title("🦷 Aligner Aesthetic & Material Predictor")

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
st.page_link("pages/1_Strumento.py", label="Vai allo strumento", icon="🧪")
st.page_link("pages/2_Fonti.py", label="Vai alle fonti", icon="📚")
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
