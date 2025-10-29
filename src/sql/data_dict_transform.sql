-- duckdb query to transform data dictionary
-- this was pasted from duckdb notebook
-- and used to create data dictionary used in the config/config.py file
create or replace table hiv_31_data_dict as
select
  *
from
  read_csv(
    '/Users/shaileshnair/Documents/projects/hiv_project_etl/data_dictionaries/AdultHIVProject3_1_DataDict_2025-01-28.csv',
    all_varchar = true
  );

create or replace table hiv_31_data_dict as
select
  *
from
  read_csv(
    '/Users/shaileshnair/Documents/projects/hiv_project_etl/data_dictionaries/AdultHIVProject3_1_DataDict_2025-01-28.csv',
    all_varchar = true
  );

-- cell 2
create or replace table hiv_31_data_dict as
select
  *
from
  read_csv(
    '/Users/shaileshnair/Documents/projects/hiv_project_etl/data_dictionaries/AdultHIVProject3_1_DataDict_2025-01-28.csv',
    all_varchar = true
  );

create or replace table hiv_31_data_dict as
select
  *
from
  read_csv(
    '/Users/shaileshnair/Documents/projects/hiv_project_etl/data_dictionaries/AdultHIVProject3_1_DataDict_2025-01-28.csv',
    all_varchar = true
  );

-- cell 3
create or replace table  hiv_11_data_dict as
select * 
from read_csv('/Users/shaileshnair/Documents/projects/hiv_project_etl/data_dictionaries/AdultHIVProject1_1_DataDict_2024-12-11.csv',
  all_varchar = true)
;
WITH file_with_rownum AS (
    SELECT
        *,
        row_number() OVER () as rn
    FROM hiv_11_data_dict
),
first_appearance AS (
    -- Find the first row number (rn) for each distinct "Form Name"
    -- for setting form_sequence
    SELECT
        "Form Name",
        MIN(rn) as min_rn
    FROM file_with_rownum
    GROUP BY "Form Name"
),
form_sequence AS
(SELECT
    "Form Name",
    row_number() OVER (ORDER BY min_rn) as form_sequence_id
FROM first_appearance),
-- CTE 2: Create groups for each section
-- This CTE identifies groups of rows that belong to the same section.
-- A new group starts every time a non-null "Section Header" is encountered.
section_groups AS (
    SELECT
        *,
        SUM(CASE WHEN "Section Header" IS NOT NULL AND "Section Header" != '' THEN 1 ELSE 0 END) OVER (ORDER BY rn) AS section_group
    FROM file_with_rownum
)
-- Final SELECT: Fill the null "Section Header" values
-- Use the FIRST_VALUE window function to propagate the header within each group.
SELECT
  "Variable / Field Name",section_groups."Form Name", --"Section Header",
  FIRST_VALUE("Section Header")  OVER (PARTITION BY section_group ORDER BY rn) AS "Section Header",
  "Field Type",
  "Field Label", 
  "Choices, Calculations, OR Slider Labels","Field Note","Text Validation Type OR Show Slider Number",
  "Text Validation Min","Text Validation Max","Identifier?","Branching Logic (Show field only if...)","Required Field?","Custom Alignment",
  "Question Number (surveys only)","Matrix Group Name","Matrix Ranking?","Field Annotation","Active"
  ,form_sequence_id
FROM section_groups
join form_sequence on section_groups."Form Name" = form_sequence."Form Name"
order by rn;

-- cell 4
create or replace table  hiv_ca_data_dict as
select * 
from read_csv('/Users/shaileshnair/Documents/projects/hiv_project_etl/data_dictionaries/AdultHIVClinicalAbstr_DataDict_2024-10-30.csv',
  all_varchar = true)
;

-- NOTE: Before running this sql add Active Column to the File
-- CTE 1: Read the data and add a row number
-- A consistent row order is essential for this logic to work correctly.
-- Add row number (rn) to preserve the original order from the CSV file.

WITH file_with_rownum AS (
    SELECT
        *,
        row_number() OVER () as rn
    FROM hiv_ca_data_dict
),
first_appearance AS (
    -- Find the first row number (rn) for each distinct "Form Name"
    -- for setting form_sequence
    SELECT
        "Form Name",
        MIN(rn) as min_rn
    FROM file_with_rownum
    GROUP BY "Form Name"
),
form_sequence AS
(SELECT
    "Form Name",
    row_number() OVER (ORDER BY min_rn) as form_sequence_id
FROM first_appearance),
-- CTE 2: Create groups for each section
-- This CTE identifies groups of rows that belong to the same section.
-- A new group starts every time a non-null "Section Header" is encountered.
section_groups AS (
    SELECT
        *,
        SUM(CASE WHEN "Section Header" IS NOT NULL AND "Section Header" != '' THEN 1 ELSE 0 END) OVER (ORDER BY rn) AS section_group
    FROM file_with_rownum
)
-- Final SELECT: Fill the null "Section Header" values
-- Use the FIRST_VALUE window function to propagate the header within each group.
SELECT
     "Variable / Field Name",section_groups."Form Name", --"Section Header",
     CASE
        WHEN STARTS_WITH(FIRST_VALUE("Section Header") OVER (PARTITION BY section_group ORDER BY rn), '<div class="rich-text-field-label"><p>Adult Clinical Data Abstraction Form')
            THEN 'Adult Clinical Data Abstraction Form'
        WHEN STARTS_WITH(FIRST_VALUE("Section Header") OVER (PARTITION BY section_group ORDER BY rn), '<div class="rich-text-field-label"><p>CLINICAL SIGNS FROM CHART DURING ADMISSION')
            THEN 'CLINICAL SIGNS FROM CHART DURING ADMISSION'
        WHEN STARTS_WITH(FIRST_VALUE("Section Header") OVER (PARTITION BY section_group ORDER BY rn), '<div class="rich-text-field-label"><p>Diagnostic Testing')
            THEN 'Diagnostic Testing'
        ELSE FIRST_VALUE("Section Header") OVER (PARTITION BY section_group ORDER BY rn)
    END AS "Section Header",
    -- FIRST_VALUE("Section Header")  OVER (PARTITION BY section_group ORDER BY rn) AS "Section Header",
    "Field Type",
 "Field Label", 
"Choices, Calculations, OR Slider Labels","Field Note","Text Validation Type OR Show Slider Number",
"Text Validation Min","Text Validation Max","Identifier?","Branching Logic (Show field only if...)","Required Field?","Custom Alignment",
"Question Number (surveys only)","Matrix Group Name","Matrix Ranking?","Field Annotation","Active",
form_sequence.form_sequence_id
FROM section_groups
join form_sequence on section_groups."Form Name" = form_sequence."Form Name"
order by rn;