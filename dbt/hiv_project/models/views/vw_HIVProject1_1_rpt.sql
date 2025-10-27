{{
  config(
    materialized = 'view'
  )
}}

-- This view is used to display the HIV Project 1.1 data in Tableau Decode Report
select 
  p11.SiteId, 
  p11.CatchmentId, 
  p11.ChampsId, 
  p11.FieldName, 
  p11.FieldValue,
  case 
    when dict.FieldType in ('radio', 'checkbox', 'dropdown') 
    then isnull(ccd.c_pref_name, p11.FieldValue) 
    else p11.FieldValue 
  end as FieldValueLabel,
  dict.FormName, 
  dict.FormSequenceId,
  dict.SectionHeader,
  dict.FieldLabel, 
  dict.FieldType, 
  dict.SequenceId,
  dict.ReportType
from {{ ref('HIVProject1_1') }} p11
left join {{ source('dbo', 'vw_champs_codes_distinct') }} ccd on p11.FieldValue = ccd.champs_local_code
left join {{ ref('HIVDataDictProj1_1') }} dict on p11.FieldName = dict.FieldName
where p11.IsDeleted = 0
and dict.Active = 1
and p11.FieldName != concat(dict.FormName, '_complete') -- Exclude completion field