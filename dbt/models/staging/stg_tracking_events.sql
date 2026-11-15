
{{ config(materialized='view') }}

WITH source_data AS (
    SELECT
        TRIM(EVENT_ID) AS event_id,
        TRIM(SHIPMENT_ID) AS shipment_id,
        UPPER(TRIM(EVENT_STATUS)) AS event_status,
        EVENT_DATETIME AS event_datetime,
        _FIVETRAN_SYNCED AS synced_at
    FROM {{ source('raw', 'tracking_events') }}
),

deduplicated AS (
    SELECT *
    FROM source_data
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY event_id
        ORDER BY synced_at DESC NULLS LAST
    ) = 1
)

SELECT *
FROM deduplicated
WHERE event_id IS NOT NULL
  AND shipment_id IS NOT NULL
