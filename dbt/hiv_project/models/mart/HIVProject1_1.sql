{{
  config(
    materialized='incremental',
    schema='hiv', 
    unique_key=['SiteId', 'CatchmentId', 'ReportId', 'FieldName'],
    incremental_strategy='merge',
    merge_update_columns=['Id', 'ChampsId', 'FieldValue', 'LastUpdated', 'IsDeleted']
  )
}}

WITH source_data AS (
    -- Current records from staging
    SELECT
      Id,
      SiteId,
      CatchmentId,
      ReportId,
      ChampsId,
      FieldName,
      FieldValue,
      GETDATE() as LastUpdated,
      0 as IsDeleted
    FROM {{ source('hiv_data_staging', 'HIVProject1_1_stg') }}
),
deleted_records AS (
    {% if is_incremental() %}
    -- This finds records in target table that NO LONGER exist in source
    SELECT
      t.Id,
      t.SiteId,
      t.CatchmentId,
      t.ReportId,
      t.ChampsId,
      t.FieldName,
      t.FieldValue,
      GETDATE() as LastUpdated,
      1 as IsDeleted  -- Mark as deleted
    FROM {{ this }} t
    WHERE 
      t.IsDeleted = 0  -- Only consider active records
      AND NOT EXISTS (
        SELECT 1 
        FROM {{ source('hiv_data_staging', 'HIVProject1_1_stg') }} s
        WHERE 
          s.SiteId = t.SiteId 
          AND s.CatchmentId = t.CatchmentId 
          AND s.ReportId = t.ReportId
          AND s.FieldName = t.FieldName
      )
    {% else %}
    -- Empty set for initial load
    SELECT
      Id,
      SiteId,
      CatchmentId,
      ReportId,
      ChampsId, 
      FieldName,
      FieldValue,
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