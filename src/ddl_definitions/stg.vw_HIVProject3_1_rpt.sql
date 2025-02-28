-- VIEW
-- Schema: stg
-- Name: vw_HIVProject3_1_rpt
-- Generated: 2025-02-26 22:17:56.998161

CREATE view [stg].[vw_HIVProject3_1_rpt] as
-- This view is used to display the HIV Project 3.1 Form data
-- in Tableau Decode Report
select ct.SiteId SiteId, p.ChampsId, p.RepeatInstrument, p.RepeatInstance  ,p.FieldName, p.FieldValue
,case when dict.FieldType in ('radio', 'checkbox' , 'dropdown') then isnull(ccd.c_pref_name, p.FieldValue) else  p.FieldValue end as FieldValueLabel
,dict.[FormName] , dict.[FieldLabel], dict.FieldType, dict.SequenceId, p.CreatedOn
from stg.HIVProject3_1_stg p
join ConsentTracking ct on p.ChampsId = ct.ChampsId and [FileName] = 'adult_hiv_study' and Active =1
left join stg.HIVDataDictProj3_1 dict on p.FieldName = dict.FieldName
left join vw_champs_codes_distinct ccd on p.FieldValue = ccd.champs_local_code