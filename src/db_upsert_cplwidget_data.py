# merge into CPLWidgetAggregateand CPLWidgetDetailAggregate table using 
# vw_HIVCPLWidgetAggregate view
import sqlalchemy as sa
from src.logging_config import logger
from config.config import CONN,CPL_WIDGET_VIEW_NAME,  DB_SCHEMA as SCHEMA_NAME
import sqlalchemy as sa

def upsert_cpl_widget_aggregate(conn_override: sa.engine.Engine = None) -> None:
    """Upsert CPLWidgetAggregate and CPLDetailWidgetAggregate from the CPL widget source view.

    Optimizations applied:
    - Source view is materialized into a session-scoped #tmp table once per transaction
      to avoid re-evaluating the expensive multi-join view twice.
    - Each MERGE runs in its own connection + commit block to limit transaction log
      usage per operation rather than holding a single long-running transaction.

    Args:
        conn_override: Optional SQLAlchemy engine to use instead of the default CONN.
                       Useful for testing against non-production databases.
    """
    engine = conn_override if conn_override is not None else CONN
    logger.info('Starting upsert_cpl_widget_aggregate')
    try:
        materialize_sql = sa.text(f"""
            IF OBJECT_ID('tempdb..#tmp_cpl_source') IS NOT NULL
                DROP TABLE #tmp_cpl_source;
            SELECT * INTO #tmp_cpl_source
            FROM {SCHEMA_NAME}.{CPL_WIDGET_VIEW_NAME}
        """)

        merge_sql = sa.text("""
        MERGE INTO dbo.CPLWidgetAggregate AS Target
        USING #tmp_cpl_source AS Source
        ON (
            Target.ChampsId = Source.ChampsId
            AND Target.SiteGuid = Source.SiteGuid
        )
        WHEN MATCHED THEN
            UPDATE SET 
                target.DateOfDeathNotification = source.DateOfDeathNotification,
                target.DaysSinceDeathNotification = source.DaysSinceDeathNotification,
                target.SiteName = source.SiteName,
                target.SiteGuid = source.SiteGuid,
                target.SiteId = source.DeathNotificationSiteId,
                target.ReportId = source.ReportId,
                target.CatchmentId = source.CatchmentId
        WHEN NOT MATCHED THEN
            INSERT (Id, ChampsId, DateOfDeathNotification, DaysSinceDeathNotification, SiteName, SiteGuid, SiteId,
                    ReportId, CatchmentId)
            VALUES (newid(), source.ChampsId, source.DateOfDeathNotification, source.DaysSinceDeathNotification, source.SiteName, source.SiteGuid, 
                    source.DeathNotificationSiteId,
                    source.ReportId, source.CatchmentId)
            ;
        """)

        merge_cpl_detail_sql = sa.text("""
                MERGE INTO dbo.CPLDetailWidgetAggregate AS target
                USING #tmp_cpl_source AS source
                ON target.ChampsId = source.ChampsId
                WHEN MATCHED THEN
                    UPDATE SET
                        target.DateOfDeathNotification = source.DateOfDeathNotification,
                        target.DaysSinceDeathNotification = source.DaysSinceDeathNotification,
                        target.SiteId = source.DeathNotificationSiteId,
                        target.SiteName = source.SiteName,
                        target.SiteGuid = source.SiteGuid,
                        target.DemographicsModifiedOn = source.DemographicsModifiedOn,
                        target.MITSProcedureModifiedOn = source.MITSProcedureModifiedOn,
                        target.ChildAbstractionModifiedOn = source.ChildAbstractionModifiedOn,
                        target.SitePathDiagModifiedOn = source.SitePathDiagModifiedOn,
                        target.SitePathFindingModifiedOn = source.SitePathFindingModifiedOn,
                        target.SitePathTissueModifiedOn = source.SitePathTissueModifiedOn,
                        target.LaboratoryResultsModifiedOn = source.LaboratoryResultsModifiedOn,
                        target.PlacentaExaminationModifiedOn = source.PlacentaExaminationModifiedOn,
                        target.ReportId = source.ReportId,
                        target.CatchmentId = source.CatchmentId
                WHEN NOT MATCHED THEN
                    INSERT (Id, ChampsId, SiteId, DateOfDeathNotification, DaysSinceDeathNotification, SiteName, SiteGuid, DemographicsModifiedOn, 
                            ChildAbstractionModifiedOn, MITSProcedureModifiedOn, SitePathDiagModifiedOn, SitePathFindingModifiedOn, SitePathTissueModifiedOn, LaboratoryResultsModifiedOn
                            ,PlacentaExaminationModifiedOn, ReportId, CatchmentId)
                    VALUES (newid(), source.ChampsId, source.DeathNotificationSiteId , source.DateOfDeathNotification, source.DaysSinceDeathNotification, source.SiteName, source.SiteGuid, 
                            source.DemographicsModifiedOn, source.ChildAbstractionModifiedOn, source.MITSProcedureModifiedOn, source.SitePathDiagModifiedOn, source.SitePathFindingModifiedOn, 
                            source.SitePathTissueModifiedOn, source.LaboratoryResultsModifiedOn, source.PlacentaExaminationModifiedOn,
                            source.ReportId, source.CatchmentId)
            ;
        """)

        #  upsert CaseStatus table using CPLWidgetAggregate table data

        merge_case_status_sql = sa.text(f""" 
                merge into dbo.CaseStatus as target
                using (select cdw.Id, s.SiteId, 'adult_hiv_study' FileName, cdw.ChampsId, cdw.ConsentType
                        from CPLWidgetAggregate as cdw
                        join CatchmentArea cs on cdw.SiteGuid = cs.SiteId 
                                and cdw.CatchmentId = cs.CatchmentAreaId 
                                and cs.Description like 'Adult HIV MITS Catchment'
                        join Site s on cs.SiteId = s.Id
                        ) as source
                on target.ChampsId = source.ChampsId
                when matched  and StatusText = 'Pending' then
                    update set
                        target.SiteId = source.SiteId,
                        target.FileName = 'adult_hiv_study',
                        target.UploadedOn = GETDATE(),
                        target.UploadedBy = 'HIV_PROJECT_ETL',
                        target.ModifiedOn = GETDATE(),
                        target.ModifiedBy = 'HIV_PROJECT_ETL'
                when not matched then
                    insert (Id, JobId, ProcessId, SiteId, FileName, ChampsId, 
                            CreatedOn, CreatedBy, UploadedOn, UploadedBy, ModifiedOn, ModifiedBy, Active, Valid,  ConsentType, Status, StatusText)
                    values (newid(), 'HIV_PROJECT_ETL', 'HIV_PROJECT_ETL', source.SiteId, 'adult_hiv_study', source.ChampsId, 
                            GETDATE(), 'HIV_PROJECT_ETL', GETDATE(), 'HIV_PROJECT_ETL', GETDATE(), 'HIV_PROJECT_ETL', 1, 1, source.ConsentType,1, 'Pending')
                    ;
        """)

        # Transaction 1: materialize source view once, then merge into CPLWidgetAggregate
        with engine.connect() as conn:
            conn.execute(materialize_sql)
            result = conn.execute(merge_sql)
            conn.commit()
            logger.info(f"Merged {result.rowcount} rows into CPLWidgetAggregate")

        # Transaction 2: re-materialize source view (new session), then merge into CPLDetailWidgetAggregate
        with engine.connect() as conn:
            conn.execute(materialize_sql)
            result_detail = conn.execute(merge_cpl_detail_sql)
            # result_case_status = conn.execute(merge_case_status_sql)
            conn.commit()
            logger.info(f"Merged {result_detail.rowcount} rows into CPLDetailWidgetAggregate")
            # logger.info(f"Merged {result_case_status.rowcount} rows into CaseStatus")

        logger.info('Finished upsert_cpl_widget_aggregate')
    except Exception as e:
        print(f"Error in upsert_cpl_widget_aggregate.py: {e}")
        logger.error(f"Error in upsert_cpl_widget_aggregate.py: {e}")
        raise e