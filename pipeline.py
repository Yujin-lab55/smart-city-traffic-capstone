from pathlib import Path
import logging
import pandas as pd

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent

EXPECTED_COLUMNS = [
    "holiday", "temp", "rain_1h", "snow_1h", "clouds_all",
    "weather_main", "weather_description",
    "date_time", "traffic_volume"
]


def configure_logging():
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    logger.setLevel(logging.INFO)
    logger.propagate = False

    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(
        BASE_DIR / "pipeline.log",
        mode="a",
        encoding="utf-8"
    )

    for handler in (console_handler, file_handler):
        handler.setFormatter(formatter)
        logger.addHandler(handler)


def load_and_validate(csv_path):
    # Preserve the literal holiday value "None".
    df = pd.read_csv(csv_path, keep_default_na=False)

    logger.info(
        "Loaded CSV: %s | rows=%d | columns=%d",
        csv_path.name, df.shape[0], df.shape[1]
    )

    # Validate the schema before cleaning or transforming data.
    missing_columns = [
        column for column in EXPECTED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    logger.info("Schema validation passed: all 9 required columns exist")
    return df


def main():
    configure_logging()
    csv_path = BASE_DIR / "data" / "Metro_Interstate_Traffic_Volume.csv"

    try:
        df = load_and_validate(csv_path)
        logger.info(
            "Loading and validation completed: %d records",
            len(df)
        )
        return 0

    except (OSError, ValueError, pd.errors.ParserError) as exc:
        logger.error(
            "Pipeline failed: %s", exc, exc_info=True
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
