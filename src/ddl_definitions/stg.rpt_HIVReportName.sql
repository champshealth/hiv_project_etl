-- Schema: stg
-- Table: rpt_HIVReportName
-- Generated: 2025-02-26 22:17:56.841888

CREATE TABLE [stg].[rpt_HIVReportName] (    [ReportViewName] [varchar](200) NOT NULL,    [ReportViewId] [varchar](100) NOT NULL,    [ReportSequence] [tinyint] NOT NULL,    [ReportUri] [varchar](200) NOT NULL,    [ReportUriHeader] [varchar](200) NULL,    [PackageType] [varchar](50) NULL,) ON [PRIMARY]