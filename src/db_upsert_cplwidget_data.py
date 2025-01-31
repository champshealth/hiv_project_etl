# merge into CPLWidgetAggregateand CPLWidgetDetailAggregate table using 
# vw_HIVCPLWidgetAggregate view
import sqlalchemy as sa
from src.logging_config import logger
from config.config import CONN,CPL_WIDGET_VIEW_NAME,  DB_SCHEMA as SCHEMA_NAME


import sqlalchemy as sa
def upsert_cpl_widget_aggregate() -> None:
    logger.info('Starting upsert_cpl_widget_aggregate')
    try:
        merge_sql = sa.text(f"""
        MERGE INTO dbo.CPLWidgetAggregate AS Target
        USING {SCHEMA_NAME}.{CPL_WIDGET_VIEW_NAME} AS Source
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
                target.ReportId = source.ReportId,
                target.CatchmentId = source.CatchmentId
        when not matched then
            insert (Id, ChampsId, DateOfDeathNotification, DaysSinceDeathNotification, SiteName, SiteGuid, 
                    ReportId, CatchmentId)
            values (newid(), source.ChampsId, source.DateOfDeathNotification, source.DaysSinceDeathNotification, source.SiteName, source.SiteGuid, 
                    source.ReportId, source.CatchmentId)
            ;
        """)
        # # print(merge_sql)
        # # deactivate any record not found in source CPL_WIDGET_AGGREGATE_VIEW_NAME 
        # # but are in the CPLWidgetAggregate table
        # # Set Active = 2 
        # deactivate_deleted_sql = sa.text(f"""
        #     update CPLWidgetAggregate set Active = 2 , 
        #     where FileName = 'adult_hiv_study'
        #     and Active = 1
        #     and not exists (select 1 from {SCHEMA_NAME}.vw_HIVCPLWidgetAggregate source 
        #         where source.ChampsId = CPLWidgetAggregate.ChampsId
        #         and source.FileName = CPLWidgetAggregate.FileName
        #         and source.Active = 1
        #     ) ;
        #     """)
        merge_cpl_detail_sql = sa.text(f"""
                merge into CPLDetailWidgetAggregate as target
                using stg.vw_HIVCPLWidgetAggregate as source
                on target.ChampsId = source.ChampsId
                when matched then
                    update set
                        target.DateOfDeathNotification = source.DateOfDeathNotification,
                        target.DaysSinceDeathNotification = source.DaysSinceDeathNotification,
                        target.SiteName = source.SiteName,
                        target.SiteGuid = source.SiteGuid,
                        target.DemographicsModifiedOn = source.DemographicsModifiedOn,
                        target.ChildAbstractionModifiedOn = source.ChildAbstractionModifiedOn,
                        target.SitePathDiagModifiedOn = source.SitePathDiagModifiedOn,
                        target.SitePathFindingModifiedOn = source.SitePathFindingModifiedOn,
                        target.SitePathTissueModifiedOn = source.SitePathTissueModifiedOn,
                        target.LaboratoryResultsModifiedOn = source.LaboratoryResultsModifiedOn,
                        target.PlacentaExaminationModifiedOn = source.PlacentaExaminationModifiedOn,
                        target.ReportId = source.ReportId,
                        target.CatchmentId = source.CatchmentId
                when not matched then
                    insert (Id, ChampsId, SiteId, DateOfDeathNotification, DaysSinceDeathNotification, SiteName, SiteGuid, DemographicsModifiedOn, 
                            ChildAbstractionModifiedOn, SitePathDiagModifiedOn, SitePathFindingModifiedOn, SitePathTissueModifiedOn, LaboratoryResultsModifiedOn
                            ,PlacentaExaminationModifiedOn, ReportId, CatchmentId)
                    values (newid(), source.ChampsId, source.SiteGuid, source.DateOfDeathNotification, source.DaysSinceDeathNotification, source.SiteName, source.SiteGuid, 
                            source.DemographicsModifiedOn, source.ChildAbstractionModifiedOn, source.SitePathDiagModifiedOn, source.SitePathFindingModifiedOn, 
                            source.SitePathTissueModifiedOn, source.LaboratoryResultsModifiedOn, source.PlacentaExaminationModifiedOn,
                            source.ReportId, source.CatchmentId)
            ;
        """)


        with CONN.connect() as conn:
            result = conn.execute(merge_sql)
            result_detail = conn.execute(merge_cpl_detail_sql)
            # result_deactivate_deleted = conn.execute(deactivate_deleted_sql)
            conn.commit()
            logger.info(f"Merged {result.rowcount} rows into CPLWidgetAggregate")
            logger.info(f"Merged {result_detail.rowcount} rows into CPLDetailWidgetAggregate")
        logger.info('Finished upsert_cpl_widget_aggregate')
    except Exception as e:
        print(f"Error in upsert_cpl_widget_aggregate.py: {e}")
        logger.error(f"Error in upsert_cpl_widget_aggregate.py: {e}")
        raise e