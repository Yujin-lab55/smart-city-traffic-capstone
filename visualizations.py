from pathlib import Path
import logging

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent


def save_figure(fig, folder, filename):
    path = folder / filename
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved figure: %s", path)


def create_visualizations(df, output_folder):
    required = {"date_time", "traffic_volume", "temperature_c"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if df.empty:
        raise ValueError("The dataset is empty")

    df = df.copy()
    df["date_time"] = pd.to_datetime(df["date_time"], errors="raise")

    if df[list(required)].isna().any().any():
        raise ValueError("Missing values in required chart columns")

    output_folder.mkdir(parents=True, exist_ok=True)

    # Give each observed timestamp equal weight.
    hourly = (
        df.groupby("date_time", as_index=False)
        .agg(
            traffic_volume=("traffic_volume", "mean"),
            temperature_c=("temperature_c", "mean")
        )
    )
    hourly["hour"] = hourly["date_time"].dt.hour
    hourly["is_weekend"] = (
        hourly["date_time"].dt.dayofweek >= 5
    ).astype(int)

    logger.info(
        "Prepared charts from %d records and %d distinct timestamps",
        len(df), len(hourly)
    )

    # Chart 1: Average traffic by hour.
    by_hour = (
        hourly.groupby("hour")["traffic_volume"]
        .mean()
        .reindex(range(24))
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(by_hour.index, by_hour.values, color="#2878B5")
    ax.set(
        title="Average Traffic by Hour",
        xlabel="Hour of day",
        ylabel="Average traffic volume (vehicles)"
    )
    ax.set_xticks(range(24))
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    save_figure(fig, output_folder, "01_traffic_by_hour.png")

    # Chart 2: Weekday and weekend hourly patterns.
    comparison = (
        hourly.groupby(["hour", "is_weekend"])["traffic_volume"]
        .mean()
        .unstack("is_weekend")
        .reindex(index=range(24), columns=[0, 1])
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    for value, label, color in [
        (0, "Weekday", "#2878B5"),
        (1, "Weekend", "#D97706")
    ]:
        ax.plot(
            comparison.index,
            comparison[value],
            marker="o",
            label=label,
            color=color
        )

    ax.set(
        title="Hourly Traffic on Weekdays and Weekends",
        xlabel="Hour of day",
        ylabel="Average traffic volume (vehicles)"
    )
    ax.set_xticks(range(24))
    ax.set_ylim(bottom=0)
    ax.legend()
    ax.grid(alpha=0.25)
    save_figure(fig, output_folder, "02_weekday_weekend.png")

    # Chart 3: Temperature and traffic.
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(
        hourly["temperature_c"],
        hourly["traffic_volume"],
        s=7,
        alpha=0.12,
        color="#2878B5",
        edgecolors="none"
    )
    ax.set(
        title="Temperature and Traffic Volume",
        xlabel="Temperature (°C)",
        ylabel="Traffic volume (vehicles)"
    )
    ax.grid(alpha=0.2)
    save_figure(fig, output_folder, "03_temperature_traffic.png")

    # Save short interpretations using the calculated results.
    peak_hour = int(by_hour.idxmax())
    quiet_hour = int(by_hour.idxmin())
    day_means = hourly.groupby("is_weekend")["traffic_volume"].mean()
    correlation = hourly["temperature_c"].corr(hourly["traffic_volume"])

    notes = (
        "# Traffic visualisation findings\n\n"
        "Scope: all available years in the cleaned dataset. "
        "Records are averaged by timestamp before plotting, so each "
        "observed timestamp has equal weight. Missing hours are not "
        "filled with zero.\n\n"
        "## 1. Average traffic by hour\n"
        f"The highest hourly mean occurs at {peak_hour:02d}:00 "
        f"({by_hour.loc[peak_hour]:,.2f} vehicles), and the lowest at "
        f"{quiet_hour:02d}:00 ({by_hour.loc[quiet_hour]:,.2f} vehicles). "
        "These differences support time-specific mobility planning.\n\n"
        "## 2. Weekday and weekend patterns\n"
        f"Average traffic is {day_means.get(0, float('nan')):,.2f} "
        "vehicles on weekdays and "
        f"{day_means.get(1, float('nan')):,.2f} on weekends. "
        "The hourly curves allow comparison at similar times of day. "
        "Unequal coverage and holidays may influence these averages.\n\n"
        "## 3. Temperature and traffic\n"
        f"The Pearson correlation for the cleaned, timestamp-averaged "
        f"data is {correlation:.3f}. "
        "The scatter shows whether similar temperatures coincide with "
        "different traffic volumes. This association does not establish "
        "causation because time of day and season may influence both "
        "variables. This calculation uses a different preparation method "
        "from the raw-record correlation in Part 1.\n"
    )

    notes_path = output_folder / "visualization_notes.md"
    notes_path.write_text(notes, encoding="utf-8")
    logger.info("Saved chart interpretations: %s", notes_path)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                BASE_DIR / "pipeline.log",
                mode="a",
                encoding="utf-8"
            )
        ],
        force=True
    )

    try:
        input_path = (
            BASE_DIR / "data" / "processed" / "traffic_features.csv"
        )
        df = pd.read_csv(input_path, keep_default_na=False)
        logger.info("Loaded feature dataset: rows=%d | columns=%d", *df.shape)

        create_visualizations(df, BASE_DIR / "figures")
        logger.info("All three charts completed")
        return 0

    except (OSError, ValueError, KeyError, TypeError) as exc:
        logger.error("Visualisation failed: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
