
{{ config(materialized='table') }}

WITH delivery_events AS (
    SELECT
        shipment_id,
        MIN(event_datetime) AS delivered_at
    FROM {{ ref('stg_tracking_events') }}
    WHERE event_status = 'DELIVERED'
    GROUP BY shipment_id
),

shipments AS (
    SELECT *
    FROM {{ ref('stg_shipments') }}
),

carriers AS (
    SELECT *
    FROM {{ ref('stg_carriers') }}
)

SELECT
    s.shipment_id,
    s.carrier_id,
    COALESCE(c.carrier_name, 'Unknown') AS carrier_name,
    s.origin_city,
    s.destination_city,
    s.order_datetime,
    s.promised_delivery_date,
    s.current_status,
    d.delivered_at,

    CASE
        WHEN d.delivered_at IS NOT NULL
        THEN DATEDIFF('day', s.order_datetime, d.delivered_at)
        ELSE NULL
    END AS delivery_days,

    CASE
        WHEN d.delivered_at IS NOT NULL
             AND CAST(d.delivered_at AS DATE) > s.promised_delivery_date
        THEN TRUE
        WHEN d.delivered_at IS NOT NULL
        THEN FALSE
        ELSE NULL
    END AS is_late

FROM shipments s
LEFT JOIN delivery_events d
    ON s.shipment_id = d.shipment_id
LEFT JOIN carriers c
    ON s.carrier_id = c.carrier_id
