-- check if table exists in stg schema

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'HIVProject6_1_stg' AND schema_id = SCHEMA_ID('stg'))
BEGIN
CREATE TABLE [stg].[HIVProject6_1_stg](
	[Id] [varchar](100) PRIMARY KEY NOT NULL default NEWID(),
    PacketVersionId [varchar](100) NOT NULL,
	[ChampsId] [varchar](9) NOT NULL,
	[RepeatInstrument] [varchar](100) NULL,
	[RepeatInstance] [varchar](3) NULL,
	[FieldName] [varchar](100) NULL,
	[FieldValue] [varchar](max) NULL,
	[CreatedOn] [datetime2](7) NOT NULL default GETDATE()
);
END
GO
-- create or replace index on ChampsId
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_HIVProject6_1_stg_ChampsId' AND object_id = OBJECT_ID('stg.HIVProject6_1_stg'))
CREATE INDEX [idx_HIVProject6_1_stg_ChampsId] ON [stg].[HIVProject6_1_stg] ([ChampsId])
GO
-- create or replace index on field name
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_HIVProject6_1_stg_FieldName' AND object_id = OBJECT_ID('stg.HIVProject6_1_stg'))
CREATE INDEX [idx_HIVProject6_1_stg_FieldName] ON [stg].[HIVProject6_1_stg] ([FieldName])
GO

-- create or replace table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'HIVDataDictProj6_1' AND schema_id = SCHEMA_ID('stg'))
CREATE TABLE [stg].[HIVDataDictProj6_1](
	[SequenceId] [bigint] NULL,
	[FormName] [varchar](max) NULL,
	[FieldName] [varchar](max) NULL,
	[FieldLabel] [varchar](max) NULL,
	[FieldType] [varchar](max) NULL,
	[FileName] [varchar](max) NULL,
	[CreatedOn] [datetime] NULL,
	[Active] [smallint] NOT NULL default 1,
	[SectionHeader] [varchar](200) NULL,
	[FormSequenceId] [int] NULL,
	[ReportType] [varchar](100) NULL default '6.1'
) 
GO

-- check if table exists in hiv schema
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'HIVProject6_1' AND schema_id = SCHEMA_ID('hiv'))
BEGIN
CREATE TABLE [hiv].[HIVProject6_1](
	[Id] [varchar](100) NOT NULL,
	[PacketVersionId] [varchar](100) NOT NULL,
	[ChampsId] [varchar](9) NOT NULL,
	[RepeatInstrument] [varchar](100) NULL,
	[RepeatInstance] [varchar](3) NULL,
	[FieldName] [varchar](100) NULL,
	[FieldValue] [varchar](max) NULL,
	[CreatedOn] [datetime] NOT NULL,
	[LastUpdated] [datetime] NOT NULL,
	[IsDeleted] [int] NOT NULL
) 
END
GO
-- create or replace index on ChampsId
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_HIVProject6_1_ChampsId' AND object_id = OBJECT_ID('hiv.HIVProject6_1'))
CREATE INDEX [idx_HIVProject6_1_ChampsId] ON [hiv].[HIVProject6_1] ([ChampsId])
GO
-- create or replace index on field name
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_HIVProject6_1_FieldName' AND object_id = OBJECT_ID('hiv.HIVProject6_1'))
CREATE INDEX [idx_HIVProject6_1_FieldName] ON [hiv].[HIVProject6_1] ([FieldName])
GO
-- create or replace index on PacketVersionId
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_HIVProject6_1_PacketVersionId' AND object_id = OBJECT_ID('hiv.HIVProject6_1'))
CREATE INDEX [idx_HIVProject6_1_PacketVersionId] ON [hiv].[HIVProject6_1] ([PacketVersionId])
GO
