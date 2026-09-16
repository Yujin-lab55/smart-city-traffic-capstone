-- Query 1: Basic probabilities

SELECT
    COUNT(*) AS total_records,

    SUM(CASE
        WHEN traffic_volume > 5500 THEN 1
        ELSE 0
    END) AS congestion_records,

    SUM(CASE
        WHEN weather_main = 'Clear' THEN 1
        ELSE 0
    END) AS clear_records,

    SUM(CASE
        WHEN traffic_volume > 5500
         AND weather_main = 'Clear' THEN 1
        ELSE 0
    END) AS congestion_and_clear_records,

    ROUND(
        1.0 * SUM(CASE
            WHEN traffic_volume > 5500 THEN 1
            ELSE 0
        END) / COUNT(*),
        6
    ) AS p_congestion,

    ROUND(
        1.0 * SUM(CASE
            WHEN weather_main = 'Clear' THEN 1
            ELSE 0
        END) / COUNT(*),
        6
    ) AS p_clear,

    ROUND(
        1.0 * SUM(CASE
            WHEN traffic_volume > 5500
             AND weather_main = 'Clear' THEN 1
            ELSE 0
        END) / COUNT(*),
        6
    ) AS p_congestion_and_clear

FROM Traffic;

-- Results:
-- Total records: 48204
-- Congestion records: 7100
-- Clear records: 13391
-- Congestion and clear records: 1763
-- P(Congestion): 0.147291, approximately 14.73%
-- P(Clear): 0.277799, approximately 27.78%
-- P(Congestion AND Clear): 0.036574, approximately 3.66%


-- Query 2: Conditional probabilities given congestion

SELECT
    COUNT(*) AS congestion_records,

    SUM(CASE
        WHEN weather_main = 'Clear' THEN 1
        ELSE 0
    END) AS clear_and_congestion_records,

    SUM(CASE
        WHEN temp > 292 THEN 1
        ELSE 0
    END) AS hot_and_congestion_records,

    ROUND(
        1.0 * SUM(CASE
            WHEN weather_main = 'Clear' THEN 1
            ELSE 0
        END) / NULLIF(COUNT(*), 0),
        6
    ) AS p_clear_given_congestion,

    ROUND(
        1.0 * SUM(CASE
            WHEN temp > 292 THEN 1
            ELSE 0
        END) / NULLIF(COUNT(*), 0),
        6
    ) AS p_hot_given_congestion

FROM Traffic
WHERE traffic_volume > 5500;

-- Results:
-- Congestion records: 7100
-- Clear and congestion records: 1763
-- High temperature and congestion records: 1867
-- P(Clear | Congestion): 0.248310, approximately 24.83%
-- P(High Temperature | Congestion): 0.262958,
-- approximately 26.30%.
-- These conditions can overlap; their percentages
-- should not be added as mutually exclusive categories.


-- Query 3: Independence of clear weather and congestion

WITH counts AS (
    SELECT
        COUNT(*) AS total_records,

        SUM(CASE
            WHEN traffic_volume > 5500 THEN 1
            ELSE 0
        END) AS congestion_records,

        SUM(CASE
            WHEN weather_main = 'Clear' THEN 1
            ELSE 0
        END) AS clear_records,

        SUM(CASE
            WHEN traffic_volume > 5500
             AND weather_main = 'Clear' THEN 1
            ELSE 0
        END) AS joint_records

    FROM Traffic
),
probabilities AS (
    SELECT
        1.0 * congestion_records / total_records
            AS p_congestion,
        1.0 * clear_records / total_records
            AS p_clear,
        1.0 * joint_records / total_records
            AS p_joint
    FROM counts
)
SELECT
    ROUND(p_joint, 6) AS actual_joint_probability,
    ROUND(p_congestion * p_clear, 6)
        AS expected_if_independent,
    ROUND(p_joint - p_congestion * p_clear, 6)
        AS difference
FROM probabilities;

-- Results:
-- Actual joint probability: 0.036574
-- Expected under independence: 0.040917
-- Difference: -0.004343, approximately -0.4343
-- percentage points.
--
-- Interpretation:
-- P(Congestion AND Clear) differs from
-- P(Congestion) * P(Clear).
-- The independence equality does not hold for the
-- observed record-level proportions.
-- This comparison is not a statistical significance test.


-- Query 4: Congestion odds ratio, Clear versus Clouds
-- Weather categories other than Clear and Clouds
-- are excluded from this comparison.

WITH weather_counts AS (
    SELECT
        SUM(CASE
            WHEN weather_main = 'Clear'
             AND traffic_volume > 5500
            THEN 1 ELSE 0
        END) AS clear_congested,

        SUM(CASE
            WHEN weather_main = 'Clear'
             AND traffic_volume <= 5500
            THEN 1 ELSE 0
        END) AS clear_not_congested,

        SUM(CASE
            WHEN weather_main = 'Clouds'
             AND traffic_volume > 5500
            THEN 1 ELSE 0
        END) AS cloudy_congested,

        SUM(CASE
            WHEN weather_main = 'Clouds'
             AND traffic_volume <= 5500
            THEN 1 ELSE 0
        END) AS cloudy_not_congested

    FROM Traffic
)
SELECT
    clear_congested,
    clear_not_congested,
    cloudy_congested,
    cloudy_not_congested,

    ROUND(
        1.0 * clear_congested
        / NULLIF(clear_not_congested, 0),
        6
    ) AS clear_congestion_odds,

    ROUND(
        1.0 * cloudy_congested
        / NULLIF(cloudy_not_congested, 0),
        6
    ) AS cloudy_congestion_odds,

    ROUND(
        (1.0 * clear_congested * cloudy_not_congested)
        / NULLIF(
            1.0 * clear_not_congested * cloudy_congested,
            0
        ),
        6
    ) AS odds_ratio_clear_vs_cloudy

FROM weather_counts;

-- Results:
-- Clear, congested: 1763
-- Clear, not congested: 11628
-- Clouds, congested: 2592
-- Clouds, not congested: 12572
-- Clear congestion odds: 0.151617
-- Cloudy congestion odds: 0.206172
-- Odds ratio: approximately 0.7354.
--
-- Interpretation:
-- Congestion odds in clear weather are approximately
-- 26.5% lower than in cloudy weather.
-- This is a comparison of odds, not a percentage-point
-- difference in congestion probabilities.


-- Overall conclusion and limitations:
-- Weather and congestion show an association in these
-- historical records. Clear weather has lower congestion
-- odds than cloudy weather, but this does not establish
-- that weather causes changes in congestion.
--
-- Hour, weekday, season and holidays may help explain
-- the observed relationship.
-- Repeated timestamps and unequal data coverage affect
-- the record-level proportions.
-- The traffic-volume threshold is the assignment's
-- operational definition of congestion; it does not
-- directly measure vehicle speed or travel delay.
