import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import requests
import base64
from datetime import date

st.set_page_config(page_title="Freight Shipment Delay Prediction", layout="wide")

API_URL   = "http://127.0.0.1:8000/predict"
BASE_DIR  = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "images"
logo_path = IMAGE_DIR / "logo.png"
bg_path   = IMAGE_DIR / "bg.jpg"


# ── Background + global styles ────────────────────────────────────────────────
def set_bg():
    with open(bg_path, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()

    st.markdown(f"""
    <style>
        

    /* Background image */
    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    /* Hide sidebar and top bar */
    [data-testid="stSidebar"]    {{ display: none !important; }}
    [data-testid="stDecoration"] {{ display: none !important; }}

    /* Field labels — white */
    label {{
        color: white !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.6) !important;
    }}

    /* Dropdown / date inputs — white background */
    div[data-testid="stSelectbox"] > div,
    div[data-testid="stDateInput"] > div {{
        background-color: rgba(255,255,255,0.92) !important;
        border-radius: 8px !important;
    }}

    /* Predict Delay button */
    div.stButton > button {{
        background-color: #0b3d91 !important;
        color: white !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        letter-spacing: 1px !important;
        border-radius: 8px !important;
        padding: 10px 30px !important;
        border: none !important;
        transition: background 0.2s !important;
    }}
    div.stButton > button:hover {{ background-color: #062a63 !important; }}

    /* Warning box */
    .warning-box {{
        background: rgba(255,200,0,0.15);
        border: 1px solid #ffcc00;
        border-radius: 8px;
        padding: 10px 16px;
        color: #ffcc00;
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        margin-top: 10px;
    }}

    /* ══════════════════════════════════════════════════════════════
       CIRCULAR FLOATING ACTION BUTTONS
       Built with st.page_link() — pure Python Streamlit widget.
       Styled here with CSS only — zero HTML, zero JavaScript.

       st.page_link renders:
         <div data-testid="stPageLink">
           <div data-testid="stPageLink-NavLink">
             <a href="...">label text</a>
           </div>
         </div>

       We make the outer wrapper fixed-position and turn the <a>
       into a circle using CSS.
    ══════════════════════════════════════════════════════════════ */

    /* Remove all default page-link chrome */
    div[data-testid="stPageLink"] {{
        position: fixed !important;
        z-index  : 999999 !important;
        padding  : 0 !important;
        margin   : 0 !important;
        width    : 72px !important;
        height   : 72px !important;
        display  : flex !important;
        align-items     : center !important;
        justify-content : center !important;
    }}

    div[data-testid="stPageLink-NavLink"] {{
        padding  : 0 !important;
        margin   : 0 !important;
        width    : 66px !important;
        height   : 66px !important;
    }}

    /* Base style for both circular FABs */
    div[data-testid="stPageLink-NavLink"] a {{
        display         : flex !important;
        align-items     : center !important;
        justify-content : center !important;
        width           : 66px !important;
        height          : 66px !important;
        border-radius   : 50% !important;
        border          : 3px solid rgba(255,255,255,0.88) !important;
        box-shadow      : 0 4px 22px rgba(0,0,0,0.55) !important;
        font-size       : 30px !important;
        text-decoration : none !important;
        font-weight     : 900 !important;
        transition      : transform 0.18s, box-shadow 0.18s !important;
        padding         : 0 !important;
        margin          : 0 !important;
        line-height     : 1 !important;
    }}
    div[data-testid="stPageLink-NavLink"] a:hover {{
        transform  : scale(1.13) !important;
        box-shadow : 0 8px 30px rgba(0,0,0,0.65) !important;
    }}

    /* Suppress default page-link text rendering */
    div[data-testid="stPageLink-NavLink"] a p,
    div[data-testid="stPageLink-NavLink"] a span {{
        display : none !important;
    }}
/* LEFT button */
div[data-testid="stPageLink"] a[href*="learn_more_page"] {{
    position: fixed !important;
    bottom: 36px !important;
    left: 36px !important;
    width: 70px !important;
    height: 70px !important;
    border-radius: 50% !important;
    background-color: #FFC81E;
}}

/* RIGHT button */
div[data-testid="stPageLink"] a[href*="help_page"] {{
    position: fixed !important;
    bottom: 36px !important;
    right: 36px !important;
    width: 66px !important;
    height: 66px !important;
    border-radius: 50% !important;
    background-color: white;

}}

 
    </style>
    """, unsafe_allow_html=True)


set_bg()

# ── Floating circular FABs — pure Python st.page_link() ──────────────────────

st.page_link("pages/learn_more_page.py", label="learn 💡",use_container_width=True)   # yellow lightbulb — bottom-left
st.page_link("pages/help_page.py", label="Help ?",use_container_width=True)    # blue question mark — bottom-right

# ── Header ────────────────────────────────────────────────────────────────────
header1, header2 = st.columns([1, 6])
with header1:
    st.image(str(logo_path), width=110)
with header2:
    st.markdown(
        "<h1 style='color:white;font-family:Montserrat,sans-serif;font-size:48px;"
        "font-weight:700;letter-spacing:2px;text-shadow:2px 2px 8px rgba(0,0,0,0.6);"
        "padding-top:15px;'>Freight Shipment Delay Prediction</h1>",
        unsafe_allow_html=True,
    )

st.write("")

# ── Port / option lists ───────────────────────────────────────────────────────
PORTS = [
    "Select Port", "Shanghai", "Ningbo", "Busan", "Yokohama", "Kaohsiung",
    "Yantian", "Shekou", "Xiamen", "Qingdao", "Tianjin", "Port Klang",
    "Singapore", "Ho Chi Minh", "Haiphong", "Rotterdam", "Antwerp", "Hamburg",
    "Le Havre", "Southampton", "Felixstowe", "Bremerhaven", "Zeebrugge",
    "Lisbon", "Gdansk", "Santos", "Itapoa", "Rio Grande", "Paranagua",
    "Buenos Aires", "Montevideo", "Callao", "Guayaquil", "Valparaiso",
    "San Antonio", "Los Angeles", "Long Beach", "Seattle", "Tacoma", "Oakland",
    "New York", "Norfolk", "Savannah", "Charleston", "Jacksonville", "Valencia",
    "Algeciras", "Piraeus", "Barcelona", "Baltimore", "Philadelphia", "Boston",
    "Halifax", "Houston", "Laem Chabang",
]
CARRIERS   = ["MSC", "Maersk", "COSCO", "CMA CGM", "Hapag-Lloyd", "Evergreen"]
CONTAINERS = ["20GP", "40GP", "40HC"]

# ── Input fields ──────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    origin = st.selectbox("Origin Port", PORTS)
with col2:
    destination = st.selectbox("Destination Port", PORTS)
with col3:
    carrier = st.selectbox("Carrier", CARRIERS)
with col4:
    container = st.selectbox("Container Type", CONTAINERS)
with col5:
    shipment_date = st.date_input("Shipment Date", min_value=date.today())

st.write("")

# ── Predict button ────────────────────────────────────────────────────────────
pred_col, _sp = st.columns([2, 8])
with pred_col:
    predict_clicked = st.button("🔍 Predict Delay", use_container_width=True)

# ── Predict logic ─────────────────────────────────────────────────────────────
if predict_clicked:
    if origin == "Select Port" or destination == "Select Port":
        st.markdown(
            '<div class="warning-box">⚠️ Please select Origin and Destination Ports.</div>',
            unsafe_allow_html=True,
        )
    elif origin == destination:
        st.markdown(
            '<div class="warning-box">⚠️ Origin and Destination cannot be the same port.</div>',
            unsafe_allow_html=True,
        )
    else:
        payload = {
            "origin":        origin,
            "destination":   destination,
            "carrier":       carrier,
            "container":     container,
            "shipment_date": str(shipment_date),
        }
        with st.spinner("Predicting..."):
            try:
                response = requests.post(API_URL, json=payload, timeout=10)
                response.raise_for_status()
                result = response.json()

                st.session_state["prediction"]  = result["prediction"]
                st.session_state["probability"] = result["probability"]
                st.session_state["input_data"]  = {
                    "origin":        origin,
                    "destination":   destination,
                    "carrier":       carrier,
                    "container":     container,
                    "shipment_date": str(shipment_date),
                }
                st.switch_page("pages/results_page.py")

            except requests.exceptions.ConnectionError:
                st.markdown(
                    '<div class="warning-box">⚠️ Cannot connect to API. '
                    "Make sure FastAPI is running on port 8000.</div>",
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.markdown(
                    f'<div class="warning-box">⚠️ Error: {str(e)}</div>',
                    unsafe_allow_html=True,
                )
