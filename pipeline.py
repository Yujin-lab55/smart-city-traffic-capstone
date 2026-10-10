from pathlib import Path
import logging
import numpy as np
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

    handlers = [
        logging.StreamHandler(),
        logging.FileHandler(
            BASE_DIR / "pipeline.log",
            mode="a",
            encoding="utf-8"
        )
    ]

    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)


def log_change(count, reason):
    if count:
        logger.warning("Affected rows=%d | %s", count, reason)
    else:
        logger.info("Affected rows=0 | %s", reason)


def load_and_validate(csv_path):
    df = pd.read_csv(csv_path, keep_default_na=False)
    logger.info(
        "Loaded CSV: rows=%d | columns=%d",
        *df.shape
    )

    missing = [
        column for column in EXPECTED_COLUMNS
        if column not in df.columns
    ]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if df.empty:
        raise ValueError("The CSV contains no records")

    logger.info("Schema validation passed")
    return df


def clean_data(df):
    df = df.copy()

    # Standardise text while preserving the holiday label "None".
    for column in ["holiday", "weather_main", "weather_description"]:
        original = df[column].astype("string")
        cleaned = (
            original.str.strip()
            .str.replace(r"\s+", " ", regex=True)
            .str.lower()
            .fillna("unknown")
            .replace("", "unknown")
        )
        changed = int(original.ne(cleaned).fillna(True).sum())
        df[column] = cleaned
        log_change(changed, f"Standardised text in {column}")

    # Parse dates and remove unusable timestamps.
    df["date_time"] = pd.to_datetime(
        df["date_time"],
        format="%Y-%m-%d %H:%M:%S",
        errors="coerce"
    )
    invalid_dates = df["date_time"].isna()
    log_change(int(invalid_dates.sum()), "Dropped invalid dates")
    df = df.loc[~invalid_dates].copy()

    # Convert numerical columns; invalid entries become missing.
    numeric_columns = [
        "temp", "rain_1h", "snow_1h",
        "clouds_all", "traffic_volume"
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
        df[column] = df[column].replace(
            [np.inf, -np.inf], np.nan
        )
        log_change(
            int(df[column].isna().sum()),
            f"Missing or invalid numerical values in {column}"
        )

    # Remove exact duplicates, not all repeated timestamps.
    duplicates = df.duplicated(subset=EXPECTED_COLUMNS)
    log_change(int(duplicates.sum()), "Removed exact duplicate rows")
    df = df.loc[~duplicates].copy()

    # Do not invent missing traffic targets.
    invalid_target = (
        df["traffic_volume"].isna()
        | (df["traffic_volume"] < 0)
        | (df["traffic_volume"] % 1 != 0)
    )
    log_change(
        int(invalid_target.sum()),
        "Dropped missing, negative or non-integer traffic targets"
    )
    df = df.loc[~invalid_target].copy()

    if df.empty:
        raise ValueError("No usable records remain")

    # Broad validation rules, including the assignment's rain threshold.
    invalid_rules = {
        "temp": df["temp"] <= 0,
        "rain_1h": (df["rain_1h"] < 0) | (df["rain_1h"] > 9000),
        "snow_1h": df["snow_1h"] < 0,
        "clouds_all": ~df["clouds_all"].between(0, 100)
    }

    for column, invalid in invalid_rules.items():
        affected = invalid | df[column].isna()
        log_change(
            int(affected.sum()),
            f"Flagged missing or impossible values in {column}"
        )
        df.loc[affected, column] = np.nan

        valid_values = df[column].dropna()
        if valid_values.empty:
            raise ValueError(f"No valid values available for {column}")

        fallback_median = valid_values.median()

        # Use the median for each calendar month across available years.
        for month in sorted(df["date_time"].dt.month.unique()):
            month_mask = df["date_time"].dt.month == month
            to_fill = month_mask & df[column].isna()
            count = int(to_fill.sum())

            if count:
                monthly_median = df.loc[month_mask, column].median()

                if pd.isna(monthly_median):
                    monthly_median = fallback_median
                    method = "global median fallback"
                else:
                    method = "calendar-month median"

                df.loc[to_fill, column] = monthly_median
                logger.warning(
                    "Imputed rows=%d | column=%s | month=%d | "
                    "method=%s | value=%.4f",
                    count, column, month, method, monthly_median
                )

    df["traffic_volume"] = df["traffic_volume"].astype("int64")
    df = df.sort_values("date_time").reset_index(drop=True)

    logger.info(
        "Repeated timestamp rows retained=%d; "
        "different weather records can share a timestamp",
        int(df["date_time"].duplicated().sum())
    )
    logger.info(
        "Cleaning completed: rows=%d | columns=%d",
        *df.shape
    )
    return df


def main():
    configure_logging()

    try:
        csv_path = (
            BASE_DIR / "data" / "Metro_Interstate_Traffic_Volume.csv"
        )
        df = load_and_validate(csv_path)
        cleaned = clean_data(df)

        output_folder = BASE_DIR / "data" / "processed"
        output_folder.mkdir(parents=True, exist_ok=True)
        output_path = output_folder / "traffic_cleaned.csv"

        cleaned.to_csv(output_path, index=False)
        logger.info("Saved cleaned dataset: %s", output_path)
        return 0

    except (OSError, ValueError, pd.errors.ParserError) as exc:
        logger.error("Pipeline failed: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
