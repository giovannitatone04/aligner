import streamlit as st
import streamlit.components.v1 as components
from components.ui import inject_css, navbar, section_title, step_list, footer_buttons

st.set_page_config(
    page_title="PolyStain",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PRODUCT_NAME = "PolyStain"

inject_css()
navbar(active="home")

# ── Hero: two-column layout ─────────────────────────────────────────────────
col_text, col_chart = st.columns([1, 1], gap="large")

with col_text:
    st.markdown(
        f"""<div class="ap-hero">
          <div class="ap-hero-eyebrow">v2 · evidence-based
          <h1>{PRODUCT_NAME}<br><em>Analisi predittiva</em></h1>
          <p>
            Valuta quanto gli aligner ortodontici sono soggetti a macchiarsi e a perdere
            resistenza nel tempo, combinando il tipo di materiale con le abitudini quotidiane
            del paziente.
          </p>
        </div>""",
        unsafe_allow_html=True,
    )

with col_chart:
    de_chart_html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: transparent;
    font-family: 'DM Mono', monospace;
    color: rgba(230,222,210,0.95);
    padding: 8px 0;
  }
  .chart-title {
    font-size: 0.6rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.3);
    margin-bottom: 14px;
  }
  .bar-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
  }
  .bar-label {
    font-size: 0.62rem;
    color: rgba(255,255,255,0.4);
    width: 72px;
    text-align: right;
    flex-shrink: 0;
    letter-spacing: 0.04em;
  }
  .bar-track {
    flex: 1;
    height: 3px;
    background: rgba(255,255,255,0.07);
    border-radius: 3px;
    overflow: hidden;
  }
  .bar-fill {
    height: 100%;
    border-radius: 3px;
    width: 0%;
    transition: width 1s cubic-bezier(0.22, 1, 0.36, 1);
  }
  .bar-value {
    font-size: 0.62rem;
    color: rgba(210,185,140,0.7);
    width: 30px;
    text-align: left;
    flex-shrink: 0;
  }
  .bar-fill { background: rgba(210,185,140,1); }

  @media (prefers-color-scheme: light) {
    body        { color: rgba(30,25,15,0.85); }
    .chart-title{ color: rgba(30,25,15,0.45); }
    .bar-label  { color: rgba(30,25,15,0.55); }
    .bar-value  { color: rgba(120,88,30,0.85); }
    .bar-track  { background: rgba(0,0,0,0.10); }
    .bar-fill   { background: rgba(120,88,30,1); }
  }
</style>
</head>
<body>
<div class="chart-title">delta-E stimato — Invisalign · 14 giorni</div>
<div class="bar-row">
  <div class="bar-label">caffe x2</div>
  <div class="bar-track"><div class="bar-fill" id="b1"></div></div>
  <div class="bar-value" id="v1">0.0</div>
</div>
<div class="bar-row">
  <div class="bar-label">te x1</div>
  <div class="bar-track"><div class="bar-fill" id="b2"></div></div>
  <div class="bar-value" id="v2">0.0</div>
</div>
<div class="bar-row">
  <div class="bar-label">vino rosso</div>
  <div class="bar-track"><div class="bar-fill" id="b3"></div></div>
  <div class="bar-value" id="v3">0.0</div>
</div>
<div class="bar-row">
  <div class="bar-label">cola x1</div>
  <div class="bar-track"><div class="bar-fill" id="b4"></div></div>
  <div class="bar-value" id="v4">0.0</div>
</div>
<script>
var data = [
  { id: "b1", vid: "v1", pct: 72, val: 3.6 },
  { id: "b2", vid: "v2", pct: 52, val: 2.6 },
  { id: "b3", vid: "v3", pct: 88, val: 4.4 },
  { id: "b4", vid: "v4", pct: 34, val: 1.7 },
];
function animCount(el, target, duration) {
  var start = performance.now();
  function step(now) {
    var t = Math.min((now - start) / duration, 1);
    var ease = 1 - Math.pow(1 - t, 3);
    el.textContent = (ease * target).toFixed(1);
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}
window.addEventListener("load", function() {
  setTimeout(function() {
    data.forEach(function(d, i) {
      var bar = document.getElementById(d.id);
      var val = document.getElementById(d.vid);
      setTimeout(function() {
        bar.style.width = d.pct + "%";
        animCount(val, d.val, 900);
      }, i * 120);
    });
  }, 200);
});
</script>
</body>
</html>"""
    components.html(de_chart_html, height=200)

# ── How it works ─────────────────────────────────────────────────────────────
section_title("come funziona")

step_list([
    {
        "tag": "01 · input",
        "title": "Profilo paziente",
        "body": (
            "Seleziona il materiale dell'aligner e inserisci i giorni di utilizzo. "
            "Indica la frequenza giornaliera di esposizione a caff&egrave;, t&egrave;, "
            "vino rosso, cola e fumo."
        ),
    },
    {
        "tag": "02 · analisi",
        "title": "Dati dalla letteratura",
        "body": (
            "Il modello combina la variazione di colore (&Delta;E) per ciascun agente cromogeno, "
            "le propriet&agrave; meccaniche e la rugosit&agrave; superficiale del materiale, "
            "ricavate da studi pubblicati."
        ),
    },
    {
        "tag": "03 · punteggi",
        "title": "Rischio sintetico",
        "body": (
            "Vengono calcolati quattro indici su scala 0&ndash;100: rischio cromatico, meccanico, "
            "superficiale e globale. Un indicatore di affidabilit&agrave; segnala se i dati "
            "si basano su misure dirette o su stime."
        ),
    },
])

# ── Footer ───────────────────────────────────────────────────────────────────
footer_buttons(
    primary_label="&rarr; Vai allo strumento",
    primary_page="/Strumento",
    secondary_label="&rarr; Esplora le fonti",
    secondary_page="/Fonti",
)
