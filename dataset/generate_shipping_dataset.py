"""
Shipping Dataset Generator
Generates ~194,000 rows of realistic shipping data (Jan 2024 - Dec 2025)
Based on real carrier delay % per trade route and year.

Requirements: pip install pandas
Run: python generate_shipping_dataset.py
Output: shipping_dataset.csv
"""

import pandas as pd
import random
from datetime import datetime, timedelta
from itertools import product

# ── 1. TRADE ROUTES & PORTS ──────────────────────────────────────────────────

TRADE_ROUTES = [
    {
        "trade": "Trans-Pacific (Asia-NA)",
        "type": "Export",
        "origin_ports": [
            "Shanghai", "Ningbo", "Busan", "Yokohama", "Kaohsiung",
            "Yantian", "Shekou", "Xiamen", "Qingdao", "Tianjin",
            "Nansha", "Laem Chabang"
        ],
        "destination_ports": [
            "Los Angeles", "Long Beach", "Seattle", "Tacoma", "Oakland",
            "New York", "Norfolk", "Savannah", "Charleston", "Jacksonville",
            "Houston", "Miami", "Vancouver"
        ],
    },
    {
        "trade": "Asia-Europe (via Suez/Cape)",
        "type": "Export",
        "origin_ports": [
            "Shanghai", "Ningbo", "Busan", "Yokohama", "Kaohsiung",
            "Yantian", "Port Klang", "Singapore", "Ho Chi Minh",
            "Haiphong", "Dubai", "Jebel Ali"
        ],
        "destination_ports": [
            "Rotterdam", "Antwerp", "Hamburg", "Le Havre", "Southampton",
            "Felixstowe", "Valencia", "Algeciras", "Piraeus",
            "Barcelona", "Gdansk", "Tangier"
        ],
    },
    {
        "trade": "North Atlantic (Europe-NA)",
        "type": "Export",
        "origin_ports": [
            "Rotterdam", "Antwerp", "Hamburg", "Le Havre", "Southampton",
            "Felixstowe", "Bremerhaven", "Zeebrugge", "Lisbon",
            "Gdansk", "Leixoes"
        ],
        "destination_ports": [
            "New York", "Norfolk", "Baltimore", "Philadelphia", "Boston",
            "Halifax", "Montreal", "Halifax", "Jacksonville",
            "Savannah", "Charleston", "Houston"
        ],
    },
    {
        "trade": "Intra-Asia",
        "type": "Export",
        "origin_ports": [
            "Shanghai", "Ningbo", "Busan", "Yokohama", "Kaohsiung",
            "Yantian", "Port Klang", "Singapore", "Ho Chi Minh",
            "Haiphong", "Laem Chabang", "Jakarta"
        ],
        "destination_ports": [
            "Shanghai", "Ningbo", "Busan", "Yokohama", "Kaohsiung",
            "Yantian", "Port Klang", "Singapore", "Ho Chi Minh",
            "Haiphong", "Laem Chabang"
        ],
    },
    {
        "trade": "South America-Europe",
        "type": "Export",
        "origin_ports": [
            "Santos", "Itapoa", "Rio Grande", "Paranagua", "Buenos Aires",
            "Montevideo", "Callao", "Guayaquil", "Valparaiso", "San Antonio"
        ],
        "destination_ports": [
            "Rotterdam", "Antwerp", "Hamburg", "Le Havre", "Southampton",
            "Felixstowe", "Valencia", "Algeciras", "Piraeus",
            "Barcelona", "Tangier", "Gdansk"
        ],
    },
    {
        "trade": "Trans-Pacific (NA-Asia)",
        "type": "Import",
        "origin_ports": [
            "Los Angeles", "Long Beach", "Seattle", "Tacoma", "Oakland",
            "New York", "Norfolk", "Savannah", "Charleston", "Jacksonville",
            "Houston", "Miami", "Vancouver"
        ],
        "destination_ports": [
            "Shanghai", "Ningbo", "Busan", "Yokohama", "Kaohsiung",
            "Yantian", "Shekou", "Xiamen", "Qingdao", "Tianjin",
            "Nansha", "Laem Chabang"
        ],
    },
    {
        "trade": "Europe-Asia (via Cape)",
        "type": "Import",
        "origin_ports": [
            "Rotterdam", "Antwerp", "Hamburg", "Le Havre", "Southampton",
            "Felixstowe", "Valencia", "Algeciras", "Piraeus",
            "Barcelona", "Gdansk", "Tangier"
        ],
        "destination_ports": [
            "Shanghai", "Ningbo", "Busan", "Yokohama", "Kaohsiung",
            "Yantian", "Port Klang", "Singapore", "Ho Chi Minh",
            "Haiphong", "Dubai", "Jebel Ali"
        ],
    },
    {
        "trade": "North Atlantic (NA-Europe)",
        "type": "Import",
        "origin_ports": [
            "New York", "Norfolk", "Baltimore", "Philadelphia", "Boston",
            "Halifax", "Montreal", "Jacksonville", "Savannah",
            "Charleston", "Houston"
        ],
        "destination_ports": [
            "Rotterdam", "Antwerp", "Hamburg", "Le Havre", "Southampton",
            "Felixstowe", "Bremerhaven", "Zeebrugge", "Lisbon",
            "Gdansk", "Leixoes"
        ],
    },
    {
        "trade": "Intra-Asia",
        "type": "Import",
        "origin_ports": [
            "Shanghai", "Ningbo", "Busan", "Yokohama", "Kaohsiung",
            "Yantian", "Port Klang", "Singapore", "Ho Chi Minh",
            "Haiphong", "Laem Chabang"
        ],
        "destination_ports": [
            "Shanghai", "Ningbo", "Busan", "Yokohama", "Kaohsiung",
            "Yantian", "Port Klang", "Singapore", "Ho Chi Minh",
            "Haiphong", "Laem Chabang"
        ],
    },
    {
        "trade": "Europe-South America",
        "type": "Import",
        "origin_ports": [
            "Rotterdam", "Antwerp", "Hamburg", "Le Havre", "Southampton",
            "Felixstowe", "Valencia", "Algeciras", "Piraeus",
            "Barcelona", "Tangier", "Gdansk"
        ],
        "destination_ports": [
            "Santos", "Itapoa", "Rio Grande", "Paranagua", "Buenos Aires",
            "Montevideo", "Callao", "Guayaquil", "Valparaiso", "San Antonio"
        ],
    },
]

# ── 2. PORT → COUNTRY MAPPING ─────────────────────────────────────────────────

PORT_COUNTRY = {
    # China
    "Shanghai": "China", "Ningbo": "China", "Yantian": "China",
    "Shekou": "China", "Xiamen": "China", "Qingdao": "China",
    "Tianjin": "China", "Nansha": "China",
    # South Korea
    "Busan": "South Korea",
    # Japan
    "Yokohama": "Japan",
    # Taiwan
    "Kaohsiung": "Taiwan",
    # Thailand
    "Laem Chabang": "Thailand",
    # Malaysia
    "Port Klang": "Malaysia",
    # Singapore
    "Singapore": "Singapore",
    # Vietnam
    "Ho Chi Minh": "Vietnam", "Haiphong": "Vietnam",
    # UAE
    "Dubai": "UAE", "Jebel Ali": "UAE",
    # Indonesia
    "Jakarta": "Indonesia",
    # USA
    "Los Angeles": "USA", "Long Beach": "USA", "Seattle": "USA",
    "Tacoma": "USA", "Oakland": "USA", "New York": "USA",
    "Norfolk": "USA", "Savannah": "USA", "Charleston": "USA",
    "Jacksonville": "USA", "Houston": "USA", "Miami": "USA",
    "Baltimore": "USA", "Philadelphia": "USA", "Boston": "USA",
    # Canada
    "Vancouver": "Canada", "Halifax": "Canada", "Montreal": "Canada",
    # Netherlands
    "Rotterdam": "Netherlands",
    # Belgium
    "Antwerp": "Belgium", "Zeebrugge": "Belgium",
    # Germany
    "Hamburg": "Germany", "Bremerhaven": "Germany",
    # France
    "Le Havre": "France",
    # UK
    "Southampton": "UK", "Felixstowe": "UK",
    # Spain
    "Valencia": "Spain", "Algeciras": "Spain", "Barcelona": "Spain",
    # Greece
    "Piraeus": "Greece",
    # Poland
    "Gdansk": "Poland",
    # Morocco
    "Tangier": "Morocco",
    # Portugal
    "Lisbon": "Portugal", "Leixoes": "Portugal",
    # Brazil
    "Santos": "Brazil", "Itapoa": "Brazil", "Rio Grande": "Brazil",
    "Paranagua": "Brazil",
    # Argentina
    "Buenos Aires": "Argentina",
    # Uruguay
    "Montevideo": "Uruguay",
    # Peru
    "Callao": "Peru",
    # Ecuador
    "Guayaquil": "Ecuador",
    # Chile
    "Valparaiso": "Chile", "San Antonio": "Chile",
}

# ── 3. CARRIERS ───────────────────────────────────────────────────────────────

CARRIERS = [
    {"name": "MSC",         "prefix": "MS"},
    {"name": "Maersk",      "prefix": "MK"},
    {"name": "COSCO",       "prefix": "CO"},
    {"name": "CMA CGM",     "prefix": "CM"},
    {"name": "Hapag-Lloyd", "prefix": "HL"},
    {"name": "Evergreen",   "prefix": "EV"},
]

# ── 4. DELAY % PER CARRIER / TRADE / TYPE / YEAR ─────────────────────────────
# Key: (carrier_name, trade, type, year) → delay_pct (0-100)

DELAY_PCT = {
    # Trans-Pacific (Asia-NA) Export
    ("MSC",         "Trans-Pacific (Asia-NA)", "Export", 2024): 51.2,
    ("Maersk",      "Trans-Pacific (Asia-NA)", "Export", 2024): 48.6,
    ("COSCO",       "Trans-Pacific (Asia-NA)", "Export", 2024): 54.1,
    ("CMA CGM",     "Trans-Pacific (Asia-NA)", "Export", 2024): 52.8,
    ("Hapag-Lloyd", "Trans-Pacific (Asia-NA)", "Export", 2024): 49.5,
    ("Evergreen",   "Trans-Pacific (Asia-NA)", "Export", 2024): 55.6,
    ("MSC",         "Trans-Pacific (Asia-NA)", "Export", 2025): 44.5,
    ("Maersk",      "Trans-Pacific (Asia-NA)", "Export", 2025): 35.1,
    ("COSCO",       "Trans-Pacific (Asia-NA)", "Export", 2025): 49.2,
    ("CMA CGM",     "Trans-Pacific (Asia-NA)", "Export", 2025): 43.7,
    ("Hapag-Lloyd", "Trans-Pacific (Asia-NA)", "Export", 2025): 32.8,
    ("Evergreen",   "Trans-Pacific (Asia-NA)", "Export", 2025): 48.1,
    # Asia-Europe (via Suez/Cape) Export
    ("MSC",         "Asia-Europe (via Suez/Cape)", "Export", 2024): 56.3,
    ("Maersk",      "Asia-Europe (via Suez/Cape)", "Export", 2024): 53.2,
    ("COSCO",       "Asia-Europe (via Suez/Cape)", "Export", 2024): 58.7,
    ("CMA CGM",     "Asia-Europe (via Suez/Cape)", "Export", 2024): 55.4,
    ("Hapag-Lloyd", "Asia-Europe (via Suez/Cape)", "Export", 2024): 52.1,
    ("Evergreen",   "Asia-Europe (via Suez/Cape)", "Export", 2024): 59.2,
    ("MSC",         "Asia-Europe (via Suez/Cape)", "Export", 2025): 49.1,
    ("Maersk",      "Asia-Europe (via Suez/Cape)", "Export", 2025): 40.4,
    ("COSCO",       "Asia-Europe (via Suez/Cape)", "Export", 2025): 52.3,
    ("CMA CGM",     "Asia-Europe (via Suez/Cape)", "Export", 2025): 46.8,
    ("Hapag-Lloyd", "Asia-Europe (via Suez/Cape)", "Export", 2025): 38.2,
    ("Evergreen",   "Asia-Europe (via Suez/Cape)", "Export", 2025): 51.6,
    # North Atlantic (Europe-NA) Export
    ("MSC",         "North Atlantic (Europe-NA)", "Export", 2024): 47.8,
    ("Maersk",      "North Atlantic (Europe-NA)", "Export", 2024): 45.1,
    ("COSCO",       "North Atlantic (Europe-NA)", "Export", 2024): 50.4,
    ("CMA CGM",     "North Atlantic (Europe-NA)", "Export", 2024): 48.2,
    ("Hapag-Lloyd", "North Atlantic (Europe-NA)", "Export", 2024): 44.9,
    ("Evergreen",   "North Atlantic (Europe-NA)", "Export", 2024): 51.3,
    ("MSC",         "North Atlantic (Europe-NA)", "Export", 2025): 40.3,
    ("Maersk",      "North Atlantic (Europe-NA)", "Export", 2025): 33.7,
    ("COSCO",       "North Atlantic (Europe-NA)", "Export", 2025): 45.9,
    ("CMA CGM",     "North Atlantic (Europe-NA)", "Export", 2025): 41.5,
    ("Hapag-Lloyd", "North Atlantic (Europe-NA)", "Export", 2025): 28.6,
    ("Evergreen",   "North Atlantic (Europe-NA)", "Export", 2025): 46.2,
    # Intra-Asia Export
    ("MSC",         "Intra-Asia", "Export", 2024): 43.1,
    ("Maersk",      "Intra-Asia", "Export", 2024): 40.5,
    ("COSCO",       "Intra-Asia", "Export", 2024): 46.2,
    ("CMA CGM",     "Intra-Asia", "Export", 2024): 44.3,
    ("Hapag-Lloyd", "Intra-Asia", "Export", 2024): 41.2,
    ("Evergreen",   "Intra-Asia", "Export", 2024): 47.1,
    ("MSC",         "Intra-Asia", "Export", 2025): 36.7,
    ("Maersk",      "Intra-Asia", "Export", 2025): 29.8,
    ("COSCO",       "Intra-Asia", "Export", 2025): 41.4,
    ("CMA CGM",     "Intra-Asia", "Export", 2025): 37.9,
    ("Hapag-Lloyd", "Intra-Asia", "Export", 2025): 26.1,
    ("Evergreen",   "Intra-Asia", "Export", 2025): 42.5,
    # South America-Europe Export
    ("MSC",         "South America-Europe", "Export", 2024): 52.0,
    ("Maersk",      "South America-Europe", "Export", 2024): 49.4,
    ("COSCO",       "South America-Europe", "Export", 2024): 54.8,
    ("CMA CGM",     "South America-Europe", "Export", 2024): 51.7,
    ("Hapag-Lloyd", "South America-Europe", "Export", 2024): 48.6,
    ("Evergreen",   "South America-Europe", "Export", 2024): 55.4,
    ("MSC",         "South America-Europe", "Export", 2025): 47.6,
    ("Maersk",      "South America-Europe", "Export", 2025): 38.2,
    ("COSCO",       "South America-Europe", "Export", 2025): 50.7,
    ("CMA CGM",     "South America-Europe", "Export", 2025): 45.3,
    ("Hapag-Lloyd", "South America-Europe", "Export", 2025): 34.9,
    ("Evergreen",   "South America-Europe", "Export", 2025): 50.1,
    # Trans-Pacific (NA-Asia) Import
    ("MSC",         "Trans-Pacific (NA-Asia)", "Import", 2024): 44.8,
    ("Maersk",      "Trans-Pacific (NA-Asia)", "Import", 2024): 42.3,
    ("COSCO",       "Trans-Pacific (NA-Asia)", "Import", 2024): 48.7,
    ("CMA CGM",     "Trans-Pacific (NA-Asia)", "Import", 2024): 46.2,
    ("Hapag-Lloyd", "Trans-Pacific (NA-Asia)", "Import", 2024): 41.9,
    ("Evergreen",   "Trans-Pacific (NA-Asia)", "Import", 2024): 50.2,
    ("MSC",         "Trans-Pacific (NA-Asia)", "Import", 2025): 38.9,
    ("Maersk",      "Trans-Pacific (NA-Asia)", "Import", 2025): 31.4,
    ("COSCO",       "Trans-Pacific (NA-Asia)", "Import", 2025): 43.6,
    ("CMA CGM",     "Trans-Pacific (NA-Asia)", "Import", 2025): 38.1,
    ("Hapag-Lloyd", "Trans-Pacific (NA-Asia)", "Import", 2025): 25.2,
    ("Evergreen",   "Trans-Pacific (NA-Asia)", "Import", 2025): 42.7,
    # Europe-Asia (via Cape) Import
    ("MSC",         "Europe-Asia (via Cape)", "Import", 2024): 46.5,
    ("Maersk",      "Europe-Asia (via Cape)", "Import", 2024): 43.9,
    ("COSCO",       "Europe-Asia (via Cape)", "Import", 2024): 50.1,
    ("CMA CGM",     "Europe-Asia (via Cape)", "Import", 2024): 47.6,
    ("Hapag-Lloyd", "Europe-Asia (via Cape)", "Import", 2024): 43.3,
    ("Evergreen",   "Europe-Asia (via Cape)", "Import", 2024): 51.8,
    ("MSC",         "Europe-Asia (via Cape)", "Import", 2025): 39.8,
    ("Maersk",      "Europe-Asia (via Cape)", "Import", 2025): 32.6,
    ("COSCO",       "Europe-Asia (via Cape)", "Import", 2025): 44.8,
    ("CMA CGM",     "Europe-Asia (via Cape)", "Import", 2025): 39.4,
    ("Hapag-Lloyd", "Europe-Asia (via Cape)", "Import", 2025): 26.7,
    ("Evergreen",   "Europe-Asia (via Cape)", "Import", 2025): 44.3,
    # North Atlantic (NA-Europe) Import
    ("MSC",         "North Atlantic (NA-Europe)", "Import", 2024): 42.7,
    ("Maersk",      "North Atlantic (NA-Europe)", "Import", 2024): 40.2,
    ("COSCO",       "North Atlantic (NA-Europe)", "Import", 2024): 45.9,
    ("CMA CGM",     "North Atlantic (NA-Europe)", "Import", 2024): 43.8,
    ("Hapag-Lloyd", "North Atlantic (NA-Europe)", "Import", 2024): 39.6,
    ("Evergreen",   "North Atlantic (NA-Europe)", "Import", 2024): 47.5,
    ("MSC",         "North Atlantic (NA-Europe)", "Import", 2025): 36.4,
    ("Maersk",      "North Atlantic (NA-Europe)", "Import", 2025): 28.9,
    ("COSCO",       "North Atlantic (NA-Europe)", "Import", 2025): 41.2,
    ("CMA CGM",     "North Atlantic (NA-Europe)", "Import", 2025): 36.7,
    ("Hapag-Lloyd", "North Atlantic (NA-Europe)", "Import", 2025): 23.4,
    ("Evergreen",   "North Atlantic (NA-Europe)", "Import", 2025): 40.8,
    # Intra-Asia Import
    ("MSC",         "Intra-Asia", "Import", 2024): 40.6,
    ("Maersk",      "Intra-Asia", "Import", 2024): 38.1,
    ("COSCO",       "Intra-Asia", "Import", 2024): 43.8,
    ("CMA CGM",     "Intra-Asia", "Import", 2024): 41.7,
    ("Hapag-Lloyd", "Intra-Asia", "Import", 2024): 37.8,
    ("Evergreen",   "Intra-Asia", "Import", 2024): 45.2,
    ("MSC",         "Intra-Asia", "Import", 2025): 34.2,
    ("Maersk",      "Intra-Asia", "Import", 2025): 27.3,
    ("COSCO",       "Intra-Asia", "Import", 2025): 39.1,
    ("CMA CGM",     "Intra-Asia", "Import", 2025): 35.4,
    ("Hapag-Lloyd", "Intra-Asia", "Import", 2025): 22.6,
    ("Evergreen",   "Intra-Asia", "Import", 2025): 40.2,
    # Europe-South America Import
    ("MSC",         "Europe-South America", "Import", 2024): 45.3,
    ("Maersk",      "Europe-South America", "Import", 2024): 42.8,
    ("COSCO",       "Europe-South America", "Import", 2024): 49.1,
    ("CMA CGM",     "Europe-South America", "Import", 2024): 46.9,
    ("Hapag-Lloyd", "Europe-South America", "Import", 2024): 44.2,
    ("Evergreen",   "Europe-South America", "Import", 2024): 50.7,
    ("MSC",         "Europe-South America", "Import", 2025): 39.2,
    ("Maersk",      "Europe-South America", "Import", 2025): 32.1,
    ("COSCO",       "Europe-South America", "Import", 2025): 44.3,
    ("CMA CGM",     "Europe-South America", "Import", 2025): 38.8,
    ("Hapag-Lloyd", "Europe-South America", "Import", 2025): 27.5,
    ("Evergreen",   "Europe-South America", "Import", 2025): 43.9,
}

# ── 5. TRANSIT DAYS PER TRADE ROUTE ──────────────────────────────────────────
# (min, max) in days

TRANSIT_DAYS = {
    "Trans-Pacific (Asia-NA)":    (14, 18),
    "Asia-Europe (via Suez/Cape)":(28, 35),
    "North Atlantic (Europe-NA)": (7,  10),
    "Intra-Asia":                 (4,  8),
    "South America-Europe":       (18, 24),
    "Trans-Pacific (NA-Asia)":    (14, 18),
    "Europe-Asia (via Cape)":     (32, 38),
    "North Atlantic (NA-Europe)": (7,  10),
    "Europe-South America":       (18, 24),
}

# ── 6. FREIGHT RATES PER TRADE ROUTE & CONTAINER TYPE ────────────────────────
# Realistic 2024/2025 market ranges (USD)
# Format: (min, max)

FREIGHT_RATES = {
    ("Trans-Pacific (Asia-NA)",    "20GP"): (1800, 4500),
    ("Trans-Pacific (Asia-NA)",    "40GP"): (3200, 7500),
    ("Trans-Pacific (Asia-NA)",    "40HC"): (3500, 8200),
    ("Asia-Europe (via Suez/Cape)","20GP"): (1500, 5800),
    ("Asia-Europe (via Suez/Cape)","40GP"): (2800, 9500),
    ("Asia-Europe (via Suez/Cape)","40HC"): (3000, 10500),
    ("North Atlantic (Europe-NA)", "20GP"): (900,  1800),
    ("North Atlantic (Europe-NA)", "40GP"): (1600, 3200),
    ("North Atlantic (Europe-NA)", "40HC"): (1800, 3500),
    ("Intra-Asia",                 "20GP"): (300,  800),
    ("Intra-Asia",                 "40GP"): (550,  1400),
    ("Intra-Asia",                 "40HC"): (600,  1600),
    ("South America-Europe",       "20GP"): (1200, 3500),
    ("South America-Europe",       "40GP"): (2200, 5800),
    ("South America-Europe",       "40HC"): (2400, 6200),
    ("Trans-Pacific (NA-Asia)",    "20GP"): (800,  2200),
    ("Trans-Pacific (NA-Asia)",    "40GP"): (1400, 3800),
    ("Trans-Pacific (NA-Asia)",    "40HC"): (1600, 4200),
    ("Europe-Asia (via Cape)",     "20GP"): (1400, 4200),
    ("Europe-Asia (via Cape)",     "40GP"): (2600, 7200),
    ("Europe-Asia (via Cape)",     "40HC"): (2800, 7800),
    ("North Atlantic (NA-Europe)", "20GP"): (900,  1800),
    ("North Atlantic (NA-Europe)", "40GP"): (1600, 3200),
    ("North Atlantic (NA-Europe)", "40HC"): (1800, 3500),
    ("Europe-South America",       "20GP"): (1100, 3200),
    ("Europe-South America",       "40GP"): (2000, 5400),
    ("Europe-South America",       "40HC"): (2200, 5800),
}

# ── 7. DELAY REASONS BY SEVERITY ─────────────────────────────────────────────

DELAY_REASONS = {
    "minor":    ["Port Congestion", "Weather Delay", "Berth Waiting"],
    "moderate": ["Equipment Failure", "Customs Hold", "Berth Delay",
                 "Vessel Schedule Change", "Cargo Documentation Issue"],
    "severe":   ["Canal Disruption", "Strike Action", "Severe Weather",
                 "Port Strike", "Geopolitical Disruption"],
}

# Routes more prone to severe delays
SEVERE_ROUTES = {"Asia-Europe (via Suez/Cape)", "Europe-Asia (via Cape)"}

# ── 8. CONTAINER TYPES ────────────────────────────────────────────────────────

CONTAINER_TYPES = ["20GP", "40GP", "40HC"]
CONTAINER_WEIGHTS = [0.25, 0.45, 0.30]  # 40GP most common

# ── 9. MONTHS (Jan 2024 – Dec 2025) ──────────────────────────────────────────

MONTHS_2024 = [datetime(2024, m, 1) for m in range(1, 13)]
MONTHS_2025 = [datetime(2025, m, 1) for m in range(1, 13)]
ALL_MONTHS  = MONTHS_2024 + MONTHS_2025

# ── 10. HELPER FUNCTIONS ──────────────────────────────────────────────────────

def get_delay_days(trade, is_severe_bias=False):
    """Return realistic delay days based on severity distribution."""
    r = random.random()
    if is_severe_bias:
        if r < 0.20:
            return random.randint(13, 21), "severe"
        elif r < 0.55:
            return random.randint(6, 12), "moderate"
        else:
            return random.randint(1, 5), "minor"
    else:
        if r < 0.10:
            return random.randint(13, 21), "severe"
        elif r < 0.40:
            return random.randint(6, 12), "moderate"
        else:
            return random.randint(1, 5), "minor"

def get_etd(month_dt):
    """Random departure day within the month (1st–28th)."""
    day = random.randint(1, 28)
    return month_dt.replace(day=day)

def get_transit(trade):
    """Random transit days within route range."""
    lo, hi = TRANSIT_DAYS.get(trade, (10, 20))
    return random.randint(lo, hi)

def get_freight(trade, container):
    key = (trade, container)
    lo, hi = FREIGHT_RATES.get(key, (500, 2000))
    return round(random.uniform(lo, hi), 2)

def get_fuel(freight):
    """BAF: 8–15% of base freight."""
    return round(freight * random.uniform(0.08, 0.15), 2)

def get_congestion():
    """USD 150–450 per container, delayed only."""
    return round(random.uniform(150, 450), 2)

def build_delay_schedule(carrier, trade, shipment_type, year):
    """
    Build a list of 12 booleans (one per month) where True = delayed.
    The number of True values matches the delay % from real data as closely as possible.
    """
    key = (carrier, trade, shipment_type, year)
    pct = DELAY_PCT.get(key, 50.0)
    n_delayed = round(pct / 100 * 12)
    schedule = [True] * n_delayed + [False] * (12 - n_delayed)
    random.shuffle(schedule)
    return schedule

# ── 11. MAIN GENERATION ───────────────────────────────────────────────────────

def generate():
    random.seed(42)  # reproducible output

    rows = []
    carrier_counters = {c["prefix"]: 1 for c in CARRIERS}

    for carrier in CARRIERS:
        cname  = carrier["name"]
        prefix = carrier["prefix"]

        for route in TRADE_ROUTES:
            trade         = route["trade"]
            shipment_type = route["type"]
            origin_ports  = route["origin_ports"]
            dest_ports    = route["destination_ports"]

            is_severe_bias = trade in SEVERE_ROUTES

            # Build delay schedules per year (12 booleans each)
            sched_2024 = build_delay_schedule(cname, trade, shipment_type, 2024)
            sched_2025 = build_delay_schedule(cname, trade, shipment_type, 2025)

            # Month → delay flag lookup
            month_delay = {}
            for i, m in enumerate(MONTHS_2024):
                month_delay[m] = sched_2024[i]
            for i, m in enumerate(MONTHS_2025):
                month_delay[m] = sched_2025[i]

            # All port pair combinations
            port_pairs = list(product(origin_ports, dest_ports))

            for (orig, dest) in port_pairs:
                # Skip same-port pairs (Intra-Asia)
                if orig == dest:
                    continue

                for month_dt in ALL_MONTHS:
                    is_delayed = month_delay[month_dt]

                    # Shipment ID
                    seq = carrier_counters[prefix]
                    shipment_id = f"{prefix}{seq:04d}"
                    carrier_counters[prefix] += 1

                    # Container
                    container = random.choices(CONTAINER_TYPES,
                                               weights=CONTAINER_WEIGHTS, k=1)[0]

                    # Dates
                    etd = get_etd(month_dt)
                    transit = get_transit(trade)
                    eta = etd + timedelta(days=transit)

                    if is_delayed:
                        delay_days, severity = get_delay_days(trade, is_severe_bias)
                        actual_arrival = eta + timedelta(days=delay_days)
                        delay_flag = 1
                        delay_reason = random.choice(DELAY_REASONS[severity])
                    else:
                        delay_days = 0
                        delay_flag = 0
                        delay_reason = "On Time"
                        actual_arrival = eta

                    # Charges
                    freight   = get_freight(trade, container)
                    fuel      = get_fuel(freight)
                    congestion = get_congestion() if is_delayed else 0.0
                    total     = round(freight + fuel + congestion, 2)

                    rows.append({
                        "Shipment_ID":          shipment_id,
                        "Carrier":              cname,
                        "Origin_Port":          orig,
                        "Origin_Country":       PORT_COUNTRY.get(orig, "Unknown"),
                        "Destination_Port":     dest,
                        "Destination_Country":  PORT_COUNTRY.get(dest, "Unknown"),
                        "Container_Type":       container,
                        "Type":                 shipment_type,
                        "ETD":                  etd.strftime("%Y-%m-%d"),
                        "ETA":                  eta.strftime("%Y-%m-%d"),
                        "Actual_Arrival":       actual_arrival.strftime("%Y-%m-%d"),
                        "Delay_Flag":           delay_flag,
                        "Delay_Days":           delay_days,
                        "Delay_Reason":         delay_reason,
                        "Basic_Ocean_Freight_USD": freight,
                        "Fuel_Charges_USD":     fuel,
                        "Congestion_Charges_USD": congestion,
                        "Total_Charges_USD":    total,
                        "Trade":                trade,
                    })

        print(f"  ✓ {cname} done — running total: {len(rows):,} rows")

    df = pd.DataFrame(rows)
    output_file = "shipping_dataset.csv"
    df.to_csv(output_file, index=False)
    print(f"\n✅ Dataset saved → {output_file}")
    print(f"   Total rows : {len(df):,}")
    print(f"   Columns    : {list(df.columns)}")
    print(f"\nSample (first 3 rows):")
    print(df.head(3).to_string(index=False))

if __name__ == "__main__":
    print("🚢 Generating shipping dataset...\n")
    generate()
