{{
  config(
    materialized = 'view',
    schema = 'hiv'
  )
}}

-- This view is used to upsert HIV study consent data into the ConsentTracking table
-- FileName is set to adult_hiv_study for all records
-- Only completed forms records are inserted
SELECT 
    newid() as Id,   
    ConsentTrackingSiteId, 
    ReportId,  
    CatchmentId, 
    ChampsId, 
    [elig_mits_consent] as ConsentGranted,
    [mits_type] as [ConsentType], 
    [elig_mits_consent_dt] as [ConsentDate],
    SiteId, 
    'adult_hiv_study' as FileName, 
    GETDATE() as CreatedOn,
    1 as Active
FROM 
    (
        SELECT 
            ReportId, 
            Site.SiteId as ConsentTrackingSiteId, 
            CatchmentId,  
            ChampsId, 
            FieldName, 
            FieldValue, 
            Site.Id as SiteId
        FROM {{ ref('vw_HIVProject1_1') }}
        JOIN {{ source('dbo', 'Site') }} on Site.SiteId = {{ ref('vw_HIVProject1_1') }}.SiteId
        WHERE FormName = 'consent_tracking'
        AND FieldName IN (
            'mits_type', 
            'elig_mits_consent', 
            'elig_mits_consent_dt', 
            'consent_tracking_complete'
        )
    ) AS SourceTable
    PIVOT
    (
        MAX(FieldValue)
        FOR FieldName IN (
            [elig_mits_consent], 
            [mits_type], 
            [elig_mits_consent_dt],
            [consent_tracking_complete]
        )
    ) AS PivotTable
WHERE mits_type = 'CH00050' 
AND [consent_tracking_complete] = '2'