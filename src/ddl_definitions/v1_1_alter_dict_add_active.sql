-- changes to hiv_project_etl v1.1
-- DDL for adding Active flag to data dict tables, set default to 1 (active)
-- HIVDataDictProj3_1, HIVDataDictProj1_1, HIVDataDictClinicalAbstr
-- check if column already exists and then add if not

IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE Name = N'Active' 
      AND Object_ID = Object_ID(N'hiv.HIVDataDictProj3_1')
)
BEGIN
    ALTER TABLE [hiv].[HIVDataDictProj3_1]
    ADD Active SMALLINT NOT NULL DEFAULT 1;
END
GO

-- Add Active flag to [hiv].[HIVDataDictProj1_1]
IF NOT EXISTS (SELECT 1 FROM sys.columns 
               WHERE Name = N'Active' 
               AND Object_ID = Object_ID(N'hiv.HIVDataDictProj1_1')
               )
BEGIN
Alter  TABLE [hiv].[HIVDataDictProj1_1] ADD  Active SMALLINT NOT NULL DEFAULT 1 ;
END
GO

-- Add Active flag to [hiv].[HIVDataDictClinicalAbstr]
IF NOT EXISTS (SELECT 1 FROM sys.columns 
               WHERE Name = N'Active' 
               AND Object_ID = Object_ID(N'hiv.HIVDataDictClinicalAbstr')
               )
BEGIN
Alter  TABLE [hiv].[HIVDataDictClinicalAbstr] ADD  Active SMALLINT NOT NULL DEFAULT 1 ;
END
GO

-- do the same for these tables in the stg schema
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE Name = N'Active' 
      AND Object_ID = Object_ID(N'stg.HIVDataDictProj3_1')
)
BEGIN
    ALTER TABLE [stg].[HIVDataDictProj3_1]
    ADD Active SMALLINT NOT NULL DEFAULT 1;
END
GO
-- Add Active flag to [stg].[HIVDataDictProj1_1]
IF NOT EXISTS (SELECT 1 FROM sys.columns 
               WHERE Name = N'Active' 
               AND Object_ID = Object_ID(N'stg.HIVDataDictProj1_1')
               )
BEGIN
Alter  TABLE [stg].[HIVDataDictProj1_1] ADD  Active SMALLINT NOT NULL DEFAULT 1 ;
END

GO
-- Add Active flag to [stg].[HIVDataDictClinicalAbstr]
IF NOT EXISTS (SELECT 1 FROM sys.columns 
               WHERE Name = N'Active' 
               AND Object_ID = Object_ID(N'stg.HIVDataDictClinicalAbstr')
               )
BEGIN
Alter  TABLE [stg].[HIVDataDictClinicalAbstr] ADD  Active SMALLINT NOT NULL DEFAULT 1 ;
END
GO

-- Add SectionHeader varchar (200) to HIVDataDictProj3_1, HIVDataDictProj1_1, HIVDataDictClinicalAbstr
-- Add SectionHeader to [hiv].[HIVDataDictProj3_1]
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE Name = N'SectionHeader' 
      AND Object_ID = Object_ID(N'hiv.HIVDataDictProj3_1')
)
BEGIN
    ALTER TABLE [hiv].[HIVDataDictProj3_1]
    ADD SectionHeader VARCHAR(200) NULL;
END
GO
-- Add SectionHeader to [hiv].[HIVDataDictProj1_1]
IF NOT EXISTS (SELECT 1 FROM sys.columns 
               WHERE Name = N'SectionHeader' 
               AND Object_ID = Object_ID(N'hiv.HIVDataDictProj1_1')
               )
BEGIN
Alter  TABLE [hiv].[HIVDataDictProj1_1] ADD  SectionHeader VARCHAR(200) NULL ;
END
GO
-- Add SectionHeader to [hiv].[HIVDataDictClinicalAbstr]
IF NOT EXISTS (SELECT 1 FROM sys.columns 
               WHERE Name = N'SectionHeader' 
               AND Object_ID = Object_ID(N'hiv.HIVDataDictClinicalAbstr')
               )
BEGIN
Alter  TABLE [hiv].[HIVDataDictClinicalAbstr] ADD  SectionHeader VARCHAR(200) NULL ;
END
GO

-- do the same for these tables in the stg schema
-- Add SectionHeader to [stg].[HIVDataDictProj3_1]
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE Name = N'SectionHeader' 
      AND Object_ID = Object_ID(N'stg.HIVDataDictProj3_1')
)
BEGIN
    ALTER TABLE [stg].[HIVDataDictProj3_1]
    ADD SectionHeader VARCHAR(200) NULL;
END
GO
-- Add SectionHeader to [stg].[HIVDataDictProj1_1]
IF NOT EXISTS (SELECT 1 FROM sys.columns 
               WHERE Name = N'SectionHeader' 
               AND Object_ID = Object_ID(N'stg.HIVDataDictProj1_1')
)
BEGIN
Alter  TABLE [stg].[HIVDataDictProj1_1] ADD  SectionHeader VARCHAR(200) NULL ;
END
GO
-- Add SectionHeader to [stg].[HIVDataDictClinicalAbstr]
IF NOT EXISTS (SELECT 1 FROM sys.columns 
               WHERE Name = N'SectionHeader' 
               AND Object_ID = Object_ID(N'stg.HIVDataDictClinicalAbstr')
)
BEGIN
Alter  TABLE [stg].[HIVDataDictClinicalAbstr] ADD  SectionHeader VARCHAR(200) NULL ;
END
GO

-- Check if ReportType varchar(5) column exists in [stg].[HIVDataDictProj1_1], if not add it
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE Name = N' ' 
      AND Object_ID = Object_ID(N'stg.HIVDataDictProj1_1')
)
BEGIN
Alter  TABLE [stg].[HIVDataDictProj1_1] ADD  ReportType VARCHAR(5) NULL default '1.1' ;
END
GO

-- Check if ReportType varchar(5) column exists in [stg].[HIVDataDictClinicalAbstr], if not add it
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE Name = N'ReportType' 
      AND Object_ID = Object_ID(N'stg.HIVDataDictClinicalAbstr')
)
BEGIN
Alter  TABLE [stg].[HIVDataDictClinicalAbstr] ADD  ReportType VARCHAR(5) NULL default '3.2' ;
END
GO

-- Check if ReportType column exists in stg.HIVDataDictProj3_1, if not add it
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE Name = N'ReportType' 
      AND Object_ID = Object_ID(N'stg.HIVDataDictProj3_1')
)
BEGIN
    ALTER TABLE [stg].[HIVDataDictProj3_1]
    ADD ReportType AS (
        CASE 
            WHEN FormName IN ('disposition_of_body_form', 
                              'lung_only_mits', 
                              'mits_specimen_collection_form'
                             ) 
                THEN '3.1.1'
            WHEN FormName IN ('ast', 
                              'bld_microbiology_results', 
                              'clinical_lab_results', 
                              'csf_microbiology_results', 
                              'lung_microbiology_results'
                             ) 
                THEN '3.1.2'
            WHEN FormName IN ('site_pathology_report') 
                THEN '3.1.3'
            WHEN FormName IN ('placenta_gross_examination', 
                              'placenta_microscopic_examination'
                             ) 
                THEN '3.1.4'
            ELSE NULL
        END
    );
END

GO

-- Add column FormSequenceId INT NULL to stg.HIVDataDictProj3_1 if it does not exist
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE Name = N'FormSequenceId' 
      AND Object_ID = Object_ID(N'stg.HIVDataDictProj3_1')
)
BEGIN
    ALTER TABLE [stg].[HIVDataDictProj3_1]
    ADD FormSequenceId INT NULL;
END

GO

-- Add column FormSequenceId INT NULL to stg.HIVDataDictProj1_1 if it does not exist
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE Name = N'FormSequenceId' 
      AND Object_ID = Object_ID(N'stg.HIVDataDictProj1_1')
)
BEGIN
    ALTER TABLE [stg].[HIVDataDictProj1_1]
    ADD FormSequenceId INT NULL;
END
GO
-- Add column FormSequenceId INT NULL to stg.HIVDataDictClinicalAbstr if it does not exist
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE Name = N'FormSequenceId' 
      AND Object_ID = Object_ID(N'stg.HIVDataDictClinicalAbstr')
)
BEGIN
    ALTER TABLE [stg].[HIVDataDictClinicalAbstr]
    ADD FormSequenceId INT NULL;
END
GO


-- end of script