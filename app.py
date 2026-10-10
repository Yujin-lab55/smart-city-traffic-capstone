from pathlib import Path
import logging

import joblib
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify

logger = logging.getLogger(__name__)
app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

model = joblib.load(
    BASE_DIR / "models" / "traffic_regression.joblib"
)
settings = joblib.load(
    BASE_DIR / "models" / "preparation_settings.joblib"
)
FEATURES = settings["feature_columns"]


@app.get("/health")
def health():
    return jsonify(status="ok", model="traffic_regression")


@app.post("/predict")
def predict():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify(error="Send one JSON object."), 400

    missing = [name for name in FEATURES if name not in payload]
    if missing:
        logger.warning("Missing input fields: %s", missing)
        return jsonify(error="Missing features", fields=missing), 400

    try:
        frame = pd.DataFrame(
            [{name: payload[name] for name in FEATURES}]
        )

        for name in FEATURES:
            if name == "weather_main":
                value = frame.at[0, name]
                if not isinstance(value, str) or not value.strip():
                    raise ValueError("weather_main must be non-empty text.")
                frame[name] = value.strip().lower()
            else:
                value = frame.at[0, name]
                if isinstance(value, (bool, list, dict)) or value is None:
                    raise ValueError(f"{name} must be a finite number.")
                value = float(value)
                if not np.isfinite(value):
                    raise ValueError(f"{name} must be a finite number.")
                frame[name] = value

    except (ValueError, TypeError) as exc:
        logger.warning("Invalid request: %s", exc)
        return jsonify(error=str(exc)), 400

    prediction = float(model.predict(frame[FEATURES])[0])
    logger.info("Traffic prediction completed: %.2f", prediction)

    return jsonify(
        predicted_traffic_volume=round(prediction, 2),
        model_version="v1",
        input_type="engineered_features",
        note="Educational prototype for the I-94 dataset."
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(
                BASE_DIR / "api.log", encoding="utf-8"
            ),
            logging.StreamHandler()
        ]
    )
    app.run(host="127.0.0.1", port=5001, debug=False)
