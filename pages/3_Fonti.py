import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Fonti",
    page_icon="📚",
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
    max-width: 1100px;
}

body {
    background: linear-gradient(180deg, #f4f8fc 0%, #eef4fb 100%);
}

.glass-card {
    background: rgba(255,255,255,0.58);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.4);
    border-radius: 22px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}
</style>
""", unsafe_allow_html=True)

st.title("📚 Fonti e dataset usati")
st.caption("Pagina dedicata alla base dati e alle fonti presenti nei CSV del progetto.")

nav1, nav2, nav3, nav4 = st.columns(4)
with nav1:
    st.page_link("Home.py", label="🏠 Home")
with nav2:
    st.page_link("pages/1_Strumento.py", label="🧪 Strumento")
with nav3:
    st.page_link("pages/2_Risultati.py", label="📊 Risultati")
with nav4:
    st.page_link("pages/3_Fonti.py", label="📚 Fonti")

def load_csv(name):
    return pd.read_csv(name)

materials = load_csv("materials_master_v2.csv")
staining = load_csv("staining_evidence_v2.csv")
mechanical = load_csv("mechanical_evidence_v2.csv")
surface = load_csv("thermoforming_fit_surface_v2.csv")

tab1, tab2, tab3, tab4 = st.tabs([
    "Materiali",
    "Staining",
    "Meccanica",
    "Superficie / termoformatura"
])

with tab1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Dataset materiali")
    cols = [c for c in ["brand", "polymer", "polymer_family", "structure", "source", "notes"] if c in materials.columns]
    st.dataframe(materials[cols], use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Dataset staining")
    cols = [c for c in ["brand", "polymer_family", "agent", "exposure_time", "deltaE", "source", "notes"] if c in staining.columns]
    st.dataframe(staining[cols], use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Dataset meccanica")
    cols = [c for c in ["brand", "polymer", "young_modulus_MPa", "yield_strength_MPa", "stress_decay_day15_percent", "source", "notes"] if c in mechanical.columns]
    st.dataframe(mechanical[cols], use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Dataset superficie / termoformatura")
    cols = [c for c in ["brand", "polymer", "thickness_pre_mm", "thickness_post_mm", "gap_mm", "source", "notes"] if c in surface.columns]
    st.dataframe(surface[cols], use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.write(
    "Questa pagina permette di verificare direttamente i dataset che alimentano il livello 1. "
    "La webapp principale usa questi dati per la stima del ΔE e per la costruzione dei profili "
    "meccanici e superficiali del materiale."
)