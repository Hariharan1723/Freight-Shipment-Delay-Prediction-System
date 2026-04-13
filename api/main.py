from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from datetime import datetime
import logging

from pipeline.prediction_pipeline import predict_delay
from app.mysql_connection import get_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Freight Delay Prediction API", redirect_slashes=False)


class ShipmentInput(BaseModel):
    origin: str
    destination: str
    carrier: str
    container: str
    shipment_date: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/predict")
def predict_shipment(data: ShipmentInput):
    logger.info(f"Received prediction request: {data}")
    start_time = datetime.now()

    try:
        input_df = pd.DataFrame({
            "Origin_Port":      [data.origin],
            "Destination_Port": [data.destination],
            "Carrier":          [data.carrier],
            "Container_Type":   [data.container],
            "ETD":              [data.shipment_date]
        })

        prediction, probability = predict_delay(input_df)

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

    end_time = datetime.now()

    # ── Save to MySQL ──
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shipment_predictions (
                id                 INT AUTO_INCREMENT PRIMARY KEY,
                origin_port        VARCHAR(100),
                destination_port   VARCHAR(100),
                carrier            VARCHAR(100),
                container_type     VARCHAR(50),
                shipment_date      VARCHAR(50),
                delay_prediction   INT,
                delay_probability  FLOAT,
                start_time         DATETIME,
                end_time           DATETIME,
                created_at         DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        query = """
            INSERT INTO shipment_predictions
            (origin_port, destination_port, carrier, container_type,
             shipment_date, delay_prediction, delay_probability, start_time, end_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data.origin, data.destination, data.carrier, data.container,
            data.shipment_date, int(prediction), float(probability),
            start_time, end_time
        )
        cursor.execute(query, values)
        conn.commit()
        logger.info("Prediction saved to MySQL successfully.")

    except Exception as e:
        logger.error(f"Failed to save to MySQL: {e}")
        # Don't raise — still return prediction even if DB fails

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    return {
        "prediction":  int(prediction),
        "probability": float(probability)
    }