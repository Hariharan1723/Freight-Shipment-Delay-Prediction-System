import joblib
import pandas as pd
from pathlib import Path

from .feature_engineering import create_features

BASE_DIR  = Path(__file__).resolve().parents[1]
MODEL_DIR = BASE_DIR / "Model"

# ── Load model artifacts ───────────────────────────────────────────────────────
model          = joblib.load(MODEL_DIR / "freight_delay_model.pkl")
encoder        = joblib.load(MODEL_DIR / "ohe_encoder.pkl")
target_encoder = joblib.load(MODEL_DIR / "target_encoder.pkl")


def predict_delay(input_df: pd.DataFrame):
    """
    Takes raw user input DataFrame with columns:
        Origin_Port, Destination_Port, Carrier, Container_Type, ETD

    Returns:
        prediction  (int)   — 1 = Delayed, 0 = On Time
        probability (float) — delay probability (0.0 to 1.0)
    """
    df = create_features(input_df.copy())

    # ── Target Encoding (high cardinality columns) ────────────────────────────
    te_cols = ["Origin_Port", "Destination_Port", "Route", "Carrier_Route"]
    df[te_cols] = target_encoder.transform(df[te_cols])

    # ── One-Hot Encoding (low cardinality columns) ────────────────────────────
    ohe_cols   = ["Carrier", "Trade", "Container_Type"]
    encoded    = encoder.transform(df[ohe_cols])
    encoded_df = pd.DataFrame(
        encoded,
        columns=encoder.get_feature_names_out(ohe_cols),
        index=df.index
    )
    df = df.drop(columns=ohe_cols)
    df = pd.concat([df, encoded_df], axis=1)

    # ── Drop raw ETD (already extracted into day/month/quarter features) ───────
    if "ETD" in df.columns:
        df = df.drop(columns=["ETD"])

    # ── Align to model's expected feature order ───────────────────────────────
    # Use the feature names the XGBoost model was trained on
    expected_cols = model.get_booster().feature_names

    # Add any columns the model expects but are missing (fill with 0)
    for col in expected_cols:
        if col not in df.columns:
            df[col] = 0

    # Drop any extra columns not expected by the model
    df = df[expected_cols]

    # ── Predict ───────────────────────────────────────────────────────────────
    prediction  = model.predict(df)
    probability = model.predict_proba(df)[:, 1]

    return int(prediction[0]), float(probability[0])
