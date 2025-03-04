{{
  config(
    materialized = 'view',
    schema = 'hiv'
  )
}}

-- This view is used to upsert HIV study Death Notification data into the DeathNotification table
SELECT 
    newid() as Id, 
    -- FormName, 
    ReportId, 
    CatchmentId,  
    -- ChampsId, FieldName, 
    FieldValue as DateOfDeathNotification, 
    Site.Id as SiteId,
    Site.SiteId as DeathNotificationSiteId,
    'adult_hiv_study' as FileName, 
    1 as Active, 
    GETDATE() as CreatedOn, 
    GETDATE() as ModifiedOn, 
    GETDATE() as UploadedOn
FROM {{ ref('vw_HIVProject1_1') }}
JOIN {{ source('dbo', 'Site') }} on Site.SiteId = {{ ref('vw_HIVProject1_1') }}.SiteId
WHERE FormName like 'initial_death_notification'
AND FieldName IN ('report_death_dt')
AND CatchmentId != ''