# This script upserts MITSPRocedure Table for Adult HIV Study using a MERGE SQL statement
# The MERGE SQL statement compares the MITSProcedure Table with the vw_HIVMitsProcedure view
# CreatedBy and UploadedBy is set to 'HIV_PROJECT_ETL'

import sqlalchemy as sa
from src.logging_config import logger
from config.config import CONN, MITS_PROCEDURE_VIEW_NAME, DB_SCHEMA as SCHEMA_NAME

def upsert_mits_proc_data() -> None:
    logger.info('Starting upsert_mits_proc_data')
    try:
        merge_sql = sa.text(f""" 
        MERGE INTO dbo.MITSProcedure AS Target
        USING {SCHEMA_NAME}.{MITS_PROCEDURE_VIEW_NAME} AS Source
        ON (
            Target.ChampsId = Source.ChampsId
            AND Target.FileName = Source.FileName
            and Target.Filename = 'adult_hiv_study'
            AND Target.Active = 1
        )
        WHEN MATCHED THEN
            UPDATE SET 
                Target.MITSPerformed = Source.MITSPerformed,
                Target.SpecimenKitId = Source.SpecimenKitId,
                Target.DateBodyReceived = Source.DateBodyReceived,
                Target.MITSLocation = Source.MITSLocation,
                Target.DateProcedureStarted = Source.DateProcedureStarted,
                Target.TimeProcedureStarted = Source.TimeProcedureStarted,
                Target.TimeProcedureCompleted = Source.TimeProcedureCompleted,
                Target.SexOfDeceased = Source.SexOfDeceased,
                Target.ModifiedOn = Source.ModifiedOn,
                Target.UploadedOn = Source.UploadedOn
        WHEN NOT MATCHED THEN
            INSERT (
                Id, SiteId, ChampsId, MITSPerformed, SpecimenKitId, DateBodyReceived,
                MITSLocation, DateProcedureStarted, TimeProcedureStarted, 
                TimeProcedureCompleted, SexOfDeceased, FileName,
                Active, CreatedOn, ModifiedOn, UploadedOn, CreatedBy, UploadedBy
            )
            VALUES (
                Source.Id,Source.SiteId, Source.ChampsId, Source.MITSPerformed, Source.SpecimenKitId,
                Source.DateBodyReceived, Source.MITSLocation, Source.DateProcedureStarted,
                Source.TimeProcedureStarted, Source.TimeProcedureCompleted,
                Source.SexOfDeceased, Source.FileName, Source.Active,
                Source.CreatedOn, Source.ModifiedOn, Source.UploadedOn, 'HIV_PROJECT_ETL', 'HIV_PROJECT_ETL'
            )
        ;
        """)
        # print(merge_sql)
        # deactivate any record not found in source MITS_PROCEDURE_VIEW_NAME but are in the MITSProcedure table
        # Set Active = 2 
        deactivate_deleted_sql = sa.text(f"""
            update MITSProcedure set Active = 2 , ModifiedOn = getdate()
            where FileName = 'adult_hiv_study'
            and Active = 1
            and not exists (select 1 from {SCHEMA_NAME}.{MITS_PROCEDURE_VIEW_NAME} source 
                where source.ChampsId = MITSProcedure.ChampsId
                and source.FileName = MITSProcedure.FileName
                and source.Active = 1
            ) ;
            """)

        # Assumption duplicate CHampsId , FIlename are not possible since HIV study 
        # ChampsId prefix are different from perdiatrics cases
    
        with CONN.connect() as conn:
            result = conn.execute(merge_sql)
            result_deactivate_deleted = conn.execute(deactivate_deleted_sql)
            conn.commit()
            logger.info(f"Merged {result.rowcount} rows into MITSProcedure")
            logger.info(f"Deactivated {result_deactivate_deleted.rowcount} rows not found in source")
        logger.info('Finished upsert_mits_proc_data')

    except Exception as e:
        print(f"Error in upsert_mits_proc_data.py: {e}")
        logger.error(f"Error in upsert_mits_proc_data.py: {e}")

    