{{
  config(
    materialized='incremental',
    unique_key=['PacketVersionId', 'FieldName', 'RepeatInstrument', 'RepeatInstance'],
    incremental_strategy='merge',
    merge_update_columns=['Id', 'LastUpdated', 'IsDeleted', 'FieldValue']
  )
}}

WITH source_data AS (
    -- Current records from staging
    SELECT
      Id,
      PacketVersionId,
      ChampsId,
      RepeatInstrument,
      RepeatInstance,
      FieldName,
      FieldValue,
      CreatedOn,
      GETDATE() as LastUpdated,
      0 as IsDeleted
    FROM {{ source('hiv_data_staging', 'HIVProject6_1_stg') }}
),
deleted_records AS (
    {% if is_incremental() %}
    -- This finds records in target table that NO LONGER exist in source
    SELECT
      t.Id,
      t.PacketVersionId,
      t.ChampsId,
      t.RepeatInstrument,
      t.RepeatInstance,
      t.FieldName,
      t.FieldValue,
      t.CreatedOn,
      GETDATE() as LastUpdated,
      1 as IsDeleted
    FROM {{ this }} t
    LEFT JOIN source_data s ON 
      t.PacketVersionId = s.PacketVersionId
      AND COALESCE(t.RepeatInstrument, '') = COALESCE(s.RepeatInstrument, '')
      AND COALESCE(t.RepeatInstance, '') = COALESCE(s.RepeatInstance, '')
      AND t.FieldName = s.FieldName
    WHERE s.PacketVersionId IS NULL
    {% else %}
    -- For full refresh, no deleted records to consider
    SELECT 
      CAST(NULL AS VARCHAR(100)) as Id,
      CAST(NULL AS VARCHAR(100)) as PacketVersionId,
      CAST(NULL AS VARCHAR(9)) as ChampsId,
      CAST(NULL AS VARCHAR(100)) as RepeatInstrument,
      CAST(NULL AS VARCHAR(3)) as RepeatInstance,
      CAST(NULL AS VARCHAR(100)) as FieldName,
      CAST(NULL AS VARCHAR(MAX)) as FieldValue,
      CAST(NULL AS DATETIME) as CreatedOn,
      CAST(NULL AS DATETIME) as LastUpdated,
      CAST(NULL AS INT) as IsDeleted
    WHERE 1=0
    {% endif %}
),
final AS (
    -- New or updated records from source
    SELECT * FROM source_data
    
    UNION ALL
    
    -- Soft-deleted records (mark as deleted in target but not in source)
    SELECT * FROM deleted_records
)

SELECT 
    COALESCE(
        (SELECT top 1 Id FROM final WHERE Id IS NOT NULL AND PacketVersionId = f.PacketVersionId 
         AND COALESCE(RepeatInstrument, '') = COALESCE(f.RepeatInstrument, '')
         AND COALESCE(RepeatInstance, '') = COALESCE(f.RepeatInstance, '')
         AND FieldName = f.FieldName
         ),
        NEWID()
    ) as Id,
    PacketVersionId,
    ChampsId,
    RepeatInstrument,
    RepeatInstance,
    FieldName,
    FieldValue,
    COALESCE(CreatedOn, GETDATE()) as CreatedOn,
    LastUpdated,
    IsDeleted
FROM final f
