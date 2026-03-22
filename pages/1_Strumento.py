
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from predictor_level1_v2 import EvidenceDB, Level1Predictor, UserHabits
from scoring_level2 import build_level2_scores

st.set_page_config(
    page_title="Strumento",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {
    background: #f7f9fc;
    border: 1px solid #e6ebf2;
    padding: 14px;
    border-radius: 16px;
}
.card {
    background: #ffffff;
    border: 1px solid #e8edf5;
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_model():
    db = EvidenceDB(".")
    predictor = Level1Predictor(db)
    return db, predictor

def run_full_model(
    predictor,
    material_brand: str,
    wear_days: int,
    coffee_per_day: int,
    tea_per_day: int,
    red_wine_per_day: int,
    cola_per_day: int,
    cigarettes_per_day: int,
):
    habits = UserHabits(
        material_brand=material_brand,
        wear_days=wear_days,
        coffee_per_day=coffee_per_day,
        tea_per_day=tea_per_day,
        red_wine_per_day=red_wine_per_day,
        cola_per_day=cola_per_day,
        cigarettes_per_day=cigarettes_per_day,
    )
    level1_result = predictor.predict(habits)
    level2_result = build_level2_scores(level1_result)
    return {"level1": level1_result, "level2": level2_result}

def build_agents_dataframe(level1_result):
    rows = []
    for row in level1_result.get("agent_predictions", []):
        rows.append({
            "Agente": row.get("agent"),
            "Esposizioni/die": row.get("events_per_day"),
            "Secondi/esposizione": row.get("seconds_per_event"),
            "Ore cumulative": row.get("total_exposure_hours"),
            "ΔE stimato": row.get("estimated_deltaE"),
            "Severità": row.get("severity"),
            "Match": row.get("matched_on"),
        })
    return pd.DataFrame(rows)

def build_scores_dataframe(level2_result):
    return pd.DataFrame([
        {"Indice": "Staining score", "Valore": level2_result["staining_summary"].get("staining_score"), "Classe": level2_result["staining_summary"].get("staining_risk_class")},
        {"Indice": "Mechanical risk", "Valore": level2_result["mechanical_summary"].get("mechanical_risk_score"), "Classe": level2_result["mechanical_summary"].get("mechanical_risk_class")},
        {"Indice": "Surface risk", "Valore": level2_result["surface_summary"].get("surface_risk_score"), "Classe": level2_result["surface_summary"].get("surface_risk_class")},
        {"Indice": "Global risk", "Valore": level2_result["global_summary"].get("global_risk_score"), "Classe": level2_result["global_summary"].get("global_risk_class")},
        {"Indice": "Confidence", "Valore": level2_result["confidence_summary"].get("confidence_score"), "Classe": level2_result["confidence_summary"].get("confidence_level")},
    ])

def plot_agent_deltae(level1_result):
    rows = []
    for row in level1_result.get("agent_predictions", []):
        dE = row.get("estimated_deltaE")
        if dE is not None:
            rows.append((row.get("agent"), float(dE)))
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["Agente", "ΔE"])
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(df["Agente"], df["ΔE"])
    ax.set_title("Contributo dei singoli agenti al ΔE")
    ax.set_xlabel("Agente")
    ax.set_ylabel("ΔE stimato")
    ax.grid(axis="y", alpha=0.25)
    return fig

def plot_level2_scores(level2_result):
    df = build_scores_dataframe(level2_result)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(df["Indice"], df["Valore"])
    ax.set_title("Sintesi degli score di livello 2")
    ax.set_xlabel("Indice")
    ax.set_ylabel("Valore (0-100)")
    ax.set_ylim(0, 100)
    ax.grid(axis="y", alpha=0.25)
    plt.xticks(rotation=15, ha="right")
    return fig

db, predictor = load_model()

with st.sidebar:
    st.title("🧪 Strumento")
    st.page_link("Home.py", label="Torna alla home", icon="🏠")
    st.page_link("pages/2_Fonti.py", label="Vai alle fonti", icon="📚")
    st.markdown("---")
    brands = db.list_available_brands()
    material_brand = st.selectbox("Materiale", brands)
    wear_days = st.slider("Giorni di utilizzo", 1, 30, 14)
    st.markdown("**Abitudini giornaliere**")
    coffee_per_day = st.number_input("Caffè/die", 0, 20, 0, 1)
    tea_per_day = st.number_input("Tè/die", 0, 20, 0, 1)
    red_wine_per_day = st.number_input("Vino rosso/die", 0, 20, 0, 1)
    cola_per_day = st.number_input("Cola/die", 0, 20, 0, 1)
    cigarettes_per_day = st.number_input("Sigarette/die", 0, 60, 0, 1)
    run_button = st.button("Calcola predizione", use_container_width=True)

st.title("Strumento di predizione")
st.caption("Output del livello 1 + sintesi del livello 2")

if run_button:
    try:
        results = run_full_model(
            predictor=predictor,
            material_brand=material_brand,
            wear_days=wear_days,
            coffee_per_day=coffee_per_day,
            tea_per_day=tea_per_day,
            red_wine_per_day=red_wine_per_day,
            cola_per_day=cola_per_day,
            cigarettes_per_day=cigarettes_per_day,
        )
        level1 = results["level1"]
        level2 = results["level2"]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Materiale", level1.get("material_brand"))
        m2.metric("Polimero", level1.get("polymer"))
        m3.metric("ΔE totale", level1.get("total_estimated_deltaE_numeric_agents_only"))
        m4.metric("Global risk", level2["global_summary"].get("global_risk_score"))

        left, right = st.columns([1.2, 0.8])

        with left:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Livello 1 — Output evidence-based")
            st.write({
                "brand": level1.get("material_brand"),
                "polymer": level1.get("polymer"),
                "polymer_family": level1.get("polymer_family"),
                "structure": level1.get("structure"),
                "wear_days": level1.get("wear_days"),
            })
            st.dataframe(build_agents_dataframe(level1), use_container_width=True, hide_index=True)
            fig1 = plot_agent_deltae(level1)
            if fig1 is not None:
                st.pyplot(fig1)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Profili del materiale")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Profilo meccanico**")
                st.json(level1.get("mechanical_profile") or {})
                st.caption(f"Match: {level1.get('mechanical_profile_match')}")
            with c2:
                st.markdown("**Profilo superficie / termoformatura**")
                st.json(level1.get("surface_profile") or {})
                st.caption(f"Match: {level1.get('surface_profile_match')}")
            st.markdown('</div>', unsafe_allow_html=True)

        with right:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Livello 2 — Sintesi")
            s1, s2 = st.columns(2)
            s1.metric("Staining", level2["staining_summary"].get("staining_score"))
            s2.metric("Mechanical", level2["mechanical_summary"].get("mechanical_risk_score"))
            s3, s4 = st.columns(2)
            s3.metric("Surface", level2["surface_summary"].get("surface_risk_score"))
            s4.metric("Confidence", level2["confidence_summary"].get("confidence_score"))
            st.dataframe(build_scores_dataframe(level2), use_container_width=True, hide_index=True)
            fig2 = plot_level2_scores(level2)
            st.pyplot(fig2)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Driver principali")
            drivers = level2.get("drivers", [])
            if drivers:
                for d in drivers:
                    st.write(f"• {d}")
            else:
                st.write("Nessun driver principale evidenziato.")
            st.markdown("**Smoke profile**")
            st.json(level2.get("smoke_profile") or {})
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Errore durante la predizione: {e}")
else:
    st.info("Inserisci gli input nella barra laterale e premi **Calcola predizione**.")
