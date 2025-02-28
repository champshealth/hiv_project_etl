-- VIEW
-- Schema: stg
-- Name: vw_HIVConsentTracking
-- Generated: 2025-02-26 22:17:56.968135

CREATE view [stg].[vw_HIVConsentTracking] as
-- this view is used to upsert HIV study consent data into the ConsentTracking table
-- FileName is set to  adult_hiv_study for all records
-- only completed forms recrods are inserted
SELECT newid() Id,   ConsentTrackingSiteId, ReportId,  CatchmentId, ChampsId, [elig_mits_consent] ConsentGranted,
 [mits_type] [ConsentType], [elig_mits_consent_dt] [ConsentDate],SiteId, 'adult_hiv_study' FileName, GETDATE() CreatedOn,
 1 Active
FROM 
    (
        SELECT ReportId, Site.SiteId ConsentTrackingSiteId, CatchmentId,  ChampsId, FieldName, FieldValue, Site.Id SiteId
        FROM vw_HIVProject1_1 
        join Site on Site.SiteId = vw_HIVProject1_1.SiteId
        WHERE FormName = 'consent_tracking'
        AND FieldName IN ('mits_type', 'elig_mits_consent', 
                            'elig_mits_consent_dt', 'consent_tracking_complete')
    ) AS SourceTable
    PIVOT
    (
        MAX(FieldValue)
        FOR FieldName IN ([elig_mits_consent], [mits_type], [elig_mits_consent_dt],
                        [consent_tracking_complete])
    ) AS PivotTable
where mits_type = 'CH00050' 
and [consent_tracking_complete] = '2'
