{{
  config(
    materialized='incremental',
    schema='hiv',
    unique_key=['ChampsId', 'RepeatInstrument', 'RepeatInstance', 'FieldName', 'FieldValue'],
    incremental_strategy='merge',
    merge_update_columns=['Id', 'LastUpdated', 'IsDeleted']
  )
}}

WITH source_data AS (
    -- Current records from staging
    SELECT
      Id,
      ChampsId,
      RepeatInstrument,
      RepeatInstance,
      FieldName,
      FieldValue,
      CreatedOn,
      GETDATE() as LastUpdated,
      0 as IsDeleted
    FROM {{ source('hiv_data_staging', 'HIVProject3_1_stg') }}
),
deleted_records AS (
    {% if is_incremental() %}
    -- This finds records in target table that NO LONGER exist in source
    SELECT
      t.Id,
      t.ChampsId,
      t.RepeatInstrument,
      t.RepeatInstance,
      t.FieldName,
      t.FieldValue,
      t.CreatedOn,
      GETDATE() as LastUpdated,
      1 as IsDeleted  -- Mark as deleted
    FROM {{ this }} t
    WHERE 
      t.IsDeleted = 0  -- Only consider active records
      AND NOT EXISTS (
        SELECT 1 
        FROM {{ source('hiv_data_staging', 'HIVProject3_1_stg') }} s
        WHERE 
          s.ChampsId = t.ChampsId
          AND COALESCE(s.RepeatInstrument, '') = COALESCE(t.RepeatInstrument, '')
          AND COALESCE(s.RepeatInstance, '') = COALESCE(t.RepeatInstance, '')
          AND s.FieldName = t.FieldName
          AND s.FieldValue = t.FieldValue
      )
    {% else %}
    -- Empty set for initial load
    SELECT
      Id,
      ChampsId,
      RepeatInstrument,
      RepeatInstance,
      FieldName,
      FieldValue,
      CreatedOn,
      GETDATE() as LastUpdated,
      1 as IsDeleted
    FROM source_data
    WHERE 1=0
    {% endif %}
)

-- Combine active records with those that need to be marked as deleted
SELECT * FROM source_data
UNION ALL 
SELECT * FROM deleted_records