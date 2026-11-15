
{{ config(materialized='view') }}

WITH source_data AS (
    SELECT
        TRIM(SHIPMENT_ID) AS shipment_id,
        TRIM(CARRIER_ID) AS carrier_id,
        TRIM(ORIGIN_CITY) AS origin_city,
        TRIM(DESTINATION_CITY) AS destination_city,
        ORDER_DATETIME AS order_datetime,
        PROMISED_DELIVERY_DATE AS promised_delivery_date,
        UPPER(TRIM(CURRENT_STATUS)) AS current_status,
        _FIVETRAN_SYNCED AS synced_at
    FROM {{ source('raw', 'shipments') }}
),

deduplicated AS (
    SELECT *
    FROM source_data
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY shipment_id
        ORDER BY synced_at DESC NULLS LAST
    ) = 1
)

SELECT *
FROM deduplicated
WHERE shipment_id IS NOT NULL
