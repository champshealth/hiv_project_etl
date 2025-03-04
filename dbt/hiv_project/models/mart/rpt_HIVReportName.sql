{{
  config(
    materialized='table',
    schema='hiv',
    full_refresh=true
  )
}}

/*
This is a lookup table for HIV report configuration including report naming and URLs.
The data is loaded from a CSV file containing report mappings for Tableau.
This table supports report generation for the HIV project.
*/

-- Load data from CSV file
WITH source_data AS (
    SELECT 
        ReportViewName,
        ReportViewId,
        ReportSequence,
        ReportUri,
        ReportUriHeader,
        PackageType
    FROM {{ ref('seed_rpt_HIVReportName') }}
)

SELECT
    ReportViewName,
    ReportViewId,
    CAST(ReportSequence AS INT) AS ReportSequence,
    ReportUri,
    ReportUriHeader,
    PackageType,
    GETDATE() AS CreatedOn
FROM source_data