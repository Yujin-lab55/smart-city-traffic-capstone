# Part 2 — Traffic Analytics Pipeline

Python workflow for cleaning, feature engineering,
visualisation and command-line analysis of traffic data.

## Files

- pipeline.py: load, validate and clean data.
- feature_engineering.py: create time and weather features.
- visualizations.py: save three charts and interpretations.
- cli.py: query processed traffic data.
- pipeline.log: execution log.
- figures/: charts and visualization_notes.md.
- data/processed/: generated datasets and feature metadata.
- Part2_Python_Pipeline_Report.docx: methodology and findings.

Keep all four Python scripts in the same folder.

## Setup

Requires Python 3, pandas, numpy and matplotlib.

Install packages if needed:

```bash
python -m pip install pandas numpy matplotlib
```

Place the supplied original CSV at:

```text
data/Metro_Interstate_Traffic_Volume.csv
```

## Run the pipeline

Open a terminal in the folder containing the scripts.
Run these commands in order:

```bash
python pipeline.py
python feature_engineering.py
python visualizations.py
```

In Jupyter Notebook, use:

```python
%run pipeline.py
%run feature_engineering.py
%run visualizations.py
```

Generated datasets and metadata:

- data/processed/traffic_cleaned.csv
- data/processed/traffic_features.csv
- data/processed/feature_metadata.json

Generated charts:

- figures/01_traffic_by_hour.png
- figures/02_weekday_weekend.png
- figures/03_temperature_traffic.png

Chart interpretations are saved in
figures/visualization_notes.md.

## CLI commands

Query one date:

```bash
python cli.py date 2017-01-01
```

Show the ten highest traffic volumes above 5,500:

```bash
python cli.py high --threshold 5500 --limit 10
```

Compare weekdays and weekends:

```bash
python cli.py compare
```

Test invalid input:

```bash
python cli.py date 2017-13-01
```

The invalid date intentionally produces an ERROR message
and exit code 1. Jupyter may also display SystemExit: 1.

In Jupyter, replace python with %run for these commands.

## Cleaning

The original dataset contains 48,204 rows and nine columns.
The pipeline validates required columns, standardises text,
parses dates and removes exact duplicates.

Removing 17 exact duplicates leaves 48,187 records.
Ten invalid temperature readings and one rainfall outlier
are replaced with calendar-month medians.
A global median is used only if a month has no valid values.

Different weather records can share a timestamp.
These are retained in the cleaned dataset.
Charts and CLI queries first average records within each
timestamp, producing 40,575 observed hourly timestamps.
Missing hours are not filled.

## Features and traffic categories

Features include hour, weekday, weekend indicator,
cyclical time encodings, Celsius temperature, holiday,
rain and snow indicators, and one-hot weather encoding.

Temperature and rainfall receive min-max scaled versions.

Traffic categories use cleaned traffic-volume quartiles:

- Low: volume <= Q1.
- Moderate: Q1 < volume <= Q2.
- High: Q2 < volume <= Q3.
- Severe: volume > Q3.

Thresholds and scaling parameters are saved in
data/processed/feature_metadata.json.

These categories differ from Part 1's fixed thresholds.
The CLI high command uses its own user-supplied threshold.

## Logging

Every module uses logging.getLogger(__name__).
Handlers are configured when scripts run as entry points.
Logs are written to the console and appended to
pipeline.log beside the scripts.

The format includes timestamp, level, module and message.

- INFO: loading, dataset shapes, saved files and CLI activity.
- WARNING: cleaning changes, affected counts and reasons.
- ERROR: failures and invalid CLI input.
- DEBUG: intermediate feature calculations.

Enable DEBUG output for feature engineering with:

```bash
python feature_engineering.py --debug
```

Normal runs do not display DEBUG calculations.
Internal progress uses logging; CLI print output provides
user-facing results and error explanations.

## Verified results

- Date 2017-01-01: 24 observed hours, mean traffic 2,127.62.
- Above 5,500: 6,107 matching timestamps.
- Weekday: 28,979 timestamps, mean traffic 3,557.44.
- Weekend: 11,596 timestamps, mean traffic 2,623.93.
- Invalid date: clear ERROR message and exit code 1.

## Limitations and Part 3

The dataset covers one road location and has missing hours.
Charts use all available years and timestamp-level averages,
so results can differ from Part 1's selected-year analyses.

Traffic-volume categories are proxies for congestion.
Descriptive associations do not establish causation.

Part 2 transformations use the full dataset for exploration.
For Part 3, split chronologically before fitting imputation,
scaling, encoding and target thresholds on training data.
Keep identical timestamps in the same split and exclude
traffic-derived targets from model predictors.
