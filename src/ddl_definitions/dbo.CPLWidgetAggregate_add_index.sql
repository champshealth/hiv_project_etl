-- DDL: Add missing index on dbo.CPLWidgetAggregate for MERGE join key (ChampsId, SiteGuid)
-- Run once in production by DBA.
-- Matches the MERGE ON clause in upsert_cpl_widget_aggregate:
--   ON Target.ChampsId = Source.ChampsId AND Target.SiteGuid = Source.SiteGuid

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID('dbo.CPLWidgetAggregate')
      AND name = 'IX_CPLWidgetAggregate_ChampsId_SiteGuid'
)
BEGIN
    CREATE NONCLUSTERED INDEX [IX_CPLWidgetAggregate_ChampsId_SiteGuid]
    ON [dbo].[CPLWidgetAggregate] ([ChampsId] ASC, [SiteGuid] ASC)
    WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF,
          DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON,
          ALLOW_PAGE_LOCKS = ON, FILLFACTOR = 80) ON [PRIMARY];

    PRINT 'Index IX_CPLWidgetAggregate_ChampsId_SiteGuid created successfully.';
END
ELSE
BEGIN
    PRINT 'Index IX_CPLWidgetAggregate_ChampsId_SiteGuid already exists. No action taken.';
END
GO
