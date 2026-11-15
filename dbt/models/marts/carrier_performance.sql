
{{ config(materialized='table') }}

SELECT
    carrier_id,
    carrier_name,

    COUNT(*) AS total_shipments,

    COUNT_IF(delivered_at IS NOT NULL) AS delivered_shipments,

    COUNT_IF(delivered_at IS NULL) AS undelivered_shipments,

    ROUND(AVG(delivery_days), 2) AS avg_delivery_days,

    COUNT_IF(is_late = TRUE) AS late_deliveries,

    COUNT_IF(is_late = FALSE) AS on_time_deliveries,

    ROUND(
        100.0 * COUNT_IF(is_late = FALSE)
        / NULLIF(COUNT_IF(delivered_at IS NOT NULL), 0),
        2
    ) AS on_time_percentage

FROM {{ ref('fct_deliveries') }}
GROUP BY carrier_id, carrier_name
