-- Query 1: Annual recorded traffic totals
SELECT
    strftime('%Y', date_time) AS year,
    COUNT(*) AS record_count,
    SUM(traffic_volume) AS total_traffic_volume
FROM Traffic
WHERE strftime('%Y', date_time) BETWEEN '2012' AND '2017'
GROUP BY strftime('%Y', date_time)
ORDER BY year;

-- Query 2: Year-on-year changes in recorded traffic totals
WITH annual_traffic AS (
    SELECT
        strftime('%Y', date_time) AS year,
        COUNT(*) AS record_count,
        SUM(traffic_volume) AS total_traffic_volume
    FROM Traffic
    WHERE strftime('%Y', date_time) BETWEEN '2012' AND '2017'
    GROUP BY strftime('%Y', date_time)
),
yearly_comparison AS (
    SELECT
        *,
        LAG(total_traffic_volume) OVER (ORDER BY year)
            AS previous_year_volume
    FROM annual_traffic
)
SELECT
    year,
    record_count,
    total_traffic_volume,
    total_traffic_volume - previous_year_volume
        AS change_in_volume,
    ROUND(
        100.0 * (total_traffic_volume - previous_year_volume)
        / NULLIF(previous_year_volume, 0),
        2
    ) AS change_percent
FROM yearly_comparison
ORDER BY year;

-- Query 3: Annual observation coverage and repeated timestamps
SELECT
    strftime('%Y', date_time) AS year,
    COUNT(*) AS total_records,
    COUNT(DISTINCT date_time) AS unique_hours,
    COUNT(*) - COUNT(DISTINCT date_time)
        AS extra_timestamp_records,
    MIN(date_time) AS first_record,
    MAX(date_time) AS last_record
FROM Traffic
WHERE strftime('%Y', date_time) BETWEEN '2012' AND '2017'
GROUP BY strftime('%Y', date_time)
ORDER BY year;
