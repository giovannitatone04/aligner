
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Fonti",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Fonti e dataset usati")
st.caption("Pagina dedicata alla base dati e alle fonti presenti nei CSV del progetto.")

with st.sidebar:
    st.page_link("Home.py", label="Torna alla home", icon="🏠")
    st.page_link("pages/1_Strumento.py", label="Vai allo strumento", icon="🧪")

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
    st.subheader("Dataset materiali")
    cols = [c for c in ["brand", "polymer", "polymer_family", "structure", "source", "notes"] if c in materials.columns]
    st.dataframe(materials[cols], use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Dataset staining")
    cols = [c for c in ["brand", "polymer_family", "agent", "exposure_time", "deltaE", "source", "notes"] if c in staining.columns]
    st.dataframe(staining[cols], use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Dataset meccanica")
    cols = [c for c in ["brand", "polymer", "young_modulus_MPa", "yield_strength_MPa", "stress_decay_day15_percent", "source", "notes"] if c in mechanical.columns]
    st.dataframe(mechanical[cols], use_container_width=True, hide_index=True)

with tab4:
    st.subheader("Dataset superficie / termoformatura")
    cols = [c for c in ["brand", "polymer", "thickness_pre_mm", "thickness_post_mm", "gap_mm", "source", "notes"] if c in surface.columns]
    st.dataframe(surface[cols], use_container_width=True, hide_index=True)

st.markdown("---")
st.write(
    "Questa pagina permette di verificare direttamente i dataset che alimentano il livello 1. "
    "La webapp principale usa questi dati per la stima del ΔE e per la costruzione dei profili "
    "meccanici e superficiali del materiale."
)
