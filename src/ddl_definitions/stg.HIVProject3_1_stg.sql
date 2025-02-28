-- Schema: stg
-- Table: HIVProject3_1_stg
-- Generated: 2025-02-26 22:17:56.839980

CREATE TABLE [stg].[HIVProject3_1_stg] (    [Id] [varchar](100) NOT NULL,    [ChampsId] [varchar](9) NULL,    [RepeatInstrument] [varchar](100) NULL,    [RepeatInstance] [varchar](3) NULL,    [FieldName] [varchar](100) NULL,    [FieldValue] [varchar](max) NULL,    [CreatedOn] [datetime2] NOT NULL,) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]