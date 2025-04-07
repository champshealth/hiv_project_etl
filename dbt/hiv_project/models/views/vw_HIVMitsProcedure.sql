{{
  config(
    materialized = 'view'
  )
}}

-- This view is used to upsert HIV study MITS procedure data into the MITSProcedure table
SELECT  
    newid() as id, 
    SiteId, 
    ChampsId, 
    [mits_performed] as MITSPerformed, 
    [champs_kit_id] as SpecimenKitId,
    -- [mits_dod_dt], 
    [mits_rcvd_time] as DateBodyReceived, 
    [mits_location] as MITSLocation,  
    [mits_start_dt] as DateProcedureStarted, 
    [mits_start_time] as TimeProcedureStarted,
    [mits_time_complete] as TimeProcedureCompleted, 
    [mits_sex] as SexOfDeceased, 
    'adult_hiv_study' as FileName, 
    1 as Active, 
    GETDATE() as CreatedOn, 
    GETDATE() as ModifiedOn, 
    GETDATE() as UploadedOn
FROM
(    
    SELECT 
        ChampsId, 
        FieldName, 
        FieldValue, 
        Site.Id as SiteId
    FROM {{ ref('HIVProject3_1') }}
    LEFT JOIN {{ source('dbo', 'Site') }} on Site.SiteISOCode = LEFT(ChampsId, 2)
    WHERE 
        -- ChampsId = 'DWHV00001' and
        (
            FieldName LIKE 'mits_performed%'  
            OR FieldName LIKE 'champs_kit_id' 
            OR FieldName IN (
                'mits_dod_dt', 
                'mits_rcvd_time', 
                'mits_location', 
                'mits_start_time', 
                'mits_start_dt',
                'mits_time_complete', 
                'mits_sex'
            )
        )
) source
PIVOT
(
    MAX(FieldValue)
    FOR FieldName IN (
        [mits_performed], 
        [champs_kit_id], 
        [mits_dod_dt], 
        [mits_rcvd_time],
        [mits_location], 
        [mits_start_time], 
        [mits_start_dt], 
        [mits_time_complete],
        [mits_sex]
    )
) AS pivoted
WHERE mits_performed = 'CH00002'