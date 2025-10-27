{{
  config(
    materialized='table',
    full_refresh=true
  )
}}

-- This model contains the data dictionary for the HIV Project 3.1 REDCap instrument
-- All field definitions, labels, and types are stored here for reference and reporting
SELECT
  SequenceId,
  FormName,
  FormSequenceId,
  SectionHeader,
  FieldName,
  FieldLabel,
  FieldType,
  ReportType,
  FileName,
  CreatedOn,
  Active
FROM {{ source('hiv_data_staging', 'HIVDataDictProj3_1') }}