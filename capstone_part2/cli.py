from pathlib import Path
import argparse
import logging
import sys
from datetime import datetime

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
logger = logging.getLogger(__name__)


class LoggedArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        logger.error("Invalid command: %s", message)
        self.print_usage(sys.stderr)
        self.exit(2, f"Error: {message}\n")


def load_hourly_data():
    path = BASE_DIR / "data" / "processed" / "traffic_features.csv"
    df = pd.read_csv(path, keep_default_na=False)

    required = {"date_time", "traffic_volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if df.empty:
        raise ValueError("The dataset is empty.")

    df["date_time"] = pd.to_datetime(df["date_time"], errors="raise")
    df["traffic_volume"] = pd.to_numeric(
        df["traffic_volume"], errors="raise"
    )
    if df[list(required)].isna().any().any():
        raise ValueError("Missing dates or traffic volumes.")

    # Average records sharing a timestamp so each observed hour counts once.
    hourly = (
        df.groupby("date_time", as_index=False)["traffic_volume"]
        .mean()
        .sort_values("date_time")
    )
    logger.info("Loaded %d unique timestamps", len(hourly))
    return hourly


def main(argv=None):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                BASE_DIR / "pipeline.log", mode="a", encoding="utf-8"
            ),
        ],
        force=True,
    )

    arguments = sys.argv[1:] if argv is None else argv
    logger.info("CLI invoked | arguments=%s", arguments)

    parser = LoggedArgumentParser(description="Traffic data queries")
    commands = parser.add_subparsers(dest="command", required=True)

    date_parser = commands.add_parser("date", help="Traffic on one date")
    date_parser.add_argument("day", help="Date in YYYY-MM-DD format")

    high_parser = commands.add_parser(
        "high", help="Highest traffic above a threshold"
    )
    high_parser.add_argument("--threshold", type=float, default=5500)
    high_parser.add_argument("--limit", type=int, default=10)

    commands.add_parser(
        "compare", help="Compare weekday and weekend traffic"
    )

    args = parser.parse_args(arguments)
    logger.info("Command=%s | parameters=%s", args.command, vars(args))

    try:
        if args.command == "date":
            try:
                selected_date = datetime.strptime(args.day, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Use a valid date in YYYY-MM-DD format.")
            if selected_date.strftime("%Y-%m-%d") != args.day:
                raise ValueError("Use YYYY-MM-DD, for example 2017-01-01.")

        if args.command == "high":
            if not (0 <= args.threshold < float("inf")):
                raise ValueError("Threshold must be finite and non-negative.")
            if args.limit < 1:
                raise ValueError("Limit must be at least 1.")

        hourly = load_hourly_data()

        if args.command == "date":
            result = hourly.loc[
                hourly["date_time"].dt.date == selected_date.date()
            ]
            if result.empty:
                print(f"No observations found for {args.day}.")
            else:
                print(result.round(2).to_string(index=False))
                print(f"\nObserved hours: {len(result)}")
                print(
                    "Average traffic: "
                    f"{result['traffic_volume'].mean():.2f}"
                )

        elif args.command == "high":
            matching = hourly.loc[
                hourly["traffic_volume"] > args.threshold
            ]
            result = matching.nlargest(args.limit, "traffic_volume")
            print(f"Matching timestamps: {len(matching)}")
            if result.empty:
                print("No observations exceed this threshold.")
            else:
                print(result.round(2).to_string(index=False))

        else:
            hourly["day_type"] = (
                hourly["date_time"].dt.dayofweek.ge(5)
                .map({False: "Weekday", True: "Weekend"})
            )
            result = (
                hourly.groupby("day_type")
                .agg(
                    observed_hours=("traffic_volume", "size"),
                    average_traffic=("traffic_volume", "mean"),
                )
                .reindex(["Weekday", "Weekend"])
            )
            print(result.round(2).to_string())

        logger.info("Command completed successfully: %s", args.command)
        return 0

    except (OSError, ValueError, KeyError, pd.errors.ParserError) as exc:
        logger.error("Command failed: %s", exc)
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
