-- This table definition is from the existing database for reference only
-- To assist with inserting the data into the ConsentAuthorization table
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ConsentAuthorization](
	[Id] [nvarchar](255) NOT NULL,
	[JobId] [nvarchar](255) NULL,
	[SiteId] [nvarchar](255) NULL,
	[FileName] [nvarchar](255) NULL,
	[Active] [int] NOT NULL,
	[AuthId] [nvarchar](255) NULL,
	[ChampsId] [nvarchar](255) NULL,
	[Action] [nvarchar](255) NULL,
	[Protocol] [nvarchar](255) NULL,
	[ConsentType] [nvarchar](255) NULL,
	[AuthorizationCode] [nvarchar](255) NULL,
	[WithdrawalReason] [nvarchar](255) NULL,
	[OtherReasonForWithdrawal] [nvarchar](4000) NULL,
	[FutureContact] [nvarchar](255) NULL,
	[DataEntered] [nvarchar](255) NULL,
	[TimingOfWithrawal] [nvarchar](255) NULL,
	[VersionOfDataSpecification] [nvarchar](255) NULL,
	[Valid] [bit] NOT NULL,
	[EventDate] [date] NULL,
	[CreatedOn] [datetime] NOT NULL,
	[CreatedBy] [nvarchar](128) NOT NULL,
	[UploadedOn] [datetime] NOT NULL,
	[UploadedBy] [nvarchar](128) NOT NULL,
	[ModifiedOn] [datetime] NULL,
	[ModifiedBy] [nvarchar](128) NULL,
	[DuplicationKey]  AS (CONVERT([nvarchar](32),hashbytes('MD5',upper((((isnull([AuthId],'')+isnull([ChampsId],''))+isnull([Protocol],''))+isnull([ConsentType],''))+isnull([AuthorizationCode],''))),(2))) PERSISTED,
	[HASH]  AS (CONVERT([nvarchar](32),hashbytes('MD5',upper(((((((((((isnull([AuthId],'')+isnull([ChampsId],''))+isnull([Action],''))+isnull([Protocol],''))+isnull([ConsentType],''))+isnull([AuthorizationCode],''))+isnull([WithdrawalReason],''))+isnull([OtherReasonForWithdrawal],''))+isnull([FutureContact],''))+isnull([DataEntered],''))+isnull([TimingOfWithrawal],''))+isnull(CONVERT([nvarchar](32),[EventDate],(127)),''))),(2))),
 CONSTRAINT [PK_ConsentAuthorization_Id] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
CREATE NONCLUSTERED INDEX [IX_ConsentAuthorization_UpsertOn] ON [dbo].[ConsentAuthorization]
(
	[AuthId] ASC,
	[ChampsId] ASC,
	[Protocol] ASC,
	[AuthorizationCode] ASC,
	[Active] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, FILLFACTOR = 80, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
ALTER TABLE [dbo].[ConsentAuthorization] ADD  CONSTRAINT [DF_ConsentAuthorization_Valid]  DEFAULT ((1)) FOR [Valid]
GO
ALTER TABLE [dbo].[ConsentAuthorization] ADD  CONSTRAINT [DF_ConsentAuthorization_CreatedOn]  DEFAULT (getdate()) FOR [CreatedOn]
GO
ALTER TABLE [dbo].[ConsentAuthorization] ADD  CONSTRAINT [DF_ConsentAuthorization_CreatedBy]  DEFAULT ('00000000-0000-0000-0000-000000000000') FOR [CreatedBy]
GO
ALTER TABLE [dbo].[ConsentAuthorization] ADD  CONSTRAINT [DF_ConsentAuthorization_UploadedOn]  DEFAULT (getdate()) FOR [UploadedOn]
GO
ALTER TABLE [dbo].[ConsentAuthorization] ADD  CONSTRAINT [DF_ConsentAuthorization_UploadedBy]  DEFAULT ('00000000-0000-0000-0000-000000000000') FOR [UploadedBy]
GO
