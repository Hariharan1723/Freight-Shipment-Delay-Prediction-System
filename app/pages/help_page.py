"""
app/pages/help_page.py
======================
Full-page help guide for the Freight Delay Prediction tool.
"Close & Return" navigates back to app.py using st.switch_page().

Place this file in:  app/pages/help_page.py
"""

import sys
import base64
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

st.set_page_config(
    page_title="Help — Freight Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR  = Path(__file__).resolve().parents[1]   # app/
IMAGE_DIR = BASE_DIR / "images"
bg_path   = IMAGE_DIR / "bg.jpg"
logo_path = IMAGE_DIR / "logo.png"

# ── Background image ──────────────────────────────────────────────────────────
with open(bg_path, "rb") as _f:
    BG_B64 = base64.b64encode(_f.read()).decode()

# ── Page styles ───────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

/* Background */
.stApp {{
    background-image     : url("data:image/jpg;base64,{BG_B64}") !important;
    background-size      : cover !important;
    background-position  : center !important;
    background-attachment: fixed !important;
}}

[data-testid="stSidebar"]    {{ display: none !important; }}
[data-testid="stDecoration"] {{ display: none !important; }}

.block-container {{
    padding-top    : 2rem !important;
    padding-bottom : 2rem !important;
    max-width      : 1100px !important;
    margin         : 0 auto;
}}

/* Close button */
div.stButton > button {{
    background-color : #0b3d91 !important;
    color            : white !important;
    font-family      : 'Inter', sans-serif !important;
    font-size        : 15px !important;
    font-weight      : 700 !important;
    border-radius    : 8px !important;
    padding          : 8px 20px !important;
    border           : none !important;
    transition       : background 0.2s !important;
    width            : 100% !important;
}}
div.stButton > button:hover {{ background-color: #062a63 !important; }}

/* Help content cards */
.hcard {{
    background    : rgba(4, 14, 45, 0.82);
    border        : 1px solid rgba(255,255,255,0.18);
    border-radius : 14px;
    padding       : 22px 26px;
    margin-bottom : 18px;
    backdrop-filter: blur(14px);
}}
.hcard-title {{
    font-family    : 'Inter', sans-serif;
    font-size      : 12px;
    font-weight    : 800;
    letter-spacing : 1.8px;
    text-transform : uppercase;
    color          : #93c5fd;
    margin-bottom  : 14px;
    padding-bottom : 10px;
    border-bottom  : 1px solid rgba(255,255,255,0.12);
}}

/* Individual help items */
.hitem {{
    display      : flex;
    gap          : 12px;
    padding      : 9px 0;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    font-family  : 'Inter', sans-serif;
    font-size    : 14px;
    color        : rgba(255,255,255,0.88);
    line-height  : 1.65;
    align-items  : flex-start;
}}
.hitem:last-child {{ border-bottom: none; }}
.hitem b {{ color: #e0f2fe; }}
.hicon {{ font-size: 16px; flex-shrink: 0; margin-top: 2px; }}

/* Numbered step badges */
.step-num {{
    display         : inline-flex;
    align-items     : center;
    justify-content : center;
    width           : 26px;
    height          : 26px;
    border-radius   : 50%;
    background      : #0b3d91;
    color           : white;
    font-size       : 13px;
    font-weight     : 800;
    font-family     : 'Inter', sans-serif;
    flex-shrink     : 0;
    margin-top      : 1px;
}}

/* Model stat badges */
.stat-row {{
    display    : flex;
    gap        : 12px;
    flex-wrap  : wrap;
    margin-top : 12px;
}}
.stat-badge {{
    background    : rgba(11,61,145,0.45);
    border        : 1px solid rgba(147,197,253,0.4);
    border-radius : 8px;
    padding       : 8px 16px;
    font-family   : 'Inter', sans-serif;
    font-size     : 12px;
    color         : #bfdbfe;
    font-weight   : 600;
    text-align    : center;
}}
.stat-badge span {{
    display       : block;
    font-size     : 22px;
    font-weight   : 800;
    color         : white;
    margin-bottom : 2px;
}}

/* Risk level chips */
.chip {{
    display       : inline-block;
    padding       : 3px 12px;
    border-radius : 20px;
    font-size     : 12px;
    font-weight   : 700;
    margin        : 2px 4px 2px 0;
    font-family   : 'Inter', sans-serif;
}}
.chip-g {{ background:rgba(34,197,94,0.2);  color:#86efac; border:1px solid #22c55e; }}
.chip-a {{ background:rgba(245,158,11,0.2); color:#fde68a; border:1px solid #f59e0b; }}
.chip-r {{ background:rgba(239,68,68,0.2);  color:#fca5a5; border:1px solid #ef4444; }}
</style>
""", unsafe_allow_html=True)

# ── Header row ────────────────────────────────────────────────────────────────
hl, hm, hr = st.columns([1, 7, 2])

with hl:
    st.image(str(logo_path), width=88)

with hm:
    st.markdown(
        "<h1 style='color:white;font-family:Inter,sans-serif;font-size:34px;"
        "font-weight:800;padding-top:14px;text-shadow:1px 1px 6px rgba(0,0,0,0.6);'>"
        "❓ Help — How to Use</h1>"
        "<p style='color:rgba(255,255,255,0.6);font-size:14px;margin-top:0;"
        "font-family:Inter,sans-serif;'>Freight Shipment Delay Prediction System</p>",
        unsafe_allow_html=True,
    )

with hr:
    st.write("")
    st.write("")
    if st.button("✕  Close & Return", use_container_width=True, key="top_close"):
        st.switch_page("app.py")

st.markdown(
    "<hr style='border:none;border-top:1px solid rgba(255,255,255,0.15);"
    "margin:2px 0 16px 0;'/>",
    unsafe_allow_html=True,
)

# ── Two-column help content ───────────────────────────────────────────────────
left_col, right_col = st.columns(2, gap="large")

# ══════════ LEFT COLUMN ══════════
with left_col:

    # Getting Started
    st.markdown("""
    <div class="hcard">
      <div class="hcard-title">🚀 Getting Started</div>

      <div class="hitem">
        <span class="step-num">1</span>
        <span>Select <b>Origin Port</b> — the port where your shipment departs from.</span>
      </div>
      <div class="hitem">
        <span class="step-num">2</span>
        <span>Select <b>Destination Port</b> — the port where your cargo is headed.</span>
      </div>
      <div class="hitem">
        <span class="step-num">3</span>
        <span>Choose your <b>Carrier</b> — MSC, Maersk, COSCO, CMA CGM,
        Hapag-Lloyd, or Evergreen.</span>
      </div>
      <div class="hitem">
        <span class="step-num">4</span>
        <span>Select <b>Container Type</b> — 20GP (20ft standard), 40GP (40ft standard),
        or 40HC (40ft high cube).</span>
      </div>
      <div class="hitem">
        <span class="step-num">5</span>
        <span>Pick the <b>Shipment Date (ETD)</b> — must be today or a future date.</span>
      </div>
      <div class="hitem">
        <span class="step-num">6</span>
        <span>Click <b>🔍 Predict Delay</b> to get your delay risk score and full
        route analysis instantly.</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Understanding the Results
    st.markdown("""
    <div class="hcard">
      <div class="hcard-title">📊 Understanding the Results</div>

      <div class="hitem">
        <span class="hicon">🎯</span>
        <span><b>Delay Probability Gauge</b> — model confidence that your shipment
        will be delayed. Ranges from 0% (very safe) to 100% (very high risk).</span>
      </div>
      <div class="hitem">
        <span class="hicon">🏷️</span>
        <span><b>Risk Level:</b><br>
          <span class="chip chip-g">LOW &lt;30%</span>
          <span class="chip chip-a">MEDIUM 30–60%</span>
          <span class="chip chip-r">HIGH &gt;60%</span>
        </span>
      </div>
      <div class="hitem">
        <span class="hicon">⏱️</span>
        <span><b>Standard Transit Time</b> — typical sailing duration for your route
        from historical database records. Falls back to industry averages if data
        is not available for that route.</span>
      </div>
      <div class="hitem">
        <span class="hicon">💰</span>
        <span><b>Avg Freight Cost</b> — average total charges (USD) for this
        origin–destination pair, sourced from your shipment records in MySQL.</span>
      </div>
      <div class="hitem">
        <span class="hicon">⚠️</span>
        <span><b>Possible Delay Reasons</b> — shown only when a delay is predicted.
        Top 3 historical delay causes for this route and carrier from your database.</span>
      </div>
      <div class="hitem">
        <span class="hicon">⬇️</span>
        <span><b>Download Report</b> — saves a clean .txt summary of the full
        prediction, transit time, freight cost, and delay reasons to your device.</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════ RIGHT COLUMN ══════════
with right_col:

    # About the Model
    st.markdown("""
    <div class="hcard">
      <div class="hcard-title">🤖 About the Model</div>

      <div class="hitem">
        <span class="hicon">🧠</span>
        <span>Powered by an <b>XGBoost classifier</b> trained on real-world sea
        freight shipment records. Predicts delay risk based on route, carrier,
        container type, and departure timing.</span>
      </div>
      <div class="hitem">
        <span class="hicon">📐</span>
        <span><b>Feature engineering</b> includes date-based features (day, month,
        quarter, weekday), peak-season flags, and historical delay rates per route,
        carrier, and port — all computed without data leakage.</span>
      </div>
      <div class="hitem">
        <span class="hicon">🔢</span>
        <span>Trained on <b>190,656 real shipments</b> across 9 trade lanes and
        6 major carriers (Jan 2024 – Dec 2025).</span>
      </div>

      <div class="stat-row">
        <div class="stat-badge"><span>83.3%</span>Accuracy</div>
        <div class="stat-badge"><span>0.947</span>ROC AUC</div>
        <div class="stat-badge"><span>9</span>Trade Lanes</div>
        <div class="stat-badge"><span>6</span>Carriers</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Trade Lanes
    st.markdown("""
    <div class="hcard">
      <div class="hcard-title">🌐 Trade Lanes Covered</div>

      <div class="hitem"><span class="hicon">🔵</span>
        <span><b>Trans-Pacific (Asia ↔ NA)</b> — Shanghai, Busan, Yokohama ↔
        Los Angeles, Long Beach, Seattle, New York</span>
      </div>
      <div class="hitem"><span class="hicon">🔵</span>
        <span><b>Asia–Europe (via Suez/Cape)</b> — Shanghai, Singapore,
        Port Klang ↔ Rotterdam, Hamburg, Antwerp, Le Havre</span>
      </div>
      <div class="hitem"><span class="hicon">🔵</span>
        <span><b>North Atlantic (Europe ↔ NA)</b> — Rotterdam, Hamburg ↔
        New York, Norfolk, Houston, Halifax</span>
      </div>
      <div class="hitem"><span class="hicon">🔵</span>
        <span><b>South America ↔ Europe</b> — Santos, Buenos Aires,
        Callao ↔ Rotterdam, Hamburg, Valencia</span>
      </div>
      <div class="hitem"><span class="hicon">🔵</span>
        <span><b>Intra-Asia</b> — Shanghai, Busan, Singapore,
        Ho Chi Minh, Port Klang, Laem Chabang</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # EDA Dashboard tip
    st.markdown("""
    <div class="hcard">
      <div class="hcard-title">💡 EDA Dashboard (Learn More)</div>

      <div class="hitem"><span class="hicon">💡</span>
        <span>Click the <b>yellow 💡 lightbulb button</b> (bottom-left corner of the
        main page) to open the full EDA Dashboard in a new page.</span>
      </div>
      <div class="hitem"><span class="hicon">📊</span>
        <span>The dashboard shows <b>carrier performance</b> year-over-year,
        trade lane delay rates, port congestion rankings, and on-time vs delayed
        split — all filterable by Year, Type, Carrier, and Trade Lane.</span>
      </div>
      <div class="hitem"><span class="hicon">🔍</span>
        <span>Use the <b>sidebar filters</b> inside the dashboard to drill down —
        all charts and tables update instantly with your selection.</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Bottom close button ───────────────────────────────────────────────────────
st.write("")
_, bc, _ = st.columns([4, 2, 4])
with bc:
    if st.button("✕  Close & Return to Prediction", use_container_width=True, key="bot_close"):
        st.switch_page("app.py")
