{{
  config(
    materialized='incremental',
    schema='hiv',
    unique_key=['SiteId', 'ChampsId', 'FieldName'],
    incremental_strategy='merge',
    merge_update_columns=['Id', 'FieldValue', 'LastUpdated', 'IsDeleted']
  )
}}

WITH source_data AS (
    -- Current records from staging
    SELECT
      Id,
      SiteId,
      ChampsId,
      FieldName,
      FieldValue,
      CreatedOn,
      GETDATE() as LastUpdated,
      0 as IsDeleted
    FROM {{ source('hiv_data_staging', 'HIVClinicalAbstract_stg') }}
),
deleted_records AS (
    {% if is_incremental() %}
    -- This finds records in target table that NO LONGER exist in source
    SELECT
      t.Id,
      t.SiteId,
      t.ChampsId,
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
        FROM {{ source('hiv_data_staging', 'HIVClinicalAbstract_stg') }} s
        WHERE 
          COALESCE(s.SiteId, '') = COALESCE(t.SiteId, '')
          AND s.ChampsId = t.ChampsId
          AND s.FieldName = t.FieldName
      )
    {% else %}
    -- Empty set for initial load
    SELECT
      Id,
      SiteId,
      ChampsId,
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