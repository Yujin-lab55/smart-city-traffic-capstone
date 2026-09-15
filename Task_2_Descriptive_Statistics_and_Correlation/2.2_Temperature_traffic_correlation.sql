-- Task 2.2: Pearson correlation between temperature and traffic volume
-- Scope: all 48,204 original records.
-- Repeated timestamps and raw temperature values are retained.

WITH paired_data AS (
    SELECT
        CAST(temp AS REAL) AS temperature,
        CAST(traffic_volume AS REAL) AS volume
    FROM Traffic
    WHERE temp IS NOT NULL
      AND traffic_volume IS NOT NULL
),
means AS (
    SELECT
        AVG(temperature) AS mean_temperature,
        AVG(volume) AS mean_volume
    FROM paired_data
)
SELECT
    COUNT(*) AS record_count,
    SUM(
        (p.temperature - m.mean_temperature)
        * (p.volume - m.mean_volume)
    ) AS sum_cross_product,
    SUM(
        (p.temperature - m.mean_temperature)
        * (p.temperature - m.mean_temperature)
    ) AS sum_squared_temp,
    SUM(
        (p.volume - m.mean_volume)
        * (p.volume - m.mean_volume)
    ) AS sum_squared_traffic
FROM paired_data AS p
CROSS JOIN means AS m;

-- Pearson correlation:
-- r = sum_cross_product
--     / sqrt(sum_squared_temp * sum_squared_traffic)

-- SQRT() is unavailable in the SQLite build used.
-- The final calculation was performed in Excel:
-- =166448603.372357/SQRT(8575720.07810712*190286901451.519)

-- Result: r is approximately 0.130.

-- Interpretation:
-- Temperature and traffic volume have a weak positive
-- linear relationship. Higher temperatures are associated
-- with slightly higher traffic volumes, but temperature
-- alone provides limited information about traffic volume.

-- Correlation does not imply causation.
-- Time of day, day of week, season and holidays may affect
-- both variables or help explain the observed relationship.

-- Limitations:
-- Repeated timestamps and temperature anomalies are retained.
-- This is a raw-record baseline; cleaning may change the result.
