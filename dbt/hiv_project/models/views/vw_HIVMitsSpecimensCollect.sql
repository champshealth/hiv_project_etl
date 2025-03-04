{{
  config(
    materialized = 'view',
    schema = 'hiv'
  )
}}

-- This view is used to upsert HIV study MITS specimen collection data into the MITSSpecimensCollected table
-- A single row for each ChampsId KitId and CollectionDate
SELECT 
    newid() as id, 
    SiteId, 
    ChampsId,  
    [champs_kit_id] as KitId, 
    mits_start_dt as CollectionDate, 
    'CH00001' as MITSCollect,
    'adult_hiv_study' as FileName, 
    1 as Active, 
    GETDATE() as CreatedOn, 
    GETDATE() as ModifiedOn, 
    GETDATE() as UploadedOn,
    'HIV_PROJECT_ETL' as CreatedBy, 
    'HIV_PROJECT_ETL' as ModifiedBy, 
    'HIV_PROJECT_ETL' as UploadedBy
FROM 
(
    SELECT 
        proj3_1.ChampsId, 
        FieldName, 
        FieldValue, 
        ct.SiteId
    FROM {{ ref('HIVProject3_1') }} proj3_1
    JOIN {{ source('dbo', 'ConsentTracking') }} ct ON ct.ChampsId = proj3_1.ChampsId 
                                                  AND ct.ConsentType = 'CH00050' -- MITS Consent required
                                                  AND ct.[FileName] = 'adult_hiv_study'
                                                  AND ct.Active = 1
    WHERE  
        -- proj3_1.ChampsId = 'DWHV00001' and
        (
            FieldName LIKE 'mits_performed%'  
            OR FieldName LIKE 'champs_kit_id' 
            OR FieldName IN ('mits_start_dt')
        )
) source
PIVOT
(
    MAX(FieldValue)
    FOR FieldName IN (
        [mits_performed], 
        [champs_kit_id], 
        [mits_start_dt]
    )
) AS pivoted
WHERE mits_performed = 'CH00002'