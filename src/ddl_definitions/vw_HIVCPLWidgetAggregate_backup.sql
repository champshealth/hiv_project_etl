-- BACKUP: Original vw_HIVCPLWidgetAggregate view definition
-- Captured: 2026-05-17
-- Use this to restore the view if the optimized version produces different results.
-- Apply against the target DB after resolving schema references (hiv / dbo).

-- This view is to populate the CPL Widget Aggregate table for Adult HIV cases
SELECT 
    ct.ChampsId,
    dn.ReportId,
    dn.CatchmentId,
    DateOfDeathNotification,
    DATEDIFF(day, DateOfDeathNotification, getdate()) as DaysSinceDeathNotification,
    DeathNotificationSiteId,
    getdate() as DemographicsModifiedOn,
    mproc.CreatedOn as MITSProcedureModifiedOn,
    ca.CreatedOn as ChildAbstractionModifiedOn,
    sp.SitePathDiagModifiedOn,
    sp.SitePathFindingModifiedOn,
    sp.SitePathTissueModifiedOn,
    lab_placenta.LaboratoryResultsModifiedOn,
    lab_placenta.PlacentaExaminationModifiedOn,
    dn.SiteId as SiteGuid,
    Site.Name as SiteName
FROM hiv.vw_HIVDeathNotification dn
JOIN dbo.Site ON dn.SiteId = Site.Id
JOIN dbo.ConsentTracking ct ON dn.ReportId = ct.ReportId 
    AND ct.Active = 1 
    AND dn.SiteId = ct.SiteId
    AND dn.CatchmentId = ct.CatchmentId
LEFT JOIN (
    SELECT DISTINCT 
        ChampsId, 
        max(cast(CreatedOn as date)) as CreatedOn
    FROM hiv.HIVClinicalAbstract
    group by ChampsId
) ca ON ct.ChampsId = ca.ChampsId
LEFT JOIN (
    SELECT [SiteId], [ChampsId], [FileName], cast(CreatedOn as date) CreatedOn
    FROM hiv.vw_HIVMitsProcedure
    where SiteId is not null 
) mproc 
    on ct.ChampsId = mproc.ChampsId 
    and ct.[FileName] = mproc.[FileName]
LEFT JOIN (
    SELECT 
        ChampsId,
        FormName,  
        max(cast(CreatedOn as date)) as SitePathDiagModifiedOn,
        max(cast(CreatedOn as date)) as SitePathFindingModifiedOn,
        max(cast(CreatedOn as date)) as SitePathTissueModifiedOn
    FROM hiv.vw_HIVProject3_1_rpt
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
        FROM hiv.vw_HIVProject3_1_rpt
        WHERE FormName IN (
            'ast','bld_microbiology_results','clinical_lab_results', 
            'csf_microbiology_results', 'lung_microbiology_results',
            'placenta_microscopic_examination', 'placenta_gross_examination'
        )
    ) src
    GROUP BY ChampsId
) lab_placenta ON ct.ChampsId = lab_placenta.ChampsId
