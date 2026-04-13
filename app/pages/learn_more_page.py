"""
app/pages/learn_more_page.py
============================
Opens the EDA dashboard HTML file in a full Streamlit page.
"Close & Return" button navigates back to app.py using st.switch_page().

Place this file in:  app/pages/learn_more_page.py
"""

import sys
import base64
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

st.set_page_config(
    page_title="EDA Dashboard — Freight Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR       = Path(__file__).resolve().parents[1]   # app/
IMAGE_DIR      = BASE_DIR / "images"
DASHBOARD_PATH = IMAGE_DIR / "eda_dashboard.html"

# ── Page styles ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"]    { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

.block-container {
    padding-top    : 0.6rem !important;
    padding-bottom : 0      !important;
    padding-left   : 1.2rem !important;
    padding-right  : 1.2rem !important;
}

/* Close & Return button */
div.stButton > button {
    background-color : #0b3d91;
    color            : white;
    font-family      : 'Inter', sans-serif;
    font-size        : 15px;
    font-weight      : 700;
    border-radius    : 8px;
    padding          : 8px 22px;
    border           : none;
    transition       : background 0.2s;
    width            : 100%;
}
div.stButton > button:hover { background-color: #062a63; }
</style>
""", unsafe_allow_html=True)

# ── Top bar: title + close button ────────────────────────────────────────────
title_col, btn_col = st.columns([8, 2])

with title_col:
    st.markdown(
        "<h3 style='margin:0;padding:8px 0 2px 0;color:#1565C0;"
        "font-family:Inter,sans-serif;font-size:20px;font-weight:800;'>"
        "⚓ Freight Intelligence — EDA Dashboard</h3>",
        unsafe_allow_html=True,
    )

with btn_col:
    if st.button("✕  Close & Return", use_container_width=True):
        st.switch_page("app.py")

st.markdown(
    "<hr style='margin:4px 0 6px 0;border:none;border-top:2px solid #1565C0;'/>",
    unsafe_allow_html=True,
)

# ── Render the EDA dashboard HTML ─────────────────────────────────────────────
# st.components.v1.html() embeds the HTML file in an iframe.
# scrolling=True lets the user scroll through the full dashboard.
try:
    with open(DASHBOARD_PATH, "r", encoding="utf-8") as f:
        dashboard_html = f.read()

    st.components.v1.html(dashboard_html, height=870, scrolling=True)

except FileNotFoundError:
    st.error(
        "⚠️ **Dashboard file not found.**\n\n"
        f"Expected location: `{DASHBOARD_PATH}`\n\n"
        "**Steps to fix:**\n"
        "1. Open `dataset/generate_dashboard.py`\n"
        "2. Run: `python generate_dashboard.py`\n"
        "3. Copy the generated `eda_dashboard.html` into `app/images/`\n"
        "4. Refresh this page."
    )
    st.write("")
    if st.button("← Back to Prediction"):
        st.switch_page("app.py")
