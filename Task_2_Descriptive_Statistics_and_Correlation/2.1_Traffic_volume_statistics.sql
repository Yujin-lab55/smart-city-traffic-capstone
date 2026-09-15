
WITH traffic_data AS (
    SELECT CAST(traffic_volume AS REAL) AS volume
    FROM Traffic
    WHERE traffic_volume IS NOT NULL
),
ranked_data AS (
    SELECT
        volume,
        ROW_NUMBER() OVER (ORDER BY volume) AS row_num,
        COUNT(*) OVER () AS total_count
    FROM traffic_data
),
summary AS (
    SELECT
        COUNT(*) AS record_count,
        AVG(volume) AS mean_volume,
        MIN(volume) AS minimum_volume,
        MAX(volume) AS maximum_volume
    FROM traffic_data
),
median_value AS (
    SELECT AVG(volume) AS median_volume
    FROM ranked_data
    WHERE row_num IN (
        (total_count + 1) / 2,
        (total_count + 2) / 2
    )
),
variance_value AS (
    SELECT
        SUM(
            (t.volume - s.mean_volume)
            * (t.volume - s.mean_volume)
        ) / NULLIF(s.record_count - 1, 0) AS sample_variance
    FROM traffic_data AS t
    CROSS JOIN summary AS s
)
SELECT
    s.record_count,
    ROUND(s.mean_volume, 2) AS mean,
    m.median_volume AS median,
    ROUND(v.sample_variance, 2) AS sample_variance
