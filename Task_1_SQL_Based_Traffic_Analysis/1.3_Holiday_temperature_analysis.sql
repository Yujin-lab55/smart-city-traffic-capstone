-- Query 1: Check holiday records for 2015–2017
SELECT
    strftime('%Y', date_time) AS year,
    holiday,
    COUNT(*) AS record_count,
    MIN(date_time) AS first_record,
    MAX(date_time) AS last_record
FROM Traffic
WHERE strftime('%Y', date_time) BETWEEN '2015' AND '2017'
  AND holiday IS NOT NULL
  AND TRIM(holiday) <> ''
  AND LOWER(TRIM(holiday)) <> 'none'
GROUP BY
    strftime('%Y', date_time),
    holiday
ORDER BY year, holiday;

-- Query 2: Daily averages for selected holiday dates
-- Use the dates labelled as holidays in the dataset.
-- Average repeated timestamps first, then average across observed hours.
-- Missing hours are not imputed.

WITH holiday_dates AS (
    SELECT DISTINCT
        DATE(date_time) AS holiday_date,
        holiday
    FROM Traffic
    WHERE strftime('%Y', date_time) BETWEEN '2015' AND '2017'
      AND holiday IN ('New Years Day', 'Labor Day')
),
hourly_data AS (
    SELECT
        date_time,
        AVG(temp) AS temperature_k,
        AVG(traffic_volume) AS hourly_traffic
    FROM Traffic
    WHERE strftime('%Y', date_time) BETWEEN '2015' AND '2017'
    GROUP BY date_time
)
SELECT
    strftime('%Y', h.holiday_date) AS year,
    h.holiday,
    h.holiday_date,
    COUNT(*) AS observed_hours,
    ROUND(AVG(t.temperature_k), 2) AS avg_temp_k,
    ROUND(AVG(t.temperature_k) - 273.15, 2)
        AS avg_temp_c,
    ROUND(AVG(t.hourly_traffic), 2)
        AS avg_traffic_volume
FROM holiday_dates AS h
JOIN hourly_data AS t
    ON DATE(t.date_time) = h.holiday_date
GROUP BY h.holiday_date, h.holiday
ORDER BY h.holiday, h.holiday_date;
