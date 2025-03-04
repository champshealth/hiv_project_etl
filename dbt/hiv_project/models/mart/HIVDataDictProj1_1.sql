{{
  config(
    materialized='table',
    schema='hiv',
    full_refresh=true
  )
}}

-- This model contains the data dictionary for the HIV Project 1.1 REDCap instrument
-- All field definitions, labels, and types are stored here for reference and reporting
SELECT
  SequenceId,
  FormName,
  FieldName,
  FieldLabel,
  FieldType,
  FileName,
  CreatedOn
FROM {{ source('hiv_data_staging', 'HIVDataDictProj1_1') }}