import streamlit as st
import plotly.graph_objects as go
import base64
from pathlib import Path
import sys
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.mysql_connection import get_connection

st.set_page_config(page_title="Prediction Result", layout="wide")

# ── Guard ──────────────────────────────────────────────────────────────────────
if "prediction" not in st.session_state or "probability" not in st.session_state:
    st.warning("No prediction data found. Please go back and submit the form.")
    if st.button("⬅ Back to Prediction"):
        st.switch_page("app.py")
    st.stop()

prediction    = st.session_state["prediction"]
probability   = st.session_state["probability"]
pct           = round(probability * 100, 2)
on_time_pct   = round(100 - pct, 2)
input_data    = st.session_state.get("input_data", {})

origin        = input_data.get("origin",        "—")
destination   = input_data.get("destination",   "—")
carrier       = input_data.get("carrier",       "—")
container     = input_data.get("container",     "—")
shipment_date = input_data.get("shipment_date", "—")

try:
    shipment_month = datetime.strptime(shipment_date, "%Y-%m-%d").month
except Exception:
    shipment_month = None

# ── Risk level ─────────────────────────────────────────────────────────────────
if pct < 30:
    risk_label = "LOW RISK"
    risk_color = "#22c55e"
elif pct < 60:
    risk_label = "MEDIUM RISK"
    risk_color = "#f59e0b"
else:
    risk_label = "HIGH RISK"
    risk_color = "#ef4444"

# ── Static transit-time lookup ─────────────────────────────────────────────────
# Covers all 9 trade lanes. Used as fallback when MySQL returns NULL.
TRANSIT_DAYS: dict = {
    # Asia → North America
    "Shanghai":    {"Los Angeles": 14, "Long Beach": 14, "Seattle": 12, "Tacoma": 12,
                    "Oakland": 13, "New York": 28, "Norfolk": 27, "Savannah": 26,
                    "Charleston": 26, "Jacksonville": 27},
    "Ningbo":      {"Los Angeles": 14, "Long Beach": 14, "Seattle": 12, "Tacoma": 12,
                    "Oakland": 13, "New York": 28, "Norfolk": 27, "Savannah": 26,
                    "Charleston": 26, "Jacksonville": 27},
    "Busan":       {"Los Angeles": 12, "Long Beach": 12, "Seattle": 10, "Tacoma": 10,
                    "Oakland": 11, "New York": 26, "Norfolk": 25, "Savannah": 24,
                    "Charleston": 24, "Jacksonville": 25},
    "Yokohama":    {"Los Angeles": 11, "Long Beach": 11, "Seattle": 9,  "Tacoma": 9,
                    "Oakland": 10, "New York": 25, "Norfolk": 24, "Savannah": 23,
                    "Charleston": 23, "Jacksonville": 24},
    "Kaohsiung":   {"Los Angeles": 15, "Long Beach": 15, "Seattle": 13, "Tacoma": 13,
                    "Oakland": 14, "New York": 28, "Norfolk": 27, "Savannah": 26,
                    "Charleston": 26, "Jacksonville": 27},
    "Yantian":     {"Los Angeles": 14, "Long Beach": 14, "Seattle": 12, "Tacoma": 12,
                    "Oakland": 13, "New York": 28, "Norfolk": 27, "Savannah": 26,
                    "Charleston": 26, "Jacksonville": 27},
    "Shekou":      {"Los Angeles": 14, "Long Beach": 14, "Seattle": 12, "Tacoma": 12,
                    "Oakland": 13, "New York": 28, "Norfolk": 27, "Savannah": 26,
                    "Charleston": 26, "Jacksonville": 27},
    "Xiamen":      {"Los Angeles": 15, "Long Beach": 15, "Seattle": 13, "Tacoma": 13,
                    "Oakland": 14, "New York": 29, "Norfolk": 28, "Savannah": 27,
                    "Charleston": 27, "Jacksonville": 28},
    "Qingdao":     {"Los Angeles": 15, "Long Beach": 15, "Seattle": 13, "Tacoma": 13,
                    "Oakland": 14, "New York": 29, "Norfolk": 28, "Savannah": 27,
                    "Charleston": 27, "Jacksonville": 28},
    "Tianjin":     {"Los Angeles": 16, "Long Beach": 16, "Seattle": 14, "Tacoma": 14,
                    "Oakland": 15, "New York": 30, "Norfolk": 29, "Savannah": 28,
                    "Charleston": 28, "Jacksonville": 29},
    # Asia → Europe
    "Port Klang":  {"Rotterdam": 22, "Antwerp": 23, "Hamburg": 24, "Le Havre": 23,
                    "Southampton": 22, "Felixstowe": 22, "Valencia": 20,
                    "Algeciras": 19, "Piraeus": 18, "Barcelona": 20},
    "Singapore":   {"Rotterdam": 22, "Antwerp": 23, "Hamburg": 24, "Le Havre": 23,
                    "Southampton": 22, "Felixstowe": 22, "Valencia": 20,
                    "Algeciras": 19, "Piraeus": 17, "Barcelona": 20},
    "Ho Chi Minh": {"Rotterdam": 24, "Antwerp": 25, "Hamburg": 26, "Le Havre": 25,
                    "Southampton": 24, "Felixstowe": 24, "Valencia": 22,
                    "Algeciras": 21, "Piraeus": 20, "Barcelona": 22},
    "Haiphong":    {"Rotterdam": 25, "Antwerp": 26, "Hamburg": 27, "Le Havre": 26,
                    "Southampton": 25, "Felixstowe": 25, "Valencia": 23,
                    "Algeciras": 22, "Piraeus": 21, "Barcelona": 23},
    # Europe → North America
    "Rotterdam":   {"New York": 8,  "Norfolk": 9,  "Baltimore": 9,  "Philadelphia": 9,
                    "Boston": 8,  "Halifax": 7,  "Jacksonville": 11, "Savannah": 11,
                    "Charleston": 10, "Houston": 16},
    "Antwerp":     {"New York": 9,  "Norfolk": 10, "Baltimore": 10, "Philadelphia": 9,
                    "Boston": 9,  "Halifax": 8,  "Jacksonville": 12, "Savannah": 12,
                    "Charleston": 11, "Houston": 17},
    "Hamburg":     {"New York": 10, "Norfolk": 11, "Baltimore": 11, "Philadelphia": 10,
                    "Boston": 9,  "Halifax": 8,  "Jacksonville": 13, "Savannah": 13,
                    "Charleston": 12, "Houston": 18},
    "Le Havre":    {"New York": 8,  "Norfolk": 9,  "Baltimore": 9,  "Philadelphia": 8,
                    "Boston": 7,  "Halifax": 7,  "Jacksonville": 11, "Savannah": 11,
                    "Charleston": 10, "Houston": 16},
    "Southampton": {"New York": 8,  "Norfolk": 9,  "Baltimore": 9,  "Philadelphia": 8,
                    "Boston": 7,  "Halifax": 7,  "Jacksonville": 11, "Savannah": 11,
                    "Charleston": 10, "Houston": 16},
    "Felixstowe":  {"New York": 9,  "Norfolk": 10, "Baltimore": 10, "Philadelphia": 9,
                    "Boston": 8,  "Halifax": 7,  "Jacksonville": 12, "Savannah": 12,
                    "Charleston": 11, "Houston": 17},
    "Bremerhaven": {"New York": 10, "Norfolk": 11, "Baltimore": 11, "Philadelphia": 10,
                    "Boston": 9,  "Halifax": 8,  "Jacksonville": 13, "Savannah": 13,
                    "Charleston": 12, "Houston": 18},
    "Zeebrugge":   {"New York": 9,  "Norfolk": 10, "Baltimore": 10, "Philadelphia": 9,
                    "Boston": 8,  "Halifax": 7,  "Jacksonville": 12, "Savannah": 12,
                    "Charleston": 11, "Houston": 17},
    "Lisbon":      {"New York": 8,  "Norfolk": 9,  "Baltimore": 9,  "Philadelphia": 8,
                    "Boston": 7,  "Halifax": 6,  "Jacksonville": 10, "Savannah": 10,
                    "Charleston": 9,  "Houston": 15},
    "Gdansk":      {"New York": 12, "Norfolk": 13, "Baltimore": 13, "Philadelphia": 12,
                    "Boston": 11, "Halifax": 10, "Jacksonville": 15, "Savannah": 15,
                    "Charleston": 14, "Houston": 20},
    # South America → Europe
    "Santos":      {"Rotterdam": 16, "Antwerp": 17, "Hamburg": 18, "Le Havre": 17,
                    "Southampton": 17, "Felixstowe": 17, "Valencia": 14,
                    "Algeciras": 13, "Piraeus": 16, "Barcelona": 14},
    "Itapoa":      {"Rotterdam": 16, "Antwerp": 17, "Hamburg": 18, "Le Havre": 17,
                    "Southampton": 17, "Felixstowe": 17, "Valencia": 14,
                    "Algeciras": 13, "Piraeus": 16, "Barcelona": 14},
    "Rio Grande":  {"Rotterdam": 17, "Antwerp": 18, "Hamburg": 19, "Le Havre": 18,
                    "Southampton": 18, "Felixstowe": 18, "Valencia": 15,
                    "Algeciras": 14, "Piraeus": 17, "Barcelona": 15},
    "Paranagua":   {"Rotterdam": 17, "Antwerp": 18, "Hamburg": 19, "Le Havre": 18,
                    "Southampton": 18, "Felixstowe": 18, "Valencia": 15,
                    "Algeciras": 14, "Piraeus": 17, "Barcelona": 15},
    "Buenos Aires":{"Rotterdam": 18, "Antwerp": 19, "Hamburg": 20, "Le Havre": 19,
                    "Southampton": 18, "Felixstowe": 18, "Valencia": 16,
                    "Algeciras": 15, "Piraeus": 18, "Barcelona": 16},
    "Montevideo":  {"Rotterdam": 18, "Antwerp": 19, "Hamburg": 20, "Le Havre": 19,
                    "Southampton": 18, "Felixstowe": 18, "Valencia": 16,
                    "Algeciras": 15, "Piraeus": 18, "Barcelona": 16},
    "Callao":      {"Rotterdam": 20, "Antwerp": 21, "Hamburg": 22, "Le Havre": 21,
                    "Southampton": 20, "Felixstowe": 20, "Valencia": 18,
                    "Algeciras": 17, "Piraeus": 20, "Barcelona": 18},
    "Guayaquil":   {"Rotterdam": 19, "Antwerp": 20, "Hamburg": 21, "Le Havre": 20,
                    "Southampton": 19, "Felixstowe": 19, "Valencia": 17,
                    "Algeciras": 16, "Piraeus": 19, "Barcelona": 17},
    "Valparaiso":  {"Rotterdam": 20, "Antwerp": 21, "Hamburg": 22, "Le Havre": 21,
                    "Southampton": 20, "Felixstowe": 20, "Valencia": 18,
                    "Algeciras": 17, "Piraeus": 20, "Barcelona": 18},
    "San Antonio": {"Rotterdam": 20, "Antwerp": 21, "Hamburg": 22, "Le Havre": 21,
                    "Southampton": 20, "Felixstowe": 20, "Valencia": 18,
                    "Algeciras": 17, "Piraeus": 20, "Barcelona": 18},
    # Intra-Asia
    "Laem Chabang":{"Singapore": 4, "Port Klang": 5, "Ho Chi Minh": 3,
                    "Haiphong": 4, "Busan": 6, "Shanghai": 5},
    # North America → Asia (reverse Trans-Pacific)
    "Los Angeles": {"Shanghai": 14, "Ningbo": 14, "Busan": 12, "Yokohama": 11,
                    "Kaohsiung": 15, "Yantian": 14, "Shekou": 14,
                    "Xiamen": 15, "Qingdao": 15, "Tianjin": 16},
    "Long Beach":  {"Shanghai": 14, "Ningbo": 14, "Busan": 12, "Yokohama": 11,
                    "Kaohsiung": 15, "Yantian": 14, "Shekou": 14,
                    "Xiamen": 15, "Qingdao": 15, "Tianjin": 16},
    # North America → Europe
    "New York":    {"Rotterdam": 8,  "Hamburg": 10, "Antwerp": 9, "Le Havre": 8,
                    "Southampton": 8, "Felixstowe": 9},
    "Norfolk":     {"Rotterdam": 9,  "Hamburg": 11, "Antwerp": 10, "Le Havre": 9,
                    "Southampton": 9, "Felixstowe": 10},
    "Savannah":    {"Rotterdam": 11, "Hamburg": 13, "Antwerp": 12, "Le Havre": 11,
                    "Southampton": 11, "Felixstowe": 12},
    "Charleston":  {"Rotterdam": 10, "Hamburg": 12, "Antwerp": 11, "Le Havre": 10,
                    "Southampton": 10, "Felixstowe": 11},
    "Houston":     {"Rotterdam": 16, "Hamburg": 18, "Antwerp": 17, "Le Havre": 16,
                    "Southampton": 16, "Felixstowe": 17},
    # Europe → South America
    "Valencia":    {"Santos": 14, "Itapoa": 14, "Rio Grande": 15, "Paranagua": 15,
                    "Buenos Aires": 16, "Montevideo": 16, "Callao": 18,
                    "Guayaquil": 17, "Valparaiso": 18, "San Antonio": 18},
    "Algeciras":   {"Santos": 13, "Itapoa": 13, "Rio Grande": 14, "Paranagua": 14,
                    "Buenos Aires": 15, "Montevideo": 15, "Callao": 17,
                    "Guayaquil": 16, "Valparaiso": 17, "San Antonio": 17},
    "Piraeus":     {"Santos": 16, "Itapoa": 16, "Rio Grande": 17, "Paranagua": 17,
                    "Buenos Aires": 18, "Montevideo": 18, "Callao": 20,
                    "Guayaquil": 19, "Valparaiso": 20, "San Antonio": 20},
    "Barcelona":   {"Santos": 14, "Itapoa": 14, "Rio Grande": 15, "Paranagua": 15,
                    "Buenos Aires": 16, "Montevideo": 16, "Callao": 18,
                    "Guayaquil": 17, "Valparaiso": 18, "San Antonio": 18},
}


def static_transit(orig: str, dest: str):
    days = TRANSIT_DAYS.get(orig, {}).get(dest)
    if days:
        return f"{days} days"
    days = TRANSIT_DAYS.get(dest, {}).get(orig)
    if days:
        return f"{days} days"
    return None


# ── Fetch insights from MySQL ──────────────────────────────────────────────────
def get_insights(origin, destination, carrier, shipment_month):
    insights = {"avg_freight_cost": None, "avg_transit_days": None, "delay_reasons": []}
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        # Avg freight cost
        cursor.execute("""
            SELECT ROUND(AVG(Total_Charges_USD), 0)
            FROM shipments_raw_details
            WHERE Origin_Port = %s AND Destination_Port = %s
        """, (origin, destination))
        row = cursor.fetchone()
        if row and row[0]:
            insights["avg_freight_cost"] = f"$ {int(row[0]):,}"

        # Transit time — primary: DATEDIFF with sanity range filter
        cursor.execute("""
            SELECT ROUND(AVG(DATEDIFF(DATE(ETA), DATE(ETD))), 0)
            FROM shipments_raw_details
            WHERE Origin_Port = %s AND Destination_Port = %s
              AND ETA IS NOT NULL AND ETD IS NOT NULL
              AND ETA != '' AND ETD != ''
              AND DATEDIFF(DATE(ETA), DATE(ETD)) BETWEEN 1 AND 120
        """, (origin, destination))
        row = cursor.fetchone()
        if row and row[0]:
            insights["avg_transit_days"] = f"{int(row[0])} days"

        # Transit time — fallback: TIMESTAMPDIFF handles DATETIME columns too
        if not insights["avg_transit_days"]:
            cursor.execute("""
                SELECT ROUND(AVG(TIMESTAMPDIFF(DAY, ETD, ETA)), 0)
                FROM shipments_raw_details
                WHERE Origin_Port = %s AND Destination_Port = %s
                  AND ETA IS NOT NULL AND ETD IS NOT NULL
                  AND TIMESTAMPDIFF(DAY, ETD, ETA) BETWEEN 1 AND 120
            """, (origin, destination))
            row = cursor.fetchone()
            if row and row[0]:
                insights["avg_transit_days"] = f"{int(row[0])} days"

        # Delay reasons — with carrier + month filter
        if shipment_month:
            cursor.execute("""
                SELECT Delay_Reason, COUNT(*) AS cnt
                FROM shipments_raw_details
                WHERE Origin_Port = %s AND Destination_Port = %s AND Carrier = %s
                  AND MONTH(STR_TO_DATE(ETD, '%%d-%%m-%%Y')) = %s
                  AND Delay_Reason IS NOT NULL AND Delay_Reason != '' AND Delay_Reason != 'On Time'
                GROUP BY Delay_Reason ORDER BY cnt DESC LIMIT 3
            """, (origin, destination, carrier, shipment_month))
        else:
            cursor.execute("""
                SELECT Delay_Reason, COUNT(*) AS cnt
                FROM shipments_raw_details
                WHERE Origin_Port = %s AND Destination_Port = %s AND Carrier = %s
                  AND Delay_Reason IS NOT NULL AND Delay_Reason != '' AND Delay_Reason != 'On Time'
                GROUP BY Delay_Reason ORDER BY cnt DESC LIMIT 3
            """, (origin, destination, carrier))

        rows = cursor.fetchall()

        # Broader fallback — drop carrier/month
        if not rows:
            cursor.execute("""
                SELECT Delay_Reason, COUNT(*) AS cnt
                FROM shipments_raw_details
                WHERE Origin_Port = %s AND Destination_Port = %s
                  AND Delay_Reason IS NOT NULL AND Delay_Reason != '' AND Delay_Reason != 'On Time'
                GROUP BY Delay_Reason ORDER BY cnt DESC LIMIT 3
            """, (origin, destination))
            rows = cursor.fetchall()

        insights["delay_reasons"] = [r[0] for r in rows] if rows else []
        cursor.close()
        conn.close()

    except Exception as e:
        st.error(f"Could not fetch insights: {e}")

    return insights


insights      = get_insights(origin, destination, carrier, shipment_month)
avg_cost      = insights["avg_freight_cost"] or "N/A"
delay_reasons = insights["delay_reasons"]

# Transit time: MySQL → static lookup → N/A
avg_transit = (
    insights["avg_transit_days"]
    or static_transit(origin, destination)
    or "N/A"
)

# ── Background ────────────────────────────────────────────────────────────────
def set_bg():
    bg_path = Path(__file__).resolve().parent.parent / "images" / "bg.jpg"
    with open(bg_path, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded}");
        background-size: cover;
        background-position: center;
    }}
    [data-testid="stSidebar"] {{ display: none; }}
    .block-container {{
        padding-top: 3.5rem !important;
        padding-bottom: 0.5rem !important;
        max-width: 100% !important;
    }}
    .result-title {{
        color: white;
        font-family: 'Inter', sans-serif;
        font-size: 42px;
        font-weight: 600;
        letter-spacing: 1px;
        text-shadow: 1px 1px 4px rgba(0,0,0,0.5);
        padding-top: 10px;
        margin-bottom: 0;
    }}
    .result-subtitle {{
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: white;
        letter-spacing: 1px;
        margin-bottom: 1rem;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.6);
    }}
    .risk-badge {{
        display: inline-block;
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 2px;
        padding: 4px 16px;
        border-radius: 6px;
        margin-bottom: 0.6rem;
    }}
    .verdict-box {{
        border-radius: 10px;
        padding: 0.9rem 1.4rem;
        font-family: 'Inter', sans-serif;
        font-size: 1.15rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }}
    .card {{
        background: rgba(0, 10, 30, 0.65);
        border: 1px solid rgba(255,255,255,0.25);
        border-radius: 10px;
        padding: 1rem 1.4rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
    }}
    .card-title {{
        font-family: 'Inter', sans-serif;
        font-size: 0.78rem;
        color: white;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 0.7rem;
        font-weight: 600;
    }}
    .row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.35rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.15);
        font-family: 'Inter', sans-serif;
        font-size: 0.88rem;
    }}
    .row:last-child {{ border-bottom: none; }}
    .rkey {{ color: white; font-weight: 400; }}
    .rval {{ color: white; font-weight: 600; text-shadow: 1px 1px 3px rgba(0,0,0,0.4); }}
    .reason-item {{
        font-family: 'Inter', sans-serif;
        font-size: 0.88rem;
        color: #fecaca;
        padding: 0.3rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.12);
        font-weight: 500;
    }}
    .reason-item:last-child {{ border-bottom: none; }}
    div.stButton > button {{
        background-color: #0b3d91 !important;
        color: white !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        letter-spacing: 1px !important;
        border-radius: 8px !important;
        padding: 10px 30px !important;
        border: none !important;
        transition: background 0.2s !important;
        width: 100% !important;
    }}
    div.stButton > button:hover {{ background-color: #062a63 !important; }}
    div.stDownloadButton > button {{
        background-color: rgba(11,61,145,0.25) !important;
        color: white !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255,255,255,0.35) !important;
        transition: background 0.2s !important;
        width: 100% !important;
    }}
    div.stDownloadButton > button:hover {{
        background-color: rgba(11,61,145,0.5) !important;
    }}
    </style>
    """, unsafe_allow_html=True)


set_bg()

# ── Header ────────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).resolve().parent.parent
logo_path = BASE_DIR / "images" / "logo.png"

header1, header2 = st.columns([1, 6])
with header1:
    st.image(str(logo_path), width=110)
with header2:
    st.markdown("""
    <div class="result-title">Shipment Delay Analysis</div>
    <div class="result-subtitle">Prediction Result : Freight Intelligence System</div>
    """, unsafe_allow_html=True)

st.write("")

# ── Download report — above shipment details ───────────────────────────────────
def build_report() -> bytes:
    lines = [
        "=" * 58,
        "  FREIGHT DELAY PREDICTION REPORT",
        f"  Generated : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 58,
        "",
        "SHIPMENT DETAILS",
        "-" * 40,
        f"  Origin Port       : {origin}",
        f"  Destination Port  : {destination}",
        f"  Carrier           : {carrier}",
        f"  Container Type    : {container}",
        f"  Shipment Date     : {shipment_date}",
        "",
        "PREDICTION RESULT",
        "-" * 40,
        f"  Outcome           : {'DELAYED' if prediction == 1 else 'ON TIME'}",
        f"  Delay Probability : {pct}%",
        f"  On-Time Prob.     : {on_time_pct}%",
        f"  Risk Level        : {risk_label}",
        "",
        "ROUTE INFORMATION",
        "-" * 40,
        f"  Standard Transit  : {avg_transit}",
        f"  Avg Freight Cost  : {avg_cost}",
        "",
    ]
    if delay_reasons:
        lines += ["COMMON DELAY REASONS ON THIS ROUTE", "-" * 40]
        for i, r in enumerate(delay_reasons, 1):
            lines.append(f"  {i}. {r}")
        lines.append("")
    lines += [
        "=" * 58,
        "  Model: XGBoost | Accuracy: 83.3% | ROC AUC: 0.947",
        "=" * 58,
    ]
    return "\n".join(lines).encode("utf-8")


dl_col, _ = st.columns([2, 8])
with dl_col:
    st.download_button(
        label="⬇️ Download Report",
        data=build_report(),
        file_name=f"freight_prediction_{origin}_{destination}_{shipment_date}.txt",
        mime="text/plain",
        use_container_width=True,
    )

st.write("")

# ── Main layout ───────────────────────────────────────────────────────────────
left, right = st.columns([1.1, 1], gap="large")

# ════════════ LEFT ════════════
with left:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number={"suffix": "%", "font": {"size": 36, "color": "white", "family": "Inter"}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": "white",
                "tickfont": {"color": "white", "size": 10},
            },
            "bar": {"color": "white", "thickness": 0.08},
            "bgcolor": "rgba(0,10,30,0.5)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  30], "color": "rgba(34,197,94,0.7)"},
                {"range": [30, 60], "color": "rgba(245,158,11,0.7)"},
                {"range": [60,100], "color": "rgba(239,68,68,0.7)"},
            ],
            "threshold": {
                "line": {"color": "white", "width": 3},
                "thickness": 0.8,
                "value": pct,
            },
        },
        title={"text": "DELAY PROBABILITY",
               "font": {"size": 12, "color": "white", "family": "Inter"}},
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"},
        height=220,
        margin=dict(t=25, b=0, l=15, r=15),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        f'<div class="risk-badge" style="background:{risk_color}33;color:{risk_color};'
        f'border:1px solid {risk_color}66;">{risk_label}</div>',
        unsafe_allow_html=True,
    )

    if prediction == 1:
        st.markdown(
            '<div class="verdict-box" style="background:rgba(239,68,68,0.2);'
            'border:1px solid rgba(239,68,68,0.5);color:#fca5a5;">'
            '⚠️ Shipment Likely Delayed</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="verdict-box" style="background:rgba(34,197,94,0.2);'
            'border:1px solid rgba(34,197,94,0.5);color:#86efac;">'
            '✅ Shipment Likely On Time</div>',
            unsafe_allow_html=True,
        )

    st.markdown(f"""
    <div class="card">
        <div class="card-title">📦 Route Insights</div>
        <div class="row">
            <span class="rkey">Avg Freight Cost (this route)</span>
            <span class="rval" style="color:#fde68a;">{avg_cost}</span>
        </div>
        <div class="row">
            <span class="rkey">Standard Transit Time</span>
            <span class="rval" style="color:#7dd3fc;">{avg_transit}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if prediction == 1:
        reasons_html = (
            "".join(
                f'<div class="reason-item">{"ABC"[i]}. {r}</div>'
                for i, r in enumerate(delay_reasons)
            )
            if delay_reasons
            else '<div class="reason-item">No historical delay data for this route.</div>'
        )
        st.markdown(f"""
        <div class="card">
            <div class="card-title">⚠️ Possible Delay Reasons</div>
            {reasons_html}
        </div>
        """, unsafe_allow_html=True)

# ════════════ RIGHT ════════════
with right:
    st.write("")

    st.markdown(f"""
    <div class="card">
        <div class="card-title">📋 Shipment Details</div>
        <div class="row"><span class="rkey">Origin Port</span><span class="rval">{origin}</span></div>
        <div class="row"><span class="rkey">Destination Port</span><span class="rval">{destination}</span></div>
        <div class="row"><span class="rkey">Carrier</span><span class="rval">{carrier}</span></div>
        <div class="row"><span class="rkey">Container Type</span><span class="rval">{container}</span></div>
        <div class="row"><span class="rkey">Shipment Date</span><span class="rval">{shipment_date}</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <div class="card-title">📊 Probability Breakdown</div>
        <div class="row">
            <span class="rkey">On Time</span>
            <span class="rval" style="color:#86efac;">{on_time_pct}%</span>
        </div>
        <div class="row">
            <span class="rkey">Delayed</span>
            <span class="rval" style="color:#fca5a5;">{pct}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("⬅ New Prediction", use_container_width=True):
        st.switch_page("app.py")
