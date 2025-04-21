# use view stg.vw_HIVDeathNotificationto upsert into DeathNotification table
import pandas as pd
import sqlalchemy as sa
from src.logging_config import logger
from config.config import CONN, HIV_DEATH_NOTIFICATION_VIEW, DB_SCHEMA as SCHEMA_NAME, ETL_USER_ID

def upsert_death_notif_data() -> None:
    logger.info('Starting upsert_death_notif_data')
    try:
        merge_sql = sa.text(f"""
        MERGE into [dbo].[DeathNotification] as Target
        using {SCHEMA_NAME}.{HIV_DEATH_NOTIFICATION_VIEW} as Source
                        on (
                            Target.SiteId = Source.SiteId
                            and Target.ReportId = Source.ReportId 
                            and Target.CatchmentId = Source.CatchmentId
                            and Target.[FileName] = Source.[FileName]
                            and Target.FileName = 'adult_hiv_study'
                            and Target.Active=1 )
        when matched AND (Target.DateOfDeathNotification != Source.DateOfDeathNotification ) 
        then
            update set Target.DateOfDeathNotification = Source.DateOfDeathNotification,
                        Target.ModifiedOn = Source.ModifiedOn,
                        Target.UploadedOn = Source.UploadedOn,
                        Target.ModifiedBy = '{ETL_USER_ID}'
        when not matched then
            insert (Id, DeathNotificationSiteId, ReportId, CatchmentId, DateOfDeathNotification, 
                        SiteId, [FileName], CreatedOn, ModifiedOn, UploadedOn, Active, CreatedBy, UploadedBy)
            values (Source.Id, Source.DeathNotificationSiteId, Source.ReportId, Source.CatchmentId, Source.DateOfDeathNotification, 
                        Source.SiteId, Source.FileName, Source.CreatedOn, Source.ModifiedOn, Source.UploadedOn, Source.Active,
                        '{ETL_USER_ID}', '{ETL_USER_ID}')  
                        ;
        """)
    
        #  Deactivate duplicate records based on SiteId, ReportId, CatchmentId
        #  set duplicate records to inactive (Active = 0) 
        deactivate_dups_sql = sa.text(""" 
                update DeathNotification set Active = 0 
                where FileName = 'adult_hiv_study' 
                and Id in 
                (   SELECT Id from
                        (  SELECT Id, ReportId CatchmentId
                            , ROW_NUMBER() over (partition by SiteId, ReportId, CatchmentId order by CreatedOn desc) as RowNumber_dup 
                            from DeathNotification  
                            where FileName = 'adult_hiv_study' 
                            and Active = 1) dup
                    where RowNumber_dup > 1
                        ) ;               
                """)

        #  DEactivate any records not found in source stg.vw_HIVDeathNotification
        # based on the FileName = 'adult_hiv_study' and SiteId, ReportId, CatchmentId
        # set Active = 2
        deactivate_deleted_sql = sa.text(f"""
                update DeathNotification set Active = 2 , ModifiedOn = getdate() 
                where FileName = 'adult_hiv_study' 
                and Active = 1
                and not exists 
                    ( select 1 from {SCHEMA_NAME}.{HIV_DEATH_NOTIFICATION_VIEW} as Source 
                        where Source.ReportId = DeathNotification.ReportId 
                        and Source.CatchmentId = DeathNotification.CatchmentId
                        and Source.FileName = DeathNotification.FileName
                        and Source.SiteId = DeathNotification.SiteId
                    );
                """)
        
        with CONN.connect() as conn:
            result = conn.execute(merge_sql)
            result_deactivate= conn.execute(deactivate_dups_sql)
            result_deactivate_deleted = conn.execute(deactivate_deleted_sql)
            conn.commit()

            logger.info(f"Merged  {result.rowcount} rows into DeathNotification table ")
            logger.info (f"Deactivated {result_deactivate.rowcount} duplicate rows.") 
            logger.info( f"Deactivated {result_deactivate_deleted.rowcount} rows not found in source")
    except Exception as e:
        print(f"Error in upsert_death_notif_data.py: {e}")
        logger.error(f"Error in upsert_death_notif_data.py: {e}")
