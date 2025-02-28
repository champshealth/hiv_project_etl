-- VIEW
-- Schema: stg
-- Name: vw_HIVClinicalAbstr_rpt
-- Generated: 2025-02-26 22:17:56.967022

CREATE view [stg].[vw_HIVClinicalAbstr_rpt] as
-- This view is used to display the HIV Project Clinical Abstraction Form data
-- in Tableau Decode Report
select ca.SiteId, ca.ChampsId, ca.FieldName, ca.FieldValue
,case when dict.FieldType in ('radio', 'checkbox' , 'dropdown') then isnull(ccd.c_pref_name, ca.FieldValue) else  ca.FieldValue end as FieldValueLabel
,dict.[FormName] , dict.[FieldLabel], dict.FieldType, dict.SequenceId
from  [stg].[HIVClinicalAbstract_stg] ca
left join vw_champs_codes_distinct ccd on ca.FieldValue = ccd.champs_local_code
left join [stg].[HIVDataDictClinicalAbstr] dict on ca.FieldName = dict.FieldName
