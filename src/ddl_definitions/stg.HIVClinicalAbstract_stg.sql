-- Schema: stg
-- Table: HIVClinicalAbstract_stg
-- Generated: 2025-02-26 22:17:56.831606

CREATE TABLE [stg].[HIVClinicalAbstract_stg] (    [Id] [varchar](100) NOT NULL,    [SiteId] [varchar](10) NULL,    [ChampsId] [varchar](10) NULL,    [FieldName] [varchar](255) NULL,    [FieldValue] [varchar](max) NULL,    [CreatedOn] [datetime] NULL,) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]