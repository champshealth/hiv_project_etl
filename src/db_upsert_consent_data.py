# Insert consents in consentTtracking table
# adult_hiv_study
# 1. Merge the data from the view vw_HIVConsentTracking to the ConsentTracking table
import sqlalchemy as sa
from config.config import CONN, CONSENTTRACK_VIEW_NAME, DB_SCHEMA as SCHEMA_NAME
from src.logging_config import logger

# engine = connect_db.conn_qa
def upsert_consent_records():
    try:
        logger.info('Starting upsert_consent_records.py')
        MERGE_SQL = sa.text (f""" MERGE into [dbo].[ConsentTracking] as Target
            using {SCHEMA_NAME}.{CONSENTTRACK_VIEW_NAME} as Source
            on (
                Target.ReportId = Source.ReportId 
                and Target.CatchmentId = Source.CatchmentId
                and  Target.ChampsId = Source.ChampsId 
                and Target.SiteId = Source.SiteId 
                and Target.[FileName] = Source.[FileName]
                and Target.Active=1 ) 
            when matched then
                update set Target.CatchmentId = Source.CatchmentId,
                        Target.ConsentGranted = Source.ConsentGranted,
                        Target.ConsentType = Source.ConsentType,
                        Target.ConsentDate = Source.ConsentDate,
                        Target.ModifiedOn = Source.CreatedOn,
                        Target.UploadedOn = Source.CreatedOn
            when not matched then
                insert (Id, ConsentTrackingSiteId, ReportId, CatchmentId, ChampsId, ConsentGranted, ConsentType, ConsentDate, SiteId, [FileName], CreatedOn, ModifiedOn, Uploadedon, Active)
                values (Source.Id, Source.ConsentTrackingSiteId, Source.ReportId, Source.CatchmentId, Source.ChampsId, Source.ConsentGranted, 
                Source.ConsentType, Source.ConsentDate, Source.SiteId, Source.FileName, Source.CreatedOn, Source.CreatedOn, Source.CreatedOn, Source.Active)
            ; 
        """)
        # ConsentTracking set duplicate records to inactive
        DEACTIVATE_DUPS_SQL= sa.text("""
                update [ConsentTracking] set Active = 0 
                where FileName = 'adult_hiv_study' 
                and Id in 
                    ( select Id from 
                        (select Id, SiteId, ChampsId,FileName, CatchmentId, createdon, ModifiedOn, UploadedOn, Active, 
                        ROW_NUMBER() over (partition by ChampsId order by CreatedOn desc) as RowNumber_dup 
                        from ConsentTracking  
                        where FileName = 'adult_hiv_study' 
                        and Active = 1) as dup 
                        where RowNumber_dup > 1 
                        ) ;
            """
        )

        # deactivate any record not found in source CONSENTTRACK_VIEW_NAME 
        # on the basis of ChampsId, SiteId, FileName, Active = 1
        #  set active = 2
        DEACTIVATE_DELETED_SQL = sa.text(f""" 
                                        update [ConsentTracking] set Active = 2 , ModifiedOn = getdate()
                                        where FileName = 'adult_hiv_study'
                                        and Active = 1
                                        and not exists (select 1 from {SCHEMA_NAME}.{CONSENTTRACK_VIEW_NAME} source 
                                            where source.ChampsId = ConsentTracking.ChampsId
                                            and source.SiteId = ConsentTracking.SiteId
                                            and source.[FileName] = ConsentTracking.[FileName]
                                            and source.Active = 1
                                        ) ;
                                        """)
                                        
        #  execute the merge statement
        with CONN.connect() as conn:
            result = conn.execute(MERGE_SQL)
            result_deactivate= conn.execute(DEACTIVATE_DUPS_SQL)
            result_deactivate_deleted = conn.execute(DEACTIVATE_DELETED_SQL)
            conn.commit()
            logger.info(f"Merged {result.rowcount} rows into {CONSENTTRACK_VIEW_NAME}, Deactivated {result_deactivate.rowcount} duplicate rows, Deactivated {result_deactivate_deleted.rowcount} rows not found in source")
        
        logger.info('Finished upsert_consent_records.py')

    except Exception as e:
        print(f"Error in upsert_consent_records.py: {e}")
        raise e