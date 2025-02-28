-- VIEW
-- Schema: stg
-- Name: vw_HIVDeathNotification
-- Generated: 2025-02-26 22:17:56.970797

CREATE view stg.vw_HIVDeathNotification as
-- this view is used to upsert HIV study Death Notification data into the DeathNotification table
SELECT newid() Id , -- FormName, 
    ReportId, CatchmentId,  
    -- ChampsId, FieldName, 
    FieldValue DateOfDeathNotification, 
    Site.Id SiteId,Site.SiteId DeathNotificationSiteId,
     'adult_hiv_study' FileName, 1 Active, GETDATE()  CreatedOn, GETDATE() ModifiedOn, GETDATE() UploadedOn
FROM stg.vw_HIVProject1_1 
join Site on Site.SiteId = vw_HIVProject1_1.SiteId
WHERE FormName like 'initial_death_notification'
AND FieldName IN ('report_death_dt' )
and CatchmentId != ''