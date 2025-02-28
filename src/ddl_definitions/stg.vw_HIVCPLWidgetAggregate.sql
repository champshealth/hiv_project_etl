-- VIEW
-- Schema: stg
-- Name: vw_HIVCPLWidgetAggregate
-- Generated: 2025-02-26 22:17:56.969532

CREATE view [stg].[vw_HIVCPLWidgetAggregate] as
-- This view is to populate the CPL Widget Aggregate table for Adult HIV cases
SELECT 
    ct.ChampsId,
    dn.ReportId,
    dn.CatchmentId,
    DateOfDeathNotification,
    DATEDIFF(day, DateOfDeathNotification, getdate()) as DaysSinceDeathNotification,
    DeathNotificationSiteId,
    getdate() as DemographicsModifiedOn,
    ca.CreatedOn as ChildAbstractionModifiedOn,
    sp.SitePathDiagModifiedOn,
    sp.SitePathFindingModifiedOn,
    sp.SitePathTissueModifiedOn,
    lab_placenta.LaboratoryResultsModifiedOn,
    lab_placenta.PlacentaExaminationModifiedOn,
    dn.SiteId SiteGuid,
    Site.Name SiteName
FROM [stg].[vw_HIVDeathNotification] dn
JOIN Site ON dn.SiteId = Site.Id
JOIN ConsentTracking ct ON dn.ReportId = ct.ReportId 
    AND ct.Active = 1 
    AND dn.SiteId = ct.SiteId
    AND dn.CatchmentId = ct.CatchmentId
LEFT JOIN (
    SELECT DISTINCT ChampsId, 
           cast(CreatedOn as date) CreatedOn 
    FROM stg.HIVClinicalAbstract_stg
) ca ON ct.ChampsId = ca.ChampsId
LEFT JOIN (
    SELECT ChampsId,
           FormName,  
           max(cast(CreatedOn as date)) SitePathDiagModifiedOn,
           max(cast(CreatedOn as date)) SitePathFindingModifiedOn,
           max(cast(CreatedOn as date)) SitePathTissueModifiedOn
    FROM stg.vw_HIVProject3_1_rpt
    WHERE FormName = 'site_pathology_report'
    GROUP BY ChampsId, FormName
) sp ON ct.ChampsId = sp.ChampsId
LEFT JOIN (
    SELECT 
        ChampsId,
        MAX(CASE WHEN FormCategory = 'lab' THEN ModifiedDate END) as LaboratoryResultsModifiedOn,
        MAX(CASE WHEN FormCategory = 'placenta' THEN ModifiedDate END) as PlacentaExaminationModifiedOn
    FROM (
        SELECT 
            ChampsId,
            CASE 
                WHEN FormName IN ('ast','bld_microbiology_results','clinical_lab_results', 
                                'csf_microbiology_results', 'lung_microbiology_results') 
                THEN 'lab'
                WHEN FormName IN ('placenta_microscopic_examination', 'placenta_gross_examination') 
                THEN 'placenta'
            END as FormCategory,
            cast(CreatedOn as date) as ModifiedDate
        FROM stg.vw_HIVProject3_1_rpt
        WHERE FormName IN (
            'ast','bld_microbiology_results','clinical_lab_results', 
            'csf_microbiology_results', 'lung_microbiology_results',
            'placenta_microscopic_examination', 'placenta_gross_examination'
        )
    ) src
    GROUP BY ChampsId
) lab_placenta ON ct.ChampsId = lab_placenta.ChampsId