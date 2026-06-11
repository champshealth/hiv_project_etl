{{
  config(
    materialized='table',
    post_hook=[
      "CREATE NONCLUSTERED INDEX IX_HIVProject1_1_site_catchment_report ON {{ this }} (SiteId, CatchmentId, ReportId)",
    ]
  )
}}

SELECT
  CAST(Id AS varchar(100)) AS Id,
  CAST(SiteId AS varchar(10)) AS SiteId,
  CAST(CatchmentId AS varchar(10)) AS CatchmentId,
  CAST(ReportId AS varchar(100)) AS ReportId,
  CAST(ChampsId AS varchar(9)) AS ChampsId,
  CAST(FieldName AS varchar(255)) AS FieldName,
  CAST(FieldValue AS varchar(max)) AS FieldValue,
  CAST(GETDATE() AS datetime) AS LastUpdated,
  CAST(0 AS int) AS IsDeleted
FROM {{ source('hiv_data_staging', 'HIVProject1_1_stg') }}
