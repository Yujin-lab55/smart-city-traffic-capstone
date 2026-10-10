from pathlib import Path
import argparse
import json
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent


def create_features(df):
    logger.info("Before feature engineering: rows=%d | columns=%d", *df.shape)
    df = df.copy()

    df["date_time"] = pd.to_datetime(df["date_time"], errors="raise")
    if df.empty or df["date_time"].isna().any():
        raise ValueError("Empty dataset or missing timestamps")

    # Time features: Monday=0, Sunday=6.
    df["hour"] = df["date_time"].dt.hour
    df["day_of_week"] = df["date_time"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    # Cyclical encoding preserves the connection between 23:00 and 00:00.
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["day_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["day_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)

    # Propagate a holiday label to all observed hours of that date.
    dates = df["date_time"].dt.normalize()
    labelled = ~df["holiday"].str.lower().isin(["none", "unknown", ""])
    holiday_dates = dates[labelled].unique()
    df["is_holiday"] = dates.isin(holiday_dates).astype(int)

    # Weather features.
    df["temperature_c"] = df["temp"] - 273.15
    df["is_raining"] = (df["rain_1h"] > 0).astype(int)
    df["is_snowing"] = (df["snow_1h"] > 0).astype(int)

    weather_columns = pd.get_dummies(
        df["weather_main"],
        prefix="weather",
        dtype=int
    )
    df = pd.concat([df, weather_columns], axis=1)

    # Scale two continuous variables for Part 2 exploration.
    scaling = {}
    for column in ["temp", "rain_1h"]:
        minimum = float(df[column].min())
        maximum = float(df[column].max())
        span = maximum - minimum

        df[f"{column}_scaled"] = (
            (df[column] - minimum) / span if span > 0 else 0.0
        )
        scaling[column] = {"min": minimum, "max": maximum}
        logger.debug(
            "Scaling %s: min=%.4f | max=%.4f",
            column, minimum, maximum
        )

    # Data-driven target categories, based on traffic quartiles.
    q1, q2, q3 = df["traffic_volume"].quantile([0.25, 0.50, 0.75])
    df["congestion_category"] = np.select(
        [
            df["traffic_volume"] <= q1,
            df["traffic_volume"] <= q2,
            df["traffic_volume"] <= q3
        ],
        ["Low", "Moderate", "High"],
        default="Severe"
    )
    logger.debug(
        "Traffic quartiles: Q1=%.2f | Q2=%.2f | Q3=%.2f",
        q1, q2, q3
    )

    metadata = {
        "scaling": scaling,
        "traffic_quartiles": {
            "q1": float(q1),
            "q2": float(q2),
            "q3": float(q3)
        },
        "category_rule": (
            "Low <= Q1; Moderate > Q1 and <= Q2; "
            "High > Q2 and <= Q3; Severe > Q3"
        ),
        "scope": (
            "Part 2 exploratory features fitted on the cleaned dataset. "
            "For Part 3, fit learned preprocessing on training data only. "
            "Do not use traffic_volume or congestion_category as predictors "
            "of traffic_volume."
        )
    }

    logger.info("After feature engineering: rows=%d | columns=%d", *df.shape)
    return df, metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    # Configure handlers only when this script is the entry point.
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                BASE_DIR / "pipeline.log", mode="a", encoding="utf-8"
            )
        ],
        force=True
    )

    try:
        folder = BASE_DIR / "data" / "processed"
        df = pd.read_csv(
            folder / "traffic_cleaned.csv",
            keep_default_na=False
        )
        featured, metadata = create_features(df)

        output_path = folder / "traffic_features.csv"
        featured.to_csv(output_path, index=False)
        logger.info("Saved feature dataset: %s", output_path)

        metadata_path = folder / "feature_metadata.json"
        metadata_path.write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8"
        )
        logger.info("Saved feature definitions: %s", metadata_path)
        return 0

    except (OSError, ValueError, KeyError, TypeError) as exc:
        logger.error("Feature engineering failed: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
