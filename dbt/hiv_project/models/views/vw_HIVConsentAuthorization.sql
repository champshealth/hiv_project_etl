{{
  config(
    materialized = 'view'
  )
}}

-- This view is used to upsert HIV study consent authorization records into the ConsentAuthorization table
-- Only completed consent tracking forms with mits_type = 'CH00050' are included
SELECT
    newid() as Id,
    RIGHT(ChampsId, 5) as AuthId,
    ChampsId,
    SiteId,
    'CH04724' as Protocol,
    'CH00050' as ConsentType,
    'CH00585' as AuthorizationCode,
    'CH00582' as Action,
    1 as Active,
    1 as Valid,
    '4.0.0' as VersionOfDataSpecification,
    [elig_mits_consent_dt] as EventDate,
    'adult_hiv_study' as FileName,
    GETDATE() as CreatedOn,
    GETDATE() as ModifiedOn,
    GETDATE() as UploadedOn
FROM
    (
        SELECT
            ChampsId,
            FieldName,
            MAX(FieldValue) AS FieldValue,
            MAX(Site.Id) as SiteId
        FROM {{ ref('vw_HIVProject1_1') }}
        JOIN {{ source('dbo', 'Site') }} on Site.SiteId = {{ ref('vw_HIVProject1_1') }}.SiteId
        WHERE FormName = 'consent_tracking'
        AND FieldName IN (
            'mits_type',
            'elig_mits_consent_dt',
            'consent_tracking_complete'
        )
        GROUP BY ChampsId, FieldName
    ) AS SourceTable
    PIVOT
    (
        MAX(FieldValue)
        FOR FieldName IN (
            [mits_type],
            [elig_mits_consent_dt],
            [consent_tracking_complete]
        )
    ) AS PivotTable
WHERE mits_type = 'CH00050'
AND [consent_tracking_complete] = '2'
