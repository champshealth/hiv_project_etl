-- VIEW
-- Schema: stg
-- Name: vw_HIVMitsProcedure
-- Generated: 2025-02-26 22:17:56.972653

CREATE view [stg].[vw_HIVMitsProcedure] as
-- this view is used to upsert HIV study MITS procedure data into the MITSProcedure table
select  newid() id, SiteId, ChampsId , 
[mits_performed] MITSPerformed , 
[champs_kit_id] SpecimenKitId,
-- [mits_dod_dt] , 
[mits_rcvd_time] DateBodyReceived , 
[mits_location] MITSLocation,  
[mits_start_dt] DateProcedureStarted, 
[mits_start_time] TimeProcedureStarted,
[mits_time_complete] TimeProcedureCompleted
, [mits_sex] SexOfDeceased , 'adult_hiv_study' FileName, 
 1 Active , GETDATE() CreatedOn, GETDATE() ModifiedOn, GETDATE() UploadedOn
from
(    select ChampsId, FieldName, FieldValue, Site.Id SiteId
    from stg.HIVProject3_1_stg 
    left join Site on Site.SiteISOCode = left(ChampsId, 2)
    where -- ChampsId = 'DWHV00001' and
    ( FieldName like 'mits_performed%'  or FieldName like 'champs_kit_id' 
        or FieldName in ('mits_dod_dt', 'mits_rcvd_time', 'mits_location', 'mits_start_time', 
                'mits_start_dt','mits_time_complete', 'mits_sex' ))
) source
pivot
(
    max(FieldValue)
    for FieldName in ([mits_performed], [champs_kit_id], [mits_dod_dt], [mits_rcvd_time],
                     [mits_location], [mits_start_time], [mits_start_dt], [mits_time_complete]
                    , [mits_sex])
) as pivoted
where mits_performed = 'CH00002'