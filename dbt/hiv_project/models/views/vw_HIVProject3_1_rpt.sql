{{
  config(
    materialized = 'view'
  )
}}

-- This view is used to display the HIV Project 3.1 Form data
-- in Tableau Decode Report
select 
  ct.SiteId as SiteId, 
  p.ChampsId, 
  p.RepeatInstrument, 
  p.RepeatInstance, 
  p.FieldName, 
  p.FieldValue,
  case 
    when dict.FieldType in ('radio', 'checkbox', 'dropdown') 
    then isnull(ccd.c_pref_name, p.FieldValue) 
    else p.FieldValue 
  end as FieldValueLabel,
  dict.[FormName], 
  dict.[FieldLabel], 
  dict.FieldType, 
  dict.SequenceId, 
  p.CreatedOn
from {{ ref('HIVProject3_1') }} p
join {{ source('dbo', 'ConsentTracking') }} ct on p.ChampsId = ct.ChampsId and ct.[FileName] = 'adult_hiv_study' and ct.Active = 1
left join {{ ref('HIVDataDictProj3_1') }} dict on p.FieldName = dict.FieldName
left join {{ source('dbo', 'vw_champs_codes_distinct') }} ccd on p.FieldValue = ccd.champs_local_code