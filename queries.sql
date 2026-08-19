SELECT * FROM shipments LIMIT 10;


WITH carrier_stats AS (
    SELECT
        delivery_partner,
        AVG(delivery_time_hours) OVER (PARTITION BY delivery_partner) AS avg_time,
        STDDEV(delivery_time_hours) OVER (PARTITION BY delivery_partner) AS std_time,
        delivery_time_hours,
        delivery_id
    FROM shipments
),
flagged AS (
    SELECT
        delivery_id,
        delivery_partner,
        delivery_time_hours,
        avg_time,
        std_time,
        (delivery_time_hours - avg_time) / NULLIF(std_time, 0) AS z_score
    FROM carrier_stats
)
SELECT *
FROM flagged
WHERE ABS(z_score) > 2
ORDER BY ABS(z_score) DESC;


WITH carrier_stats AS (
    SELECT
        delivery_partner,
        weather_condition,
        AVG(delivery_time_hours) OVER (PARTITION BY delivery_partner) AS avg_time,
        STDDEV(delivery_time_hours) OVER (PARTITION BY delivery_partner) AS std_time,
        delivery_time_hours
    FROM shipments
),
flagged AS (
    SELECT
        weather_condition,
        CASE WHEN ABS((delivery_time_hours - avg_time) / NULLIF(std_time, 0)) > 2
             THEN 1 ELSE 0 END AS is_anomaly
    FROM carrier_stats
)
SELECT
    weather_condition,
    COUNT(*) AS total,
    SUM(is_anomaly) AS anomalies,
    ROUND(SUM(is_anomaly) * 100.0 / COUNT(*), 2) AS anomaly_rate_pct
FROM flagged
GROUP BY weather_condition
ORDER BY anomaly_rate_pct DESC;