-- VIEW
-- Schema: stg
-- Name: vw_HIVProject1_1_rpt
-- Generated: 2025-02-26 22:17:56.990821

CREATE view [stg].[vw_HIVProject1_1_rpt] as
-- This view is used to display the HIV Project 1.1 Form data
-- in Tableau Decode Report
select p.SiteId, p.ChampsId, p.FieldName, p.FieldValue 
,case when dict.FieldType in ('radio', 'checkbox' , 'dropdown') then isnull(ccd.c_pref_name, p.FieldValue) else  p.FieldValue end as FieldValueLabel
,dict.[FormName] , dict.[FieldLabel], dict.FieldType, dict.SequenceId
from stg.HIVProject1_1_stg p
left join stg.HIVDataDictProj1_1 dict on p.FieldName = dict.FieldName
left join vw_champs_codes_distinct ccd on p.FieldValue = ccd.champs_local_code