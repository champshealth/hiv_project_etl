-- VIEW
-- Schema: stg
-- Name: vw_HIVMitsSpecimensCollect
-- Generated: 2025-02-26 22:17:56.974010

CREATE view [stg].[vw_HIVMitsSpecimensCollect] as
-- this view is used to upsert HIV study MITS specimen collection data into the MITSSpecimensCollected table
-- A single row for each ChampsId KitId and CollectionDate
select newid() id, SiteId, ChampsId ,  
[champs_kit_id] KitId, mits_start_dt CollectionDate, 'CH00001' MITSCollect,
'adult_hiv_study' FileName, 
 1 Active , GETDATE() CreatedOn, GETDATE() ModifiedOn, GETDATE() UploadedOn,
 'HIV_PROJECT_ETL' CreatedBy, 'HIV_PROJECT_ETL' ModifiedBy, 'HIV_PROJECT_ETL' UploadedBy
from 
(select proj3_1.ChampsId, FieldName, FieldValue, ct.SiteId
    from stg.HIVProject3_1_stg proj3_1
    join ConsentTracking ct on ct.ChampsId = proj3_1.ChampsId 
                            and ct.ConsentType = 'CH00050' -- MITS Consent required
                            and [FileName] = 'adult_hiv_study'
                            and Active =1
    where  -- proj3_1.ChampsId = 'DWHV00001' and
    ( FieldName like 'mits_performed%'  or FieldName like 'champs_kit_id' 
      or FieldName in ( 'mits_start_dt' )
    )
) source
pivot
(
    max(FieldValue)
    for FieldName in ([mits_performed], [champs_kit_id], [mits_start_dt])
) as pivoted
where mits_performed = 'CH00002'