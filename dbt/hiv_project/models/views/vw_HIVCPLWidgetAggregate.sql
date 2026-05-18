{{
  config(
    materialized = 'view'
  )
}}

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
    sp_lab.SitePathDiagModifiedOn,
    sp_lab.SitePathFindingModifiedOn,
    sp_lab.SitePathTissueModifiedOn,
    sp_lab.LaboratoryResultsModifiedOn,
    sp_lab.PlacentaExaminationModifiedOn,
    dn.SiteId as SiteGuid,
    Site.Name as SiteName
FROM {{ ref('vw_HIVDeathNotification') }} dn
JOIN {{ source('dbo', 'Site') }} ON dn.SiteId = Site.Id
JOIN {{ source('dbo', 'ConsentTracking') }} ct ON dn.ReportId = ct.ReportId 
    AND ct.Active = 1 
    AND dn.SiteId = ct.SiteId
    AND dn.CatchmentId = ct.CatchmentId
LEFT JOIN (
    SELECT ChampsId, MAX(cast(CreatedOn as date)) as CreatedOn
    FROM {{ ref('HIVClinicalAbstract') }}
    GROUP BY ChampsId
) ca ON ct.ChampsId = ca.ChampsId
LEFT JOIN (
    SELECT [SiteId], [ChampsId], [FileName], cast(CreatedOn as date) CreatedOn
    FROM {{ ref('vw_HIVMitsProcedure') }}
    WHERE SiteId is not null
) mproc ON ct.ChampsId = mproc.ChampsId
       AND ct.[FileName] = mproc.[FileName] --'adult_hiv_study'
LEFT JOIN (
    SELECT
        ChampsId,
        MAX(CASE WHEN FormName = 'site_pathology_report'
                 THEN cast(CreatedOn as date) END) as SitePathDiagModifiedOn,
        MAX(CASE WHEN FormName = 'site_pathology_report'
                 THEN cast(CreatedOn as date) END) as SitePathFindingModifiedOn,
        MAX(CASE WHEN FormName = 'site_pathology_report'
                 THEN cast(CreatedOn as date) END) as SitePathTissueModifiedOn,
        MAX(CASE WHEN FormName IN ('ast','bld_microbiology_results','clinical_lab_results',
                                   'csf_microbiology_results','lung_microbiology_results')
                 THEN cast(CreatedOn as date) END) as LaboratoryResultsModifiedOn,
        MAX(CASE WHEN FormName IN ('placenta_microscopic_examination','placenta_gross_examination')
                 THEN cast(CreatedOn as date) END) as PlacentaExaminationModifiedOn
    FROM {{ ref('vw_HIVProject3_1_rpt') }}
    WHERE FormName IN (
        'site_pathology_report',
        'ast','bld_microbiology_results','clinical_lab_results',
        'csf_microbiology_results','lung_microbiology_results',
        'placenta_microscopic_examination','placenta_gross_examination'
    )
    GROUP BY ChampsId
) sp_lab ON ct.ChampsId = sp_lab.ChampsId