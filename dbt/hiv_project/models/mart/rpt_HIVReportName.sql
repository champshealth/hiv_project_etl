{{
  config(
    materialized='table',
    full_refresh=true,
    column_types={
      'ReportViewName': 'VARCHAR(200)',
      'ReportViewId': 'VARCHAR(100)', 
      'ReportSequence': 'TINYINT',
      'ReportUri': 'VARCHAR(200)',
      'ReportUriHeader': 'VARCHAR(200)',
      'PackageType': 'VARCHAR(50)'
    }
  )
}}

/*
This is a lookup table for HIV report configuration including report naming and URLs.
The data is loaded from a CSV file containing report mappings for Tableau.
This table supports report generation for the HIV project.
*/

-- Load data from CSV file
SELECT
    ReportViewName,
    ReportViewId,
    ReportSequence,
    ReportUri,
    ReportUriHeader,
    PackageType,
    GETDATE() AS CreatedOn
FROM {{ source('hiv_data_staging' ,'seed_rpt_HIVReportName') }}

