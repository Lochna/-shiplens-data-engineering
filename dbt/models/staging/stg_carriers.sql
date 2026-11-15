
{{ config(materialized='view') }}

WITH source_data AS (
    SELECT
        TRIM(CARRIER_ID) AS carrier_id,
        TRIM(CARRIER_NAME) AS carrier_name,
        _FIVETRAN_SYNCED AS synced_at
    FROM {{ source('raw', 'carriers') }}
)

SELECT *
FROM source_data
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY carrier_id
    ORDER BY synced_at DESC NULLS LAST
) = 1
