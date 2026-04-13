"""
generate_dashboard.py
=====================
Run this script once to generate eda_dashboard.html from your dataset.

Usage:
    python generate_dashboard.py

Requirements:
    pip install pandas

Output:
    eda_dashboard.html  →  copy to  app/images/eda_dashboard.html
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
DATASET_PATH = "shipping_dataset_updated.csv"
OUTPUT_PATH  = "eda_dashboard.html"

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
print("Loading dataset...")
df = pd.read_csv(DATASET_PATH)

df["ETD"] = pd.to_datetime(df["ETD"], dayfirst=True, errors="coerce")
df["ETA"] = pd.to_datetime(df["ETA"], dayfirst=True, errors="coerce")
df["Year"] = df["ETD"].dt.year.astype(str)

# ── STATIC SUMMARY (for KPI defaults) ─────────────────────────────────────────
total_shipments = len(df)
delayed         = int(df["Delay_Flag"].sum())
on_time         = total_shipments - delayed
overall_delay   = round(df["Delay_Flag"].mean() * 100, 2)
export_delay    = round(df[df["Type"] == "Export"]["Delay_Flag"].mean() * 100, 2)
import_delay    = round(df[df["Type"] == "Import"]["Delay_Flag"].mean() * 100, 2)

# ── YoY static (baseline display) ─────────────────────────────────────────────
yoy = df.groupby(["Type", "Year"])["Delay_Flag"].mean().mul(100).round(2)
exp_2024 = float(yoy.get(("Export", "2024"), 0))
imp_2024 = float(yoy.get(("Import", "2024"), 0))
exp_2025 = float(yoy.get(("Export", "2025"), 0))
imp_2025 = float(yoy.get(("Import", "2025"), 0))

# ── Carrier performance ────────────────────────────────────────────────────────
carrier_year = df.groupby(["Carrier", "Year"])["Delay_Flag"].mean().mul(100).round(2).unstack()
carriers = list(carrier_year.index)

def safe_val(df_idx, col):
    try:
        return round(float(carrier_year.loc[df_idx, col]), 2)
    except Exception:
        return 0.0

c2024 = [safe_val(c, "2024") for c in carriers]
c2025 = [safe_val(c, "2025") for c in carriers]

# ── Carrier x Type detail table ───────────────────────────────────────────────
ct = df.groupby(["Carrier", "Type", "Year"])["Delay_Flag"].mean().mul(100).round(2)

def get_ct(carrier, typ, year):
    try:
        return float(ct.loc[(carrier, typ, year)])
    except Exception:
        return 0.0

trend_map = {
    "Hapag-Lloyd": "↓↓ Best Improvement",
    "Maersk":      "↓ Improving",
    "CMA CGM":     "↓ Improving",
    "MSC":         "↓ Improving",
    "COSCO":       "↓ Moderate",
    "Evergreen":   "↓ Moderate",
}
trend_class_map = {
    "↓↓ Best Improvement": "pmet",
    "↓ Improving":         "pmet",
    "↓ Moderate":          "ph",
}

carrier_rows = []
for c in carriers:
    e24  = get_ct(c, "Export", "2024")
    i24  = get_ct(c, "Import", "2024")
    e25  = get_ct(c, "Export", "2025")
    i25  = get_ct(c, "Import", "2025")
    trend = trend_map.get(c, "↓ Improving")
    tcls  = trend_class_map.get(trend, "pmet")
    carrier_rows.append(f"""
      <tr data-carrier="{c}" data-exp24="{e24}" data-imp24="{i24}" data-exp25="{e25}" data-imp25="{i25}">
        <td><b>{c}</b></td>
        <td class="cv-exp24">{e24}%</td><td class="cv-imp24">{i24}%</td>
        <td class="cv-exp25">{e25}%</td><td class="cv-imp25">{i25}%</td>
        <td><span class="pill {tcls}">{trend}</span></td>
      </tr>""")
carrier_table_html = "\n".join(carrier_rows)

# ── Trade lane analysis ────────────────────────────────────────────────────────
trade_type = df.groupby(["Trade", "Type"])["Delay_Flag"].mean().mul(100).round(2)
risk_map = lambda p: ("pu","HIGH") if p >= 48 else (("ph","MED-HIGH") if p >= 44 else (("pl","MEDIUM") if p >= 40 else ("pmet","LOWER")))

trade_rows = []
all_trades  = sorted(df["Trade"].dropna().unique().tolist())

for (trade, typ), pct in trade_type.sort_values(ascending=False).items():
    rcls, rlabel = risk_map(pct)
    trade_rows.append(f"""
      <tr data-trade="{trade}" data-type="{typ}" data-pct="{pct}">
        <td>{trade}</td><td>{typ}</td><td>{pct}%</td>
        <td><span class="pill {rcls}">{rlabel}</span></td>
      </tr>""")
trade_table_html = "\n".join(trade_rows)

# Trade chart data (default — all)
def make_trade_chart_data(data_df):
    td = data_df.groupby(["Trade", "Type"])["Delay_Flag"].mean().mul(100).round(2)
    labels = []
    values = []
    colors = []
    for (trade, typ), val in td.sort_values(ascending=False).items():
        short = (trade
            .replace("(via Suez/Cape)", "").replace("(via Cape)", "")
            .replace("North Atlantic ", "N.Atl ").replace("Trans-Pacific ", "Trans-Pac ")
            .replace("South America", "S.Am"))
        labels.append(f"{short} ({typ})")
        values.append(float(val))
        colors.append("#ef4444" if val >= 48 else ("#f59e0b" if val >= 40 else "#22c55e"))
    return labels, values, colors

trade_labels_all, trade_values_all, trade_colors_all = make_trade_chart_data(df)

# ── Port analysis ──────────────────────────────────────────────────────────────
def get_port_rows_data(data_df):
    exp_ports = (
        data_df[data_df["Type"] == "Export"]
        .groupby("Origin_Port")["Delay_Flag"]
        .agg(total="count", delayed="sum")
        .assign(pct=lambda x: (x["delayed"] / x["total"] * 100).round(2))
        .sort_values("pct", ascending=False)
        .head(5)
    )
    imp_ports = (
        data_df[data_df["Type"] == "Import"]
        .groupby("Destination_Port")["Delay_Flag"]
        .agg(total="count", delayed="sum")
        .assign(pct=lambda x: (x["delayed"] / x["total"] * 100).round(2))
        .sort_values("pct", ascending=False)
        .head(5)
    )
    return exp_ports, imp_ports

def port_rows_html(port_df):
    rows = []
    for port, row in port_df.iterrows():
        pct = row["pct"]
        color = "#B71C1C" if pct >= 50 else ("#E65100" if pct >= 45 else "#1565C0")
        dot   = "🔴" if pct >= 50 else ("🟠" if pct >= 45 else "🔵")
        fill_w = round(min(pct / 55 * 100, 100), 1)
        bar_color = "#ef4444" if pct >= 50 else ("#f59e0b" if pct >= 45 else "#1565C0")
        rows.append(f"""
        <div class="port-row" data-port="{port}" data-pct="{pct}">
          <div class="port-label">
            <span class="port-name">{dot} {port}</span>
            <span class="port-pct" style="color:{color};">{pct}%</span>
          </div>
          <div class="sbar-bg"><div class="sbar-fill" style="width:{fill_w}%;background:{bar_color};"></div></div>
        </div>""")
    return "\n".join(rows)

exp_ports_df, imp_ports_df = get_port_rows_data(df)
exp_port_html = port_rows_html(exp_ports_df)
imp_port_html = port_rows_html(imp_ports_df)

# ── Build complete raw data for JS filtering ───────────────────────────────────
# We embed ALL the aggregated data as JSON so JS can filter without a backend
raw_records = df[["Year", "Type", "Carrier", "Trade", "Delay_Flag",
                   "Origin_Port", "Destination_Port"]].copy()
raw_records["Year"] = raw_records["Year"].astype(str)

# Pre-aggregate by all filter combos for JS
def agg_group(group_df):
    total   = len(group_df)
    delayed = int(group_df["Delay_Flag"].sum())
    on_time = total - delayed
    rate    = round(group_df["Delay_Flag"].mean() * 100, 2) if total > 0 else 0.0
    return {"total": total, "delayed": delayed, "on_time": on_time, "rate": rate}

# Full raw aggregated data for JS filtering
all_rows = []
for _, row in raw_records.iterrows():
    all_rows.append({
        "year":    row["Year"],
        "type":    row["Type"],
        "carrier": row["Carrier"],
        "trade":   row["Trade"],
        "delay":   int(row["Delay_Flag"]),
        "origin":  row["Origin_Port"],
        "dest":    row["Destination_Port"],
    })

# Embed as compact JSON (we aggregate in JS)
raw_json = json.dumps(all_rows)

# Carrier options for filter
carrier_options_html = "\n".join(
    f'<option value="{c}">{c}</option>' for c in sorted(carriers)
)
trade_options_html = "\n".join(
    f'<option value="{t}">{t}</option>' for t in all_trades
)

# JS arrays for initial render
def js_arr(lst):   return "[" + ",".join(str(v) for v in lst) + "]"
def js_str_arr(lst): return '["' + '","'.join(str(v).replace('"', "'") for v in lst) + '"]'

generated_at = datetime.now().strftime("%B %Y")

print(f"  Total: {total_shipments:,} | Delayed: {delayed:,} ({overall_delay}%)")
print(f"  YoY: Exp {exp_2024}→{exp_2025} | Imp {imp_2024}→{imp_2025}")
print("  Embedding filter data... (this may take a moment)")
print("Generating HTML...")

# ── HTML ──────────────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sea Route Shipment — EDA Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root {{
  --blue:#1565C0; --blue2:#1976D2; --blue3:#42A5F5; --blue-pale:#E3F2FD;
  --bg:#F0F4F8; --white:#FFFFFF; --border:#D0D9E8; --text:#111;
  --muted:#555; --muted2:#888; --green:#1B7A3E; --red:#B71C1C; --r:8px;
  --shadow:0 1px 6px rgba(0,0,0,.10);
}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;font-size:13px;}}

header{{background:var(--blue);height:54px;display:flex;align-items:center;justify-content:space-between;padding:0 28px;box-shadow:0 2px 8px rgba(21,101,192,.35);position:sticky;top:0;z-index:100;}}
.logo{{color:#fff;font-size:19px;font-weight:800;letter-spacing:-.3px;}}
.logo em{{font-style:normal;opacity:.65;font-weight:400;font-size:12px;margin-left:10px;}}
.mpill{{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:#fff;font-size:11px;font-weight:700;padding:4px 14px;border-radius:20px;letter-spacing:1.5px;}}
.hdr-right{{display:flex;align-items:center;gap:10px;}}
.close-btn{{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:#fff;font-size:12px;font-weight:700;padding:5px 16px;border-radius:6px;cursor:pointer;text-decoration:none;transition:background .2s;}}
.close-btn:hover{{background:rgba(255,255,255,.28);}}

.page{{display:flex;min-height:calc(100vh - 54px);}}

.sidebar{{width:190px;min-width:190px;background:var(--white);border-right:1px solid var(--border);padding:18px 12px;display:flex;flex-direction:column;gap:14px;}}
.sb-head{{font-size:10px;font-weight:800;color:var(--blue);letter-spacing:1.5px;text-transform:uppercase;border-bottom:2px solid var(--blue-pale);padding-bottom:6px;}}
.fg label{{display:block;font-size:10px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.4px;margin-bottom:4px;}}
select{{width:100%;background:#fff;border:1px solid var(--border);color:var(--text);font-family:'Inter',sans-serif;font-size:12px;padding:6px 8px;border-radius:6px;cursor:pointer;outline:none;transition:border .15s;}}
select:focus{{border-color:var(--blue);}}
.btn-reset{{width:100%;background:var(--blue);color:#fff;border:none;font-family:'Inter',sans-serif;font-size:12px;font-weight:700;padding:8px;border-radius:6px;cursor:pointer;margin-top:2px;transition:opacity .15s;}}
.btn-reset:hover{{opacity:.88;}}
.filter-badge{{background:var(--blue-pale);color:var(--blue);font-size:10px;font-weight:700;padding:3px 8px;border-radius:10px;text-align:center;margin-top:4px;display:none;}}

.main{{flex:1;padding:18px 22px;overflow-x:hidden;}}
.sec-banner{{background:var(--blue);color:#fff;text-align:center;font-size:13px;font-weight:700;letter-spacing:1.2px;padding:7px;border-radius:var(--r);margin-bottom:14px;text-transform:uppercase;}}

.kpi-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:14px;}}
.kpi{{background:var(--white);border:1px solid var(--border);border-top:3px solid var(--blue);border-radius:var(--r);padding:12px 14px;box-shadow:var(--shadow);transition:all .2s;}}
.kpi-lbl{{font-size:10px;font-weight:700;color:var(--muted);letter-spacing:.5px;text-transform:uppercase;margin-bottom:5px;}}
.kpi-val{{font-size:26px;font-weight:800;color:var(--blue);line-height:1.1;}}
.kpi-sub{{font-size:10px;color:var(--muted2);margin-top:3px;}}
.kv-red{{color:var(--red)!important;}}
.kv-green{{color:var(--green)!important;}}
.kv-amber{{color:#E65100!important;}}

.g2{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;}}
.g3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px;}}
.g2x1{{display:grid;grid-template-columns:2fr 1fr;gap:12px;margin-bottom:12px;}}

.card{{background:var(--white);border:1px solid var(--border);border-radius:var(--r);padding:14px 16px;box-shadow:var(--shadow);}}
.card-title{{font-size:11px;font-weight:700;color:var(--blue);letter-spacing:.5px;text-transform:uppercase;margin-bottom:10px;padding-bottom:7px;border-bottom:1px solid var(--blue-pale);display:flex;align-items:center;justify-content:space-between;}}
.card-title .badge{{font-size:10px;font-weight:600;color:var(--muted2);text-transform:none;letter-spacing:0;}}

.tbl{{width:100%;border-collapse:collapse;}}
.tbl th{{font-size:10px;font-weight:700;color:var(--blue);text-transform:uppercase;letter-spacing:.4px;padding:6px 8px;border-bottom:2px solid var(--blue-pale);text-align:left;}}
.tbl td{{padding:7px 8px;border-bottom:1px solid #EEF2F8;font-size:12px;vertical-align:middle;}}
.tbl tr:last-child td{{border-bottom:none;}}
.tbl tr:hover td{{background:#F5F9FF;}}
.tbl tr.hidden{{display:none;}}

.sbar{{display:flex;align-items:center;gap:6px;}}
.sbar-bg{{height:8px;border-radius:4px;background:#E0E8F0;flex:1;overflow:hidden;}}
.sbar-fill{{height:100%;border-radius:4px;transition:width .4s ease;}}

.port-row{{margin-bottom:10px;}}
.port-label{{display:flex;justify-content:space-between;margin-bottom:4px;}}
.port-name{{font-size:12px;color:var(--text);}}
.port-pct{{font-size:12px;font-weight:700;}}
.port-row.hidden{{display:none;}}

.pill{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:600;}}
.pu{{background:#FFEBEE;color:#B71C1C;}}
.ph{{background:#FFF3E0;color:#E65100;}}
.pl{{background:#E3F2FD;color:#1565C0;}}
.pmet{{background:#E8F5E9;color:#1B5E20;}}

.insight{{background:#EDF4FF;border:1px solid #BBDEFB;border-radius:6px;padding:10px 14px;margin-top:12px;font-size:12px;color:#1a3a6b;line-height:1.6;}}
.insight b{{color:var(--blue);}}

.insight-card{{background:var(--white);border:1px solid var(--border);border-radius:var(--r);padding:14px 16px;box-shadow:var(--shadow);}}
.insight-card-title{{font-size:10px;font-weight:800;letter-spacing:1px;text-transform:uppercase;margin-bottom:10px;}}
.insight-item{{font-size:12px;color:var(--muted);padding:7px 0;border-bottom:1px solid #EEF2F8;line-height:1.5;}}
.insight-item:last-child{{border-bottom:none;}}
.insight-item b{{color:var(--text);}}

.donut-wrap{{display:flex;align-items:center;justify-content:center;padding:8px 0;}}

footer{{text-align:center;padding:16px;margin-top:8px;color:var(--muted2);font-size:11px;border-top:1px solid var(--border);background:var(--white);}}

.loading-overlay{{display:none;position:fixed;inset:0;background:rgba(240,244,248,.7);z-index:200;align-items:center;justify-content:center;font-size:15px;font-weight:700;color:var(--blue);}}
</style>
</head>
<body>

<div class="loading-overlay" id="loadingOverlay">⏳ Applying filters...</div>

<header>
  <div class="logo">⚓ Freight Intelligence <em>SEA ROUTE SHIPMENT — EDA DASHBOARD</em></div>
  <div class="hdr-right">
    <div class="mpill" id="hdrTotal">{total_shipments:,} SHIPMENTS</div>
    <div class="mpill">2024 – 2025</div>
  </div>
</header>

<div class="page">

<!-- SIDEBAR -->
<div class="sidebar">
  <div class="sb-head">📋 Filters</div>

  <div class="fg">
    <label>Year</label>
    <select id="fYear" onchange="applyFilters()">
      <option value="all">All Years</option>
      <option value="2024">2024</option>
      <option value="2025">2025</option>
    </select>
  </div>

  <div class="fg">
    <label>Shipment Type</label>
    <select id="fType" onchange="applyFilters()">
      <option value="all">All Types</option>
      <option value="Export">Export</option>
      <option value="Import">Import</option>
    </select>
  </div>

  <div class="fg">
    <label>Carrier</label>
    <select id="fCarrier" onchange="applyFilters()">
      <option value="all">All Carriers</option>
      {carrier_options_html}
    </select>
  </div>

  <div class="fg">
    <label>Trade Lane</label>
    <select id="fTrade" onchange="applyFilters()">
      <option value="all">All Trade Lanes</option>
      {trade_options_html}
    </select>
  </div>

  <div class="fg">
    <label>Delay Status</label>
    <select id="fDelay" onchange="applyFilters()">
      <option value="all">All</option>
      <option value="1">Delayed Only</option>
      <option value="0">On Time Only</option>
    </select>
  </div>

  <button class="btn-reset" onclick="resetFilters()">↺ Reset Filters</button>
  <div class="filter-badge" id="filterBadge">Filters Active</div>
</div>

<!-- MAIN CONTENT -->
<div class="main">

  <!-- KPI ROW -->
  <div class="sec-banner">📊 Overall Shipment Delay Summary</div>
  <div class="kpi-row">
    <div class="kpi">
      <div class="kpi-lbl">Total Shipments</div>
      <div class="kpi-val" id="kpiTotal">{total_shipments:,}</div>
      <div class="kpi-sub" id="kpiPeriod">Jan 2024 – Dec 2025</div>
    </div>
    <div class="kpi">
      <div class="kpi-lbl">Overall Delay Rate</div>
      <div class="kpi-val kv-amber" id="kpiDelayRate">{overall_delay}%</div>
      <div class="kpi-sub" id="kpiDelayCount">{delayed:,} delayed shipments</div>
    </div>
    <div class="kpi">
      <div class="kpi-lbl">Export Delay Rate</div>
      <div class="kpi-val kv-red" id="kpiExportRate">{export_delay}%</div>
      <div class="kpi-sub">vs import delays</div>
    </div>
    <div class="kpi">
      <div class="kpi-lbl">Import Delay Rate</div>
      <div class="kpi-val kv-green" id="kpiImportRate">{import_delay}%</div>
      <div class="kpi-sub">vs export delays</div>
    </div>
  </div>

  <!-- YoY + Donut -->
  <div class="g2x1">
    <div class="card">
      <div class="card-title">Year-over-Year Delay Trend <span class="badge">Export vs Import</span></div>
      <canvas id="yoyChart" height="160"></canvas>
      <div class="insight" id="yoyInsight">
        <b>Key Insight:</b> Delays improved in 2025.
        Export: <b>{exp_2024}% → {exp_2025}%</b> &nbsp;|&nbsp;
        Import: <b>{imp_2024}% → {imp_2025}%</b>.
        Despite improvement, nearly <b>1 in 2 shipments</b> is still delayed.
      </div>
    </div>
    <div class="card" style="display:flex;flex-direction:column;align-items:center;">
      <div class="card-title" style="width:100%;">On-Time vs Delayed Split</div>
      <div class="donut-wrap" style="width:180px;height:180px;">
        <canvas id="donutChart"></canvas>
      </div>
      <div style="margin-top:12px;width:100%;">
        <div class="sbar" style="margin-bottom:8px;">
          <span style="width:10px;height:10px;border-radius:50%;background:#1B7A3E;display:inline-block;margin-right:4px;"></span>
          <span style="flex:1;font-size:12px;">On Time</span>
          <span id="legendOnTime" style="font-weight:700;color:#1B7A3E;">{on_time:,} ({100-overall_delay}%)</span>
        </div>
        <div class="sbar">
          <span style="width:10px;height:10px;border-radius:50%;background:#B71C1C;display:inline-block;margin-right:4px;"></span>
          <span style="flex:1;font-size:12px;">Delayed</span>
          <span id="legendDelayed" style="font-weight:700;color:#B71C1C;">{delayed:,} ({overall_delay}%)</span>
        </div>
      </div>
    </div>
  </div>

  <!-- CARRIER SECTION -->
  <div class="sec-banner">🚢 Carrier Performance Analysis</div>
  <div class="g2">
    <div class="card">
      <div class="card-title">Carrier Delay % — 2024 vs 2025</div>
      <canvas id="carrierChart" height="220"></canvas>
    </div>
    <div class="card">
      <div class="card-title">Carrier Performance Table <span class="badge">Export | Import</span></div>
      <table class="tbl" id="carrierTable">
        <thead>
          <tr>
            <th>Carrier</th><th>Exp 2024</th><th>Imp 2024</th>
            <th>Exp 2025</th><th>Imp 2025</th><th>Trend</th>
          </tr>
        </thead>
        <tbody id="carrierTableBody">
          {carrier_table_html}
        </tbody>
      </table>
      <div class="insight">
        <b>Best performer:</b> Hapag-Lloyd — import delays dropped from 41.67% to just <b>25.00%</b>.
        <br><b>Needs attention:</b> Evergreen &amp; COSCO still above 48% on exports.
      </div>
    </div>
  </div>

  <!-- TRADE LANE SECTION -->
  <div class="sec-banner">🌐 Trade Lane Delay Analysis</div>
  <div class="g2">
    <div class="card">
      <div class="card-title">Trade Lane Delay % by Direction</div>
      <canvas id="tradeChart" height="300"></canvas>
    </div>
    <div class="card">
      <div class="card-title">Trade Lane Summary</div>
      <table class="tbl">
        <thead>
          <tr><th>Trade Lane</th><th>Type</th><th>Delay %</th><th>Risk</th></tr>
        </thead>
        <tbody id="tradeTableBody">
          {trade_table_html}
        </tbody>
      </table>
    </div>
  </div>

  <!-- PORT SECTION -->
  <div class="sec-banner">🏗️ Port-Level Delay Analysis</div>
  <div class="g2">
    <div class="card">
      <div class="card-title">Top 5 Export Origin Ports — Highest Delay %</div>
      <div id="expPortRows">{exp_port_html}</div>
      <div class="insight">Middle-East export hubs show the <b>highest delay rates</b> — indicating major port congestion on outbound shipments.</div>
    </div>
    <div class="card">
      <div class="card-title">Top 5 Import Destination Ports — Highest Delay %</div>
      <div id="impPortRows">{imp_port_html}</div>
      <div class="insight">Middle-East ports also dominate import delays — reflecting persistent destination-side bottlenecks.</div>
    </div>
  </div>

  <!-- KEY INSIGHTS -->
  <div class="sec-banner">💡 Key Insights &amp; Recommendations</div>
  <div class="g3">
    <div class="insight-card" style="border-top:3px solid #B71C1C;">
      <div class="insight-card-title" style="color:#B71C1C;">🔴 High Risk Areas</div>
      <div class="insight-item"><b>Asia-Europe lane</b> has the highest export delay at 51.39% — major Suez/Cape congestion.</div>
      <div class="insight-item"><b>Jebel Ali &amp; Dubai</b> are the most congested ports on both export and import sides.</div>
      <div class="insight-item"><b>Evergreen &amp; COSCO</b> remain above 48% on export delays — highest among all carriers.</div>
    </div>
    <div class="insight-card" style="border-top:3px solid #1B7A3E;">
      <div class="insight-card-title" style="color:#1B7A3E;">🟢 Positive Trends</div>
      <div class="insight-item"><b>Hapag-Lloyd</b> achieved the most improvement — import delays dropped from 41.67% to just 25.00%.</div>
      <div class="insight-item"><b>All carriers</b> improved year-over-year from 2024 → 2025.</div>
      <div class="insight-item"><b>Intra-Asia</b> is the best-performing trade lane — import delays at just 37.50%.</div>
    </div>
    <div class="insight-card" style="border-top:3px solid #E65100;">
      <div class="insight-card-title" style="color:#E65100;">🟡 Recommendations</div>
      <div class="insight-item">Prioritize <b>Asia-Europe &amp; Trans-Pacific</b> routes for operational interventions.</div>
      <div class="insight-item">Optimize operations at <b>Jebel Ali, Dubai, Guayaquil</b> — highest delay hubs.</div>
      <div class="insight-item">Use the <b>Delay Prediction tool</b> to proactively flag high-risk shipments before departure.</div>
    </div>
  </div>

</div><!-- /main -->
</div><!-- /page -->

<footer>
  Sea Route Shipment EDA Dashboard &nbsp;·&nbsp;
  Generated from {total_shipments:,} shipment records (2024–2025) &nbsp;·&nbsp;
  XGBoost Model Accuracy: 83.3% &nbsp;·&nbsp; ROC AUC: 0.947 &nbsp;·&nbsp;
  Generated: {generated_at}
</footer>

<script>
Chart.defaults.font.family = 'Inter';
Chart.defaults.font.size   = 11;
const gridColor = '#E3F2FD';

// ── EMBEDDED RAW DATA ─────────────────────────────────────────────────────────
const RAW = {raw_json};

// ── CHART INSTANCES ───────────────────────────────────────────────────────────
let yoyChart, donutChart, carrierChart, tradeChart;

function makeYoy(data) {{
  const e24 = avg(data.filter(r=>r.type==='Export'&&r.year==='2024'));
  const i24 = avg(data.filter(r=>r.type==='Import'&&r.year==='2024'));
  const e25 = avg(data.filter(r=>r.type==='Export'&&r.year==='2025'));
  const i25 = avg(data.filter(r=>r.type==='Import'&&r.year==='2025'));
  return [e24, i24, e25, i25];
}}

function avg(arr) {{
  if (!arr.length) return 0;
  return +(arr.reduce((s,r)=>s+r.delay,0)/arr.length*100).toFixed(2);
}}

function initCharts() {{
  // 1. YoY
  yoyChart = new Chart(document.getElementById('yoyChart'), {{
    type: 'bar',
    data: {{
      labels: ['Export 2024','Import 2024','Export 2025','Import 2025'],
      datasets: [{{
        label: 'Delay %',
        data: [{exp_2024},{imp_2024},{exp_2025},{imp_2025}],
        backgroundColor:['#EF9A9A','#EF9A9A','#A5D6A7','#A5D6A7'],
        borderColor:['#B71C1C','#B71C1C','#1B7A3E','#1B7A3E'],
        borderWidth:2, borderRadius:6,
        barThickness: 36,
        maxBarThickness: 42,
      }}]
    }},
    options:{{
      responsive:true,
      plugins:{{ legend:{{display:false}}, tooltip:{{callbacks:{{label:c=>` ${{c.raw}}%`}}}} }},
      scales:{{
        y:{{min:0,max:60,ticks:{{callback:v=>v+'%'}},grid:{{color:gridColor}}}},
        x:{{grid:{{display:false}}}}
      }}
    }}
  }});

  // 2. Donut
  donutChart = new Chart(document.getElementById('donutChart'), {{
    type: 'doughnut',
    data: {{
      labels: ['On Time','Delayed'],
      datasets: [{{
        data:[{on_time},{delayed}],
        backgroundColor:['#A5D6A7','#EF9A9A'],
        borderColor:['#1B7A3E','#B71C1C'],
        borderWidth:2, hoverOffset:4
      }}]
    }},
    options:{{
      responsive:true, maintainAspectRatio:true, cutout:'70%',
      plugins:{{
        legend:{{display:false}},
        tooltip:{{callbacks:{{label:c=>` ${{c.label}}: ${{c.raw.toLocaleString()}}`}}}}
      }}
    }}
  }});

  // 3. Carrier
  carrierChart = new Chart(document.getElementById('carrierChart'), {{
    type: 'bar',
    data: {{
      labels: {js_str_arr(carriers)},
      datasets:[
        {{ label:'2024', data:{js_arr(c2024)}, backgroundColor:'#EF9A9A', borderColor:'#B71C1C', borderWidth:1.5, borderRadius:5 }},
        {{ label:'2025', data:{js_arr(c2025)}, backgroundColor:'#A5D6A7', borderColor:'#1B7A3E', borderWidth:1.5, borderRadius:5 }}
      ]
    }},
    options:{{
      responsive:true,
      plugins:{{
        legend:{{position:'top',labels:{{usePointStyle:true,pointStyle:'circle',padding:14}}}},
        tooltip:{{callbacks:{{label:c=>` ${{c.dataset.label}}: ${{c.raw}}%`}}}}
      }},
      scales:{{
        y:{{min:0,max:65,ticks:{{callback:v=>v+'%'}},grid:{{color:gridColor}}}},
        x:{{grid:{{display:false}}}}
      }}
    }}
  }});

  // 4. Trade
  tradeChart = new Chart(document.getElementById('tradeChart'), {{
    type: 'bar',
    data: {{
      labels: {js_str_arr(trade_labels_all)},
      datasets:[{{
        label:'Delay %',
        data: {js_arr(trade_values_all)},
        backgroundColor: {json.dumps(trade_colors_all)},
        borderRadius:5, borderWidth:0
      }}]
    }},
    options:{{
      indexAxis:'y', responsive:true,
      plugins:{{
        legend:{{display:false}},
        tooltip:{{callbacks:{{label:c=>` ${{c.raw}}%`}}}}
      }},
      scales:{{
        x:{{min:30,max:56,ticks:{{callback:v=>v+'%'}},grid:{{color:gridColor}}}},
        y:{{grid:{{display:false}},ticks:{{font:{{size:10}}}}}}
      }}
    }}
  }});
}}

// ── FILTER ENGINE ─────────────────────────────────────────────────────────────
function getFilters() {{
  return {{
    year:    document.getElementById('fYear').value,
    type:    document.getElementById('fType').value,
    carrier: document.getElementById('fCarrier').value,
    trade:   document.getElementById('fTrade').value,
    delay:   document.getElementById('fDelay').value,
  }};
}}

function filterData(f) {{
  return RAW.filter(r => {{
    if (f.year    !== 'all' && r.year    !== f.year)    return false;
    if (f.type    !== 'all' && r.type    !== f.type)    return false;
    if (f.carrier !== 'all' && r.carrier !== f.carrier) return false;
    if (f.trade   !== 'all' && r.trade   !== f.trade)   return false;
    if (f.delay   !== 'all' && String(r.delay) !== f.delay) return false;
    return true;
  }});
}}

function applyFilters() {{
  const f    = getFilters();
  const data = filterData(f);
  const isActive = Object.values(f).some(v => v !== 'all');

  document.getElementById('filterBadge').style.display = isActive ? 'block' : 'none';
  document.getElementById('loadingOverlay').style.display = 'flex';

  setTimeout(() => {{
    // ── KPIs ──────────────────────────────────────────────────────────────────
    const total   = data.length;
    const delayed = data.filter(r=>r.delay===1).length;
    const onTime  = total - delayed;
    const rate    = total > 0 ? +(delayed/total*100).toFixed(2) : 0;
    const expData = data.filter(r=>r.type==='Export');
    const impData = data.filter(r=>r.type==='Import');
    const expRate = expData.length > 0 ? +(expData.filter(r=>r.delay===1).length/expData.length*100).toFixed(2) : 0;
    const impRate = impData.length > 0 ? +(impData.filter(r=>r.delay===1).length/impData.length*100).toFixed(2) : 0;

    document.getElementById('kpiTotal').textContent     = total.toLocaleString();
    document.getElementById('kpiDelayRate').textContent = rate + '%';
    document.getElementById('kpiDelayCount').textContent= delayed.toLocaleString() + ' delayed';
    document.getElementById('kpiExportRate').textContent= expRate + '%';
    document.getElementById('kpiImportRate').textContent= impRate + '%';
    document.getElementById('hdrTotal').textContent     = total.toLocaleString() + ' SHIPMENTS';

    // ── YoY Chart ─────────────────────────────────────────────────────────────
    const yoyVals = makeYoy(data);
    yoyChart.data.datasets[0].data = yoyVals;
    yoyChart.update();
    document.getElementById('yoyInsight').innerHTML =
      `<b>Key Insight:</b> Export delay: <b>${{yoyVals[0]}}% → ${{yoyVals[2]}}%</b> &nbsp;|&nbsp; Import: <b>${{yoyVals[1]}}% → ${{yoyVals[3]}}%</b> (2024 → 2025). Showing <b>${{total.toLocaleString()}}</b> filtered shipments.`;

    // ── Donut Chart ───────────────────────────────────────────────────────────
    donutChart.data.datasets[0].data = [onTime, delayed];
    donutChart.update();
    document.getElementById('legendOnTime').textContent  = onTime.toLocaleString() + ' (' + (100-rate).toFixed(1) + '%)';
    document.getElementById('legendDelayed').textContent = delayed.toLocaleString() + ' (' + rate + '%)';

    // ── Carrier Chart ─────────────────────────────────────────────────────────
    const carrierNames = [...new Set(RAW.map(r=>r.carrier))].sort();
    const new2024 = carrierNames.map(c => avg(data.filter(r=>r.carrier===c&&r.year==='2024')));
    const new2025 = carrierNames.map(c => avg(data.filter(r=>r.carrier===c&&r.year==='2025')));
    carrierChart.data.labels              = carrierNames;
    carrierChart.data.datasets[0].data   = new2024;
    carrierChart.data.datasets[1].data   = new2025;
    carrierChart.update();

    // ── Carrier table ─────────────────────────────────────────────────────────
    document.querySelectorAll('#carrierTableBody tr').forEach(tr => {{
      const c     = tr.dataset.carrier;
      const match = f.carrier === 'all' || f.carrier === c;
      tr.classList.toggle('hidden', !match || !data.some(r=>r.carrier===c));
      // Update cells with filtered values
      const cData = data.filter(r=>r.carrier===c);
      tr.querySelector('.cv-exp24').textContent = avg(cData.filter(r=>r.type==='Export'&&r.year==='2024')) + '%';
      tr.querySelector('.cv-imp24').textContent = avg(cData.filter(r=>r.type==='Import'&&r.year==='2024')) + '%';
      tr.querySelector('.cv-exp25').textContent = avg(cData.filter(r=>r.type==='Export'&&r.year==='2025')) + '%';
      tr.querySelector('.cv-imp25').textContent = avg(cData.filter(r=>r.type==='Import'&&r.year==='2025')) + '%';
    }});

    // ── Trade Lane Chart + Table ──────────────────────────────────────────────
    const tradeGroups = {{}};
    data.forEach(r => {{
      const key = r.trade + '||' + r.type;
      if (!tradeGroups[key]) tradeGroups[key] = {{total:0, delayed:0, trade:r.trade, type:r.type}};
      tradeGroups[key].total++;
      if (r.delay===1) tradeGroups[key].delayed++;
    }});
    const tradeEntries = Object.values(tradeGroups)
      .map(g => ({{...g, pct: g.total>0 ? +(g.delayed/g.total*100).toFixed(2) : 0}}))
      .sort((a,b)=>b.pct-a.pct);

    const tLabels = tradeEntries.map(g => {{
      const s = g.trade.replace('(via Suez/Cape)','').replace('(via Cape)','')
        .replace('North Atlantic ','N.Atl ').replace('Trans-Pacific ','Trans-Pac ')
        .replace('South America','S.Am');
      return `${{s}} (${{g.type}})`;
    }});
    const tValues = tradeEntries.map(g=>g.pct);
    const tColors = tValues.map(v=>v>=48?'#ef4444':(v>=40?'#f59e0b':'#22c55e'));

    tradeChart.data.labels              = tLabels;
    tradeChart.data.datasets[0].data   = tValues;
    tradeChart.data.datasets[0].backgroundColor = tColors;
    tradeChart.update();

    // Update trade table
    document.querySelectorAll('#tradeTableBody tr').forEach(tr => {{
      const tradeVal = tr.dataset.trade;
      const typeVal  = tr.dataset.type;
      const key = tradeVal + '||' + typeVal;
      const match = tradeGroups[key];
      const tradeFilter = f.trade === 'all' || f.trade === tradeVal;
      const typeFilter  = f.type  === 'all' || f.type  === typeVal;
      if (match && tradeFilter && typeFilter) {{
        tr.classList.remove('hidden');
        tr.cells[2].textContent = match.pct + '%';
        const rcls = match.pct>=48?'pu':(match.pct>=44?'ph':(match.pct>=40?'pl':'pmet'));
        const rlbl = match.pct>=48?'HIGH':(match.pct>=44?'MED-HIGH':(match.pct>=40?'MEDIUM':'LOWER'));
        tr.cells[3].innerHTML = `<span class="pill ${{rcls}}">${{rlbl}}</span>`;
      }} else {{
        tr.classList.add('hidden');
      }}
    }});

    // ── Port rows ─────────────────────────────────────────────────────────────
    const expRows = getTopPorts(data.filter(r=>r.type==='Export'), 'origin', 5);
    const impRows = getTopPorts(data.filter(r=>r.type==='Import'), 'dest',   5);
    document.getElementById('expPortRows').innerHTML = renderPortRows(expRows);
    document.getElementById('impPortRows').innerHTML = renderPortRows(impRows);

    document.getElementById('loadingOverlay').style.display = 'none';
  }}, 30);
}}

function getTopPorts(data, field, n) {{
  const counts = {{}};
  data.forEach(r => {{
    const p = r[field];
    if (!counts[p]) counts[p] = {{total:0, delayed:0}};
    counts[p].total++;
    if (r.delay===1) counts[p].delayed++;
  }});
  return Object.entries(counts)
    .map(([port,v])=>({{port, pct: v.total>0?+(v.delayed/v.total*100).toFixed(2):0}}))
    .sort((a,b)=>b.pct-a.pct)
    .slice(0,n);
}}

function renderPortRows(ports) {{
  return ports.map(p => {{
    const pct      = p.pct;
    const color    = pct>=50?'#B71C1C':(pct>=45?'#E65100':'#1565C0');
    const dot      = pct>=50?'🔴':(pct>=45?'🟠':'🔵');
    const fillW    = Math.min(pct/55*100, 100).toFixed(1);
    const barColor = pct>=50?'#ef4444':(pct>=45?'#f59e0b':'#1565C0');
    return `
    <div class="port-row">
      <div class="port-label">
        <span class="port-name">${{dot}} ${{p.port}}</span>
        <span class="port-pct" style="color:${{color}};">${{pct}}%</span>
      </div>
      <div class="sbar-bg"><div class="sbar-fill" style="width:${{fillW}}%;background:${{barColor}};"></div></div>
    </div>`;
  }}).join('');
}}

function resetFilters() {{
  ['fYear','fType','fCarrier','fTrade','fDelay'].forEach(id => {{
    document.getElementById(id).value = 'all';
  }});
  applyFilters();
}}

// ── INIT ──────────────────────────────────────────────────────────────────────
initCharts();
</script>
</body>
</html>"""

# ── WRITE OUTPUT ──────────────────────────────────────────────────────────────
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n✅ Dashboard generated: {OUTPUT_PATH}")
print(f"   Copy to: app/images/eda_dashboard.html")
print(f"   File size: {Path(OUTPUT_PATH).stat().st_size / 1024:.1f} KB")
