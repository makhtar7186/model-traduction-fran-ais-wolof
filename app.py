import streamlit as st
import requests
import time

# ── Configuration de la page ──────────────────────────────────────────────────

st.set_page_config(
    page_title="Français → Wolof | Traducteur",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="collapsed",
)

API_URL = "http://127.0.0.1:8000"

# ── CSS personnalisé ──────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap');

/* Reset & base */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Fond général */
.stApp {
    background: #0e0e12;
    color: #e8e4dc;
}

/* Cacher éléments Streamlit par défaut */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 760px; }

/* ── Hero ── */
.hero {
    text-align: center;
    padding: 3rem 1rem 2rem;
    position: relative;
}
.hero-badge {
    display: inline-block;
    background: rgba(255,180,60,0.12);
    border: 1px solid rgba(255,180,60,0.35);
    color: #ffb43c;
    font-size: 0.72rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    padding: 0.3rem 1rem;
    border-radius: 999px;
    margin-bottom: 1.2rem;
}
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(2.2rem, 6vw, 3.4rem);
    font-weight: 700;
    line-height: 1.15;
    color: #f0ebe0;
    margin: 0 0 0.6rem;
    letter-spacing: -0.01em;
}
.hero-title span {
    color: #ffb43c;
}
.hero-sub {
    color: #7d7a72;
    font-size: 0.95rem;
    font-weight: 300;
    letter-spacing: 0.02em;
}

/* ── Status pill ── */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.78rem;
    font-weight: 500;
    padding: 0.35rem 0.9rem;
    border-radius: 999px;
    margin-bottom: 2rem;
}
.status-ok   { background: rgba(52,211,153,0.1); border:1px solid rgba(52,211,153,0.3); color:#34d399; }
.status-err  { background: rgba(248,113,113,0.1); border:1px solid rgba(248,113,113,0.3); color:#f87171; }
.dot { width:7px; height:7px; border-radius:50%; }
.dot-ok  { background:#34d399; box-shadow:0 0 6px #34d399; }
.dot-err { background:#f87171; box-shadow:0 0 6px #f87171; }

/* ── Carte principale ── */
.card {
    background: #16161d;
    border: 1px solid #2a2a35;
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 1.2rem;
}
.card-label {
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #5a5a6a;
    margin-bottom: 0.6rem;
    font-weight: 500;
}

/* ── Zone de résultat ── */
.result-box {
    background: linear-gradient(135deg, #1a1a24 0%, #16161d 100%);
    border: 1px solid #ffb43c33;
    border-left: 3px solid #ffb43c;
    border-radius: 12px;
    padding: 1.5rem 1.8rem;
    margin-top: 1.2rem;
}
.result-label {
    font-size: 0.68rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #ffb43c99;
    margin-bottom: 0.5rem;
}
.result-text {
    font-family: 'Playfair Display', serif;
    font-size: 1.45rem;
    color: #f0ebe0;
    line-height: 1.5;
    word-break: break-word;
}

/* ── Historique ── */
.hist-item {
    background: #13131a;
    border: 1px solid #22222e;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.7rem;
}
.hist-fr  { font-size: 0.85rem; color: #8888a0; margin-bottom: 0.3rem; }
.hist-wo  { font-size: 1rem; color: #e8e4dc; font-weight: 500; }
.hist-time { font-size: 0.68rem; color: #44444e; margin-top: 0.4rem; }

/* ── Metric cards ── */
.metrics-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.8rem;
    margin-bottom: 1.5rem;
}
.metric-card {
    background: #16161d;
    border: 1px solid #2a2a35;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
}
.metric-val { font-size: 1.6rem; font-weight: 700; color: #ffb43c; font-family: 'Playfair Display', serif; }
.metric-lbl { font-size: 0.68rem; color: #5a5a6a; letter-spacing: 0.1em; text-transform: uppercase; margin-top: 0.2rem; }

/* ── Bouton Streamlit override ── */
.stButton > button {
    background: #ffb43c !important;
    color: #0e0e12 !important;
    font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.6rem 2rem !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.03em !important;
    transition: opacity 0.2s !important;
    width: 100% !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* Slider label */
.stSlider label { color: #7d7a72 !important; font-size: 0.82rem !important; }

/* Text area */
.stTextArea textarea {
    background: #0e0e12 !important;
    border: 1px solid #2a2a35 !important;
    border-radius: 10px !important;
    color: #e8e4dc !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
}
.stTextArea textarea:focus { border-color: #ffb43c66 !important; box-shadow: 0 0 0 2px #ffb43c1a !important; }
</style>
""", unsafe_allow_html=True)

# ── State ─────────────────────────────────────────────────────────────────────

if "history" not in st.session_state:
    st.session_state.history = []
if "total_chars" not in st.session_state:
    st.session_state.total_chars = 0
if "total_translations" not in st.session_state:
    st.session_state.total_translations = 0


# ── Helpers ───────────────────────────────────────────────────────────────────

def check_api_health() -> bool:
    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        return r.status_code == 200 and r.json().get("model_loaded", False)
    except Exception:
        return False


def call_translate(text: str, num_beams: int) -> dict | None:
    try:
        r = requests.post(
            f"{API_URL}/translate",
            json={"text": text, "num_beams": num_beams},
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()
        else:
            st.error(f"Erreur API {r.status_code} : {r.json().get('detail', 'Inconnue')}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Impossible de joindre l'API. Vérifiez que le serveur FastAPI tourne.")
        return None
    except Exception as e:
        st.error(f"Erreur inattendue : {e}")
        return None


# ── Hero ──────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero">
    <div class="hero-badge">🌍 Traduction IA</div>
    <h1 class="hero-title">Français <span>→</span> Wolof</h1>
    <p class="hero-sub">Modèle MarianMT fine-tuné · Traduction neuronale</p>
</div>
""", unsafe_allow_html=True)

# Status API
api_ok = check_api_health()
if api_ok:
    st.markdown('<div style="text-align:center"><span class="status-pill status-ok"><span class="dot dot-ok"></span>API connectée · Modèle prêt</span></div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="text-align:center"><span class="status-pill status-err"><span class="dot dot-err"></span>API hors ligne</span></div>', unsafe_allow_html=True)

# ── Métriques ─────────────────────────────────────────────────────────────────

st.markdown(f"""
<div class="metrics-row">
    <div class="metric-card">
        <div class="metric-val">{st.session_state.total_translations}</div>
        <div class="metric-lbl">Traductions</div>
    </div>
    <div class="metric-card">
        <div class="metric-val">{st.session_state.total_chars}</div>
        <div class="metric-lbl">Caractères</div>
    </div>
    <div class="metric-card">
        <div class="metric-val">{len(st.session_state.history)}</div>
        <div class="metric-lbl">Historique</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Formulaire de traduction ──────────────────────────────────────────────────

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-label">Texte source — Français</div>', unsafe_allow_html=True)

text_input = st.text_area(
    label="",
    placeholder="Entrez votre texte en français ici…",
    height=130,
    key="text_input",
    label_visibility="collapsed",
)

num_beams = st.slider(
    "Qualité de traduction (num_beams)",
    min_value=1, max_value=8, value=4, step=1,
    help="Plus la valeur est élevée, meilleure est la traduction (mais plus lente)."
)

translate_btn = st.button("Traduire →", disabled=not api_ok)
st.markdown('</div>', unsafe_allow_html=True)

# ── Résultat ──────────────────────────────────────────────────────────────────

if translate_btn:
    if not text_input.strip():
        st.warning("⚠️ Veuillez entrer un texte à traduire.")
    else:
        with st.spinner("Traduction en cours…"):
            start = time.time()
            result = call_translate(text_input.strip(), num_beams)
            elapsed = time.time() - start

        if result:
            st.markdown(f"""
            <div class="result-box">
                <div class="result-label">Traduction · Wolof &nbsp;·&nbsp; {elapsed:.2f}s</div>
                <div class="result-text">{result['translated_text']}</div>
            </div>
            """, unsafe_allow_html=True)

            # Mise à jour état
            st.session_state.total_translations += 1
            st.session_state.total_chars += len(text_input.strip())
            st.session_state.history.insert(0, {
                "fr": text_input.strip(),
                "wo": result["translated_text"],
                "time": time.strftime("%H:%M:%S"),
                "elapsed": elapsed,
            })
            st.rerun()

# ── Historique ────────────────────────────────────────────────────────────────

if st.session_state.history:
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div class="card-label" style="margin-top:0.5rem">Historique des traductions</div>', unsafe_allow_html=True)
    with col2:
        if st.button("Effacer", key="clear"):
            st.session_state.history = []
            st.session_state.total_translations = 0
            st.session_state.total_chars = 0
            st.rerun()

    for item in st.session_state.history[:10]:
        st.markdown(f"""
        <div class="hist-item">
            <div class="hist-fr">🇫🇷 {item['fr']}</div>
            <div class="hist-wo">🌍 {item['wo']}</div>
            <div class="hist-time">{item['time']} · {item['elapsed']:.2f}s</div>
        </div>
        """, unsafe_allow_html=True)
