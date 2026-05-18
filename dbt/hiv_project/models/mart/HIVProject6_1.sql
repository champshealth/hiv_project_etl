{{
  config(
    materialized='table',
    post_hook=[
      "IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_HIVProject6_1_ChampsId' AND object_id = OBJECT_ID('{{ this }}')) CREATE INDEX idx_HIVProject6_1_ChampsId ON {{ this }} (ChampsId)",
      "IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_HIVProject6_1_FieldName' AND object_id = OBJECT_ID('{{ this }}')) CREATE INDEX idx_HIVProject6_1_FieldName ON {{ this }} (FieldName)",
      "IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_HIVProject6_1_PacketVersionId' AND object_id = OBJECT_ID('{{ this }}')) CREATE INDEX idx_HIVProject6_1_PacketVersionId ON {{ this }} (PacketVersionId)"
    ]
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
)
SELECT 
    CAST(NEWID() AS varchar(100)) as Id,
    CAST(PacketVersionId AS varchar(100)) as PacketVersionId,
    CAST(ChampsId AS varchar(9)) as ChampsId,
    CAST(RepeatInstrument AS varchar(100)) as RepeatInstrument,
    CAST(RepeatInstance AS varchar(3)) as RepeatInstance,
    CAST(FieldName AS varchar(100)) as FieldName,
    CAST(FieldValue AS varchar(max)) as FieldValue,
    CAST(COALESCE(CreatedOn, GETDATE()) AS datetime) as CreatedOn,
    CAST(GETDATE() AS datetime) as LastUpdated,
    CAST(0 AS int) as IsDeleted
FROM source_data
