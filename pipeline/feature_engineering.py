import pandas as pd
import joblib
from pathlib import Path

BASE_DIR   = Path(__file__).resolve().parents[1]
rate_maps  = joblib.load(BASE_DIR / "Model" / "rate_maps.pkl")

# Pull each lookup dict and the global mean from rate_maps
_carrier_route_map  = rate_maps.get("carrier_route_rate",  {})
_origin_port_map    = rate_maps.get("origin_port_rate",    {})
_dest_port_map      = rate_maps.get("dest_port_rate",      {})
_carrier_map        = rate_maps.get("carrier_rate",        {})
_route_map          = rate_maps.get("route_rate",          {})
GLOBAL_DELAY_MEAN   = rate_maps.get("global_mean",         0.43)   # fallback for unknown routes

# ── Trade Lane Mapping ────────────────────────────────────────────────────────
# Covers all 9 trade lanes present in the training dataset
ROUTES = {
    "Trans-Pacific (Asia-NA)": {
        "origin":      ["Shanghai", "Ningbo", "Busan", "Yokohama", "Kaohsiung",
                        "Yantian", "Shekou", "Xiamen", "Qingdao", "Tianjin"],
        "destination": ["Los Angeles", "Long Beach", "Seattle", "Tacoma", "Oakland",
                        "New York", "Norfolk", "Savannah", "Charleston", "Jacksonville"]
    },
    "Trans-Pacific (NA-Asia)": {
        "origin":      ["Los Angeles", "Long Beach", "Seattle", "Tacoma", "Oakland",
                        "New York", "Norfolk", "Savannah", "Charleston", "Jacksonville"],
        "destination": ["Shanghai", "Ningbo", "Busan", "Yokohama", "Kaohsiung",
                        "Yantian", "Shekou", "Xiamen", "Qingdao", "Tianjin"]
    },
    "Asia-Europe (via Suez/Cape)": {
        "origin":      ["Shanghai", "Ningbo", "Busan", "Yokohama", "Kaohsiung",
                        "Yantian", "Port Klang", "Singapore", "Ho Chi Minh", "Haiphong"],
        "destination": ["Rotterdam", "Antwerp", "Hamburg", "Le Havre", "Southampton",
                        "Felixstowe", "Valencia", "Algeciras", "Piraeus", "Barcelona"]
    },
    "Europe-Asia (via Cape)": {
        "origin":      ["Rotterdam", "Antwerp", "Hamburg", "Le Havre", "Southampton",
                        "Felixstowe", "Valencia", "Algeciras", "Piraeus", "Barcelona"],
        "destination": ["Shanghai", "Ningbo", "Busan", "Yokohama", "Kaohsiung",
                        "Yantian", "Port Klang", "Singapore", "Ho Chi Minh", "Haiphong"]
    },
    "North Atlantic (Europe-NA)": {
        "origin":      ["Rotterdam", "Antwerp", "Hamburg", "Le Havre", "Southampton",
                        "Felixstowe", "Bremerhaven", "Zeebrugge", "Lisbon", "Gdansk"],
        "destination": ["New York", "Norfolk", "Baltimore", "Philadelphia", "Boston",
                        "Halifax", "Jacksonville", "Savannah", "Charleston", "Houston"]
    },
    "North Atlantic (NA-Europe)": {
        "origin":      ["New York", "Norfolk", "Baltimore", "Philadelphia", "Boston",
                        "Halifax", "Jacksonville", "Savannah", "Charleston", "Houston"],
        "destination": ["Rotterdam", "Antwerp", "Hamburg", "Le Havre", "Southampton",
                        "Felixstowe", "Bremerhaven", "Zeebrugge", "Lisbon", "Gdansk"]
    },
    "Intra-Asia": {
        "origin":      ["Shanghai", "Ningbo", "Busan", "Yokohama", "Kaohsiung",
                        "Yantian", "Port Klang", "Singapore", "Ho Chi Minh", "Haiphong"],
        "destination": ["Shanghai", "Ningbo", "Busan", "Yokohama", "Kaohsiung",
                        "Yantian", "Port Klang", "Singapore", "Ho Chi Minh", "Laem Chabang"]
    },
    "South America-Europe": {
        "origin":      ["Santos", "Itapoa", "Rio Grande", "Paranagua", "Buenos Aires",
                        "Montevideo", "Callao", "Guayaquil", "Valparaiso", "San Antonio"],
        "destination": ["Rotterdam", "Antwerp", "Hamburg", "Le Havre", "Southampton",
                        "Felixstowe", "Valencia", "Algeciras", "Piraeus", "Barcelona"]
    },
    "Europe-South America": {
        "origin":      ["Rotterdam", "Antwerp", "Hamburg", "Le Havre", "Southampton",
                        "Felixstowe", "Valencia", "Algeciras", "Piraeus", "Barcelona"],
        "destination": ["Santos", "Itapoa", "Rio Grande", "Paranagua", "Buenos Aires",
                        "Montevideo", "Callao", "Guayaquil", "Valparaiso", "San Antonio"]
    },
}


def get_trade(origin: str, destination: str) -> str:
    """Derive trade lane from origin and destination port names."""
    for trade, data in ROUTES.items():
        if origin in data["origin"] and destination in data["destination"]:
            return trade
    # Fallback: use the most common trade lane in training data
    return "Trans-Pacific (Asia-NA)"


def get_shipment_type(origin: str, destination: str) -> int:
    """
    Determine shipment type based on direction.
    Export (1): Asia/Americas/Europe → other regions
    Import (0): arriving into destination region
    Uses a simple heuristic — same as training data encoding.
    """
    asia_ports = [
        "Shanghai", "Ningbo", "Busan", "Yokohama", "Kaohsiung", "Yantian",
        "Shekou", "Xiamen", "Qingdao", "Tianjin", "Port Klang", "Singapore",
        "Ho Chi Minh", "Haiphong", "Laem Chabang"
    ]
    # If origin is in Asia → Export
    if origin in asia_ports:
        return 1
    return 0


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes raw user input DataFrame and engineers all features
    required by the XGBoost model.

    Expected input columns:
        Origin_Port, Destination_Port, Carrier, Container_Type, ETD
    """
    df = df.copy()

    # ── Date features ─────────────────────────────────────────────────────────
    df["ETD"]         = pd.to_datetime(df["ETD"], dayfirst=True, errors="coerce")
    df["ETD_Day"]     = df["ETD"].dt.day
    df["ETD_Month"]   = df["ETD"].dt.month
    df["ETD_Weekday"] = df["ETD"].dt.weekday
    df["ETD_Quarter"] = df["ETD"].dt.quarter

    # ── Route combinations ────────────────────────────────────────────────────
    df["Route"]        = df["Origin_Port"] + "_" + df["Destination_Port"]
    df["Carrier_Route"] = df["Carrier"] + "_" + df["Route"]

    # ── Trade lane (derived from port names) ──────────────────────────────────
    df["Trade"] = df.apply(
        lambda row: get_trade(row["Origin_Port"], row["Destination_Port"]), axis=1
    )

    # ── Shipment type (Export=1 / Import=0) ───────────────────────────────────
    df["Type"] = df.apply(
        lambda row: get_shipment_type(row["Origin_Port"], row["Destination_Port"]), axis=1
    )

    # ── Seasonal features ─────────────────────────────────────────────────────
    df["Peak_Season"] = df["ETD_Month"].apply(lambda x: 1 if x in [8, 9, 10, 11] else 0)
    df["Is_Weekend"]  = df["ETD_Weekday"].apply(lambda x: 1 if x >= 5 else 0)

    # ── Historical delay rates (from training data — no leakage) ──────────────
    df["Carrier_Route_Delay_Rate"]    = df["Carrier_Route"].map(_carrier_route_map).fillna(GLOBAL_DELAY_MEAN)
    df["Origin_Port_Delay_Rate"]      = df["Origin_Port"].map(_origin_port_map).fillna(GLOBAL_DELAY_MEAN)
    df["Destination_Port_Delay_Rate"] = df["Destination_Port"].map(_dest_port_map).fillna(GLOBAL_DELAY_MEAN)
    df["Carrier_Delay_Rate"]          = df["Carrier"].map(_carrier_map).fillna(GLOBAL_DELAY_MEAN)
    df["Route_Delay_Rate"]            = df["Route"].map(_route_map).fillna(GLOBAL_DELAY_MEAN)

    return df
