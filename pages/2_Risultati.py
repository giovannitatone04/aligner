import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from pathlib import Path

from predictor_level1_v2 import EvidenceDB, Level1Predictor, UserHabits
from scoring_level2 import build_level2_scores

st.set_page_config(
    page_title="Risultati",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"

st.markdown("""
<style>
[data-testid="stSidebar"] {display: none;}
[data-testid="collapsedControl"] {display: none;}

.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 920px;
}

body {
    background: linear-gradient(180deg, #f4f8fc 0%, #eef4fb 100%);
}

.glass-card {
    background: rgba(255,255,255,0.60);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.42);
    border-radius: 22px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.card-title {
    font-size: 0.92rem;
    color: #64748b;
    margin-bottom: 8px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}

.card-value {
    font-size: 1.9rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 6px;
}

.card-sub {
    font-size: 0.96rem;
    color: #475569;
    line-height: 1.6;
}

.badge {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 700;
    margin-top: 8px;
}

.badge-low {
    background: rgba(34,197,94,0.14);
    color: #166534;
}
.badge-mid {
    background: rgba(245,158,11,0.16);
    color: #92400e;
}
.badge-high {
    background: rgba(239,68,68,0.14);
    color: #991b1b;
}

.section-title {
    font-size: 1.12rem;
    font-weight: 700;
    margin-top: 8px;
    margin-bottom: 10px;
    color: #0f172a;
}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_model():
    db = EvidenceDB(".")
    predictor = Level1Predictor(db)
    return db, predictor


def choose_aligner_image(deltae):
    if deltae is None:
        return ASSETS_DIR / "aligner_clear.png"
    if deltae < 1.2:
        return ASSETS_DIR / "aligner_clear.png"
    elif deltae < 3.0:
        return ASSETS_DIR / "aligner_low.png"
    elif deltae < 5.0:
        return ASSETS_DIR / "aligner_mid.png"
    return ASSETS_DIR / "aligner_high.png"


def run_full_model(predictor, inputs):
    habits = UserHabits(
        material_brand=inputs["material_brand"],
        wear_days=inputs["wear_days"],
        coffee_per_day=inputs["coffee_per_day"],
        tea_per_day=inputs["tea_per_day"],
        red_wine_per_day=inputs["red_wine_per_day"],
        cola_per_day=inputs["cola_per_day"],
        cigarettes_per_day=inputs["cigarettes_per_day"],
    )
    level1_result = predictor.predict(habits)
    level2_result = build_level2_scores(level1_result)
    return {"level1": level1_result, "level2": level2_result}


def risk_badge_class(value):
    if value is None:
        return "badge-mid"
    if value < 25:
        return "badge-low"
    elif value < 60:
        return "badge-mid"
    return "badge-high"


def risk_card_colors(value):
    if value is None:
        return {
            "accent": "#64748b",
            "bg": "#f8fafc",
            "border": "#cbd5e1",
        }
    if value < 25:
        return {
            "accent": "#166534",
            "bg": "#ecfdf5",
            "border": "#86efac",
        }
    elif value < 60:
        return {
            "accent": "#92400e",
            "bg": "#fffbeb",
            "border": "#fcd34d",
        }
    return {
        "accent": "#991b1b",
        "bg": "#fef2f2",
        "border": "#fca5a5",
    }


def score_width(value):
    if value is None:
        return 0
    return max(0, min(100, int(value)))


def build_agents_dataframe(level1_result):
    rows = []
    for row in level1_result.get("agent_predictions", []):
        rows.append({
            "Agente": row.get("agent"),
            "Esposizioni/die": row.get("events_per_day"),
            "Ore cumulative": row.get("total_exposure_hours"),
            "ΔE stimato": row.get("estimated_deltaE"),
            "Severità": row.get("severity"),
            "Match": row.get("matched_on"),
        })
    return pd.DataFrame(rows)


def build_scores_dataframe(level2_result):
    return pd.DataFrame([
        {
            "Indice": "Staining",
            "Valore": level2_result["staining_summary"].get("staining_score"),
            "Classe": level2_result["staining_summary"].get("staining_risk_class"),
        },
        {
            "Indice": "Mechanical",
            "Valore": level2_result["mechanical_summary"].get("mechanical_risk_score"),
            "Classe": level2_result["mechanical_summary"].get("mechanical_risk_class"),
        },
        {
            "Indice": "Surface",
            "Valore": level2_result["surface_summary"].get("surface_risk_score"),
            "Classe": level2_result["surface_summary"].get("surface_risk_class"),
        },
        {
            "Indice": "Global",
            "Valore": level2_result["global_summary"].get("global_risk_score"),
            "Classe": level2_result["global_summary"].get("global_risk_class"),
        },
        {
            "Indice": "Confidence",
            "Valore": level2_result["confidence_summary"].get("confidence_score"),
            "Classe": level2_result["confidence_summary"].get("confidence_level"),
        },
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
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.bar(df["Agente"], df["ΔE"])
    ax.set_title("Contributo dei singoli agenti al ΔE")
    ax.set_xlabel("Agente")
    ax.set_ylabel("ΔE stimato")
    ax.grid(axis="y", alpha=0.25)
    return fig


def plot_level2_scores(level2_result):
    df = build_scores_dataframe(level2_result)
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.bar(df["Indice"], df["Valore"])
    ax.set_title("Sintesi degli score di livello 2")
    ax.set_xlabel("Indice")
    ax.set_ylabel("Valore (0-100)")
    ax.set_ylim(0, 100)
    ax.grid(axis="y", alpha=0.25)
    plt.xticks(rotation=15, ha="right")
    return fig


def render_score_card(title, value, risk_class):
    colors = risk_card_colors(value)
    st.markdown(
        f"""
        <div style="
            background: {colors['bg']};
            border: 1px solid {colors['border']};
            border-radius: 22px;
            padding: 18px;
            margin-bottom: 16px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
        ">
            <div style="
                font-size: 0.9rem;
                font-weight: 700;
                color: {colors['accent']};
                text-transform: uppercase;
                margin-bottom: 6px;
            ">
                {title}
            </div>
            <div style="
                font-size: 1.8rem;
                font-weight: 800;
                color: {colors['accent']};
                margin-bottom: 6px;
            ">
                {value}
            </div>
            <div style="font-size: 0.95rem; color: #475569;">
                Classe: {risk_class}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(score_width(value) / 100.0)


def staining_visual_style(deltae):
    if deltae is None:
        return "neutral"
    if deltae < 1.2:
        return "minimal"
    elif deltae < 3.0:
        return "mild"
    elif deltae < 5.0:
        return "marked"
    return "very_marked"


def render_staining_visual(deltae):
    level = staining_visual_style(deltae)

    st.markdown(
        """
        <div class="glass-card">
            <div class="card-title">Visualizzazione illustrativa dello staining</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if level == "minimal":
        st.success("Intensità visiva stimata: minima")
    elif level == "mild":
        st.warning("Intensità visiva stimata: lieve")
    elif level == "marked":
        st.warning("Intensità visiva stimata: marcata")
    elif level == "very_marked":
        st.error("Intensità visiva stimata: molto marcata")
    else:
        st.info("Intensità visiva stimata: neutra")

    st.caption("Visualizzazione illustrativa, non simulazione clinica reale.")


st.title("📊 Risultati")
st.caption("Output del livello 1 + sintesi del livello 2")

nav1, nav2, nav3, nav4 = st.columns(4)
with nav1:
    st.page_link("Home.py", label="🏠 Home")
with nav2:
    st.page_link("pages/1_Strumento.py", label="🧪 Strumento")
with nav3:
    st.page_link("pages/2_Risultati.py", label="📊 Risultati")
with nav4:
    st.page_link("pages/3_Fonti.py", label="📚 Fonti")

if "model_inputs" not in st.session_state:
    st.warning("Non ci sono input salvati. Vai prima alla pagina Strumento.")
    st.stop()

db, predictor = load_model()
results = run_full_model(predictor, st.session_state["model_inputs"])
level1 = results["level1"]
level2 = results["level2"]

global_score = level2["global_summary"].get("global_risk_score")
global_class = level2["global_summary"].get("global_risk_class")
global_colors = risk_card_colors(global_score)

st.markdown(
    f"""
    <div style="
        background: {global_colors['bg']};
        border: 1px solid {global_colors['border']};
        border-radius: 24px;
        padding: 22px;
        margin-bottom: 12px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    ">
        <div style="
            font-size: 0.95rem;
            font-weight: 700;
            color: {global_colors['accent']};
            text-transform: uppercase;
            letter-spacing: 0.4px;
            margin-bottom: 8px;
        ">
            Risultato principale
        </div>
        <div style="
            font-size: 2.2rem;
            font-weight: 800;
            color: {global_colors['accent']};
            margin-bottom: 8px;
        ">
            Global risk: {global_score}
        </div>
        <div style="font-size: 1rem; color: #334155; line-height: 1.7;">
            <b>Classe:</b> {global_class}<br>
            <b>Materiale:</b> {level1.get('material_brand')}<br>
            <b>Polimero:</b> {level1.get('polymer')}<br>
            <b>ΔE totale:</b> {level1.get('total_estimated_deltaE_numeric_agents_only')}<br>
            <b>Confidence:</b> {level2['confidence_summary'].get('confidence_score')} ({level2['confidence_summary'].get('confidence_level')})
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.progress(score_width(global_score) / 100.0)

with st.popover("ℹ️ Informazioni sul risultato principale"):
    st.write("**Cos'è:**")
    st.write(
        "Il global risk è uno score sintetico che integra componenti estetiche (staining), "
        "meccaniche e superficiali del materiale."
    )

    st.write("**Implicazioni:**")
    st.write(
        "Valori più elevati suggeriscono una maggiore probabilità di compromissione complessiva "
        "del materiale durante l’utilizzo, sia in termini estetici che di performance."
    )

deltae_total = level1.get("total_estimated_deltaE_numeric_agents_only")
img_path = choose_aligner_image(deltae_total)

st.markdown('<div class="section-title">Visualizzazione illustrativa dello staining</div>', unsafe_allow_html=True)

if img_path.exists():
    st.image(str(img_path), caption="Visualizzazione illustrativa dello staining", use_container_width=True)
else:
    st.warning(f"Immagine non trovata: {img_path}")

with st.popover("ℹ️ Informazioni sulla visualizzazione dello staining"):
    st.write("**Cos'è:**")
    st.write(
        "Questa rappresentazione visiva mostra in modo qualitativo il livello di discolorazione stimato, come supporto alla lettura del risultato."
    )

render_score_card(
    "Staining",
    level2["staining_summary"].get("staining_score"),
    level2["staining_summary"].get("staining_risk_class"),
)

with st.popover("ℹ️ Informazioni su Staining"):
    st.write("**Cos'è:**")
    st.write(
        "Lo staining score rappresenta il rischio estetico complessivo, "
        "basato sulla variazione cromatica (ΔE) stimata e sull'esposizione agli agenti pigmentanti."
    )

    st.write("**Implicazioni:**")
    st.write(
        "Valori elevati indicano maggiore rischio di discolorazione visibile dell’aligner, "
        "con possibile impatto sull’estetica durante il trattamento."
    )

render_score_card(
    "Mechanical",
    level2["mechanical_summary"].get("mechanical_risk_score"),
    level2["mechanical_summary"].get("mechanical_risk_class"),
)

with st.popover("ℹ️ Informazioni su Mechanical"):
    st.write("**Cos'è:**")
    st.write(
        "Il mechanical risk score sintetizza la stabilità meccanica del materiale "
        "utilizzando parametri come modulo elastico, resistenza e stress decay."
    )

    st.write("**Implicazioni:**")
    st.write(
        "Valori elevati possono indicare maggiore perdita di forza nel tempo o minore "
        "stabilità del materiale, con potenziale riduzione dell’efficacia biomeccanica."
    )

render_score_card(
    "Surface",
    level2["surface_summary"].get("surface_risk_score"),
    level2["surface_summary"].get("surface_risk_class"),
)

with st.popover("ℹ️ Informazioni su Surface"):
    st.write("**Cos'è:**")
    st.write(
        "Il surface risk score descrive le caratteristiche superficiali del materiale, "
        "inclusi spessore post-termoformatura e adattamento (gap)."
    )

    st.write("**Implicazioni:**")
    st.write(
        "Valori elevati possono favorire accumulo di pigmenti e ridurre la precisione "
        "di adattamento dell’aligner, influenzando sia estetica che performance."
    )

smoke = level2.get("smoke_profile", {})
mech = level1.get("mechanical_profile") or {}
surf = level1.get("surface_profile") or {}

st.markdown('<div class="section-title">Dettaglio agenti</div>', unsafe_allow_html=True)
st.dataframe(build_agents_dataframe(level1), use_container_width=True, hide_index=True)
fig1 = plot_agent_deltae(level1)
if fig1 is not None:
    st.pyplot(fig1)

with st.popover("ℹ️ Informazioni sul dettaglio agenti"):
    st.write("**Cos'è:**")
    st.write(
        "Questa tabella mostra il contributo dei singoli agenti pigmentanti al ΔE totale."
    )

    st.write("**Implicazioni:**")
    st.write(
        "Permette di identificare quali abitudini contribuiscono maggiormente alla discolorazione, "
        "supportando eventuali strategie di riduzione del rischio."
    )

st.markdown(
    f"""
    <div class="glass-card">
        <div class="card-title">Profilo meccanico del materiale</div>
        <div class="card-sub">
            <b>Young modulus:</b> {mech.get('young_modulus_MPa', 'N/A')} MPa<br>
            <b>Yield strength:</b> {mech.get('yield_strength_MPa', 'N/A')} MPa<br>
            <b>Stress decay 15d:</b> {mech.get('stress_decay_day15_percent', 'N/A')} %<br>
            <b>Match:</b> {level1.get('mechanical_profile_match')}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.popover("ℹ️ Informazioni sul profilo meccanico"):
    st.write("**Cos'è:**")
    st.write(
        "Raccolta dei parametri meccanici del materiale derivati dalla letteratura o da proxy polimerici."
    )

    st.write("**Implicazioni:**")
    st.write(
        "Differenze nei parametri possono riflettersi in variazioni nella risposta del materiale "
        "durante il trattamento ortodontico."
    )

st.markdown(
    f"""
    <div class="glass-card">
        <div class="card-title">Profilo superficiale</div>
        <div class="card-sub">
            <b>Thickness pre:</b> {surf.get('thickness_pre_mm', 'N/A')} mm<br>
            <b>Thickness post:</b> {surf.get('thickness_post_mm', 'N/A')} mm<br>
            <b>Gap:</b> {surf.get('gap_mm', 'N/A')} mm<br>
            <b>Match:</b> {level1.get('surface_profile_match')}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.popover("ℹ️ Informazioni sul profilo superficiale"):
    st.write("**Cos'è:**")
    st.write(
        "Descrive le caratteristiche geometriche e di adattamento dell’aligner dopo termoformatura."
    )

    st.write("**Implicazioni:**")
    st.write(
        "Può influenzare sia la distribuzione delle forze che la suscettibilità alla pigmentazione."
    )

st.markdown(
    f"""
    <div class="glass-card">
        <div class="card-title">Smoke profile</div>
        <div class="card-value">{smoke.get('smoke_surface_risk_score', 'N/A')}</div>
        <div class="card-sub">
            <b>Sigarette/die:</b> {smoke.get('cigarettes_per_day', 'N/A')}<br>
            <b>Totale sigarette:</b> {smoke.get('total_cigarettes', 'N/A')}<br>
            <b>Rischio superficiale:</b> {smoke.get('smoke_surface_risk_level', 'N/A')}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.popover("ℹ️ Informazioni su Smoke profile"):
    st.write("**Cos'è:**")
    st.write(
        "Il fumo è trattato come fattore superficiale che contribuisce alla pigmentazione."
    )

    st.write("**Implicazioni:**")
    st.write(
        "Un’elevata esposizione può aumentare la discolorazione anche in assenza di dati ΔE diretti."
    )

st.markdown('<div class="section-title">Sintesi degli score</div>', unsafe_allow_html=True)
st.dataframe(build_scores_dataframe(level2), use_container_width=True, hide_index=True)
fig2 = plot_level2_scores(level2)
if fig2 is not None:
    st.pyplot(fig2)

with st.popover("ℹ️ Informazioni sulla sintesi degli score"):
    st.write("**Cos'è:**")
    st.write(
        "Tabella riassuntiva degli score del livello 2."
    )

    st.write("**Implicazioni:**")
    st.write(
        "Permette un confronto rapido tra le diverse dimensioni del comportamento del materiale."
    )

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">Driver principali</div>', unsafe_allow_html=True)
drivers = level2.get("drivers", [])
if drivers:
    for d in drivers:
        st.write(f"• {d}")
else:
    st.write("Nessun driver principale evidenziato.")
st.markdown('</div>', unsafe_allow_html=True)

with st.popover("ℹ️ Informazioni sui driver"):
    st.write("**Cos'è:**")
    st.write(
        "I driver principali sono i fattori che influenzano maggiormente il risultato."
    )

    st.write("**Implicazioni:**")
    st.write(
        "Aiutano a capire quali variabili modificare per ridurre il rischio complessivo."
    )

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">Note metodologiche</div>', unsafe_allow_html=True)
for note in level2.get("level2_notes", []):
    st.write(f"• {note}")
st.markdown('</div>', unsafe_allow_html=True)

with st.popover("ℹ️ Informazioni sulle note metodologiche"):
    st.write("**Cos'è:**")
    st.write(
        "Descrizione delle assunzioni e dei limiti del modello."
    )

    st.write("**Implicazioni:**")
    st.write(
        "I risultati devono essere interpretati come supporto decisionale e non come misura clinica diretta."
    )