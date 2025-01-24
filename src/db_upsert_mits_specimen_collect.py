# upsert MITSSpecimensCollected table with data from the view vw_HIVMitsSpecimenCollect
# CreatedBy and UploadedBy is set to 'HIV_PROJECT_ETL'
import sqlalchemy as sa
from src.logging_config import logger
from config.config import CONN, MITS_SPECIMEN_COLLECT_VIEW_NAME, DB_SCHEMA as SCHEMA_NAME

def upsert_mits_specimen_collect() -> None:
    logger.info('Starting upsert_mits_specimen_collect')
    try:
        # merge MITSSpecimensCollected table with data from the view vw_HIVMitsSpecimenCollect
        merge_sql = sa.text(f""" 
        MERGE INTO dbo.MITSSpecimensCollected AS Target
        USING {SCHEMA_NAME}.{MITS_SPECIMEN_COLLECT_VIEW_NAME} AS Source
        ON (
            Target.ChampsId = Source.ChampsId
            AND Target.SiteId = Source.SiteId
            AND Target.FileName = 'adult_hiv_study'
            AND Target.Active = 1
        )
        WHEN MATCHED THEN
            UPDATE SET 
                Target.SiteId = Source.SiteId,
                Target.KitId = Source.KitId,
                Target.CollectionDate = Source.CollectionDate,
                Target.MITSCollect = Source.MITSCollect,
                Target.ModifiedOn = Source.ModifiedOn,
                Target.ModifiedBy = Source.ModifiedBy,
                Target.UploadedOn = Source.UploadedOn,
                Target.UploadedBy = Source.UploadedBy
        WHEN NOT MATCHED THEN
        INSERT (
            Id, SiteId, ChampsId, KitId, CollectionDate, 
            MITSCollect, FileName, Active, CreatedOn, 
            ModifiedOn, UploadedOn, CreatedBy, ModifiedBy, UploadedBy
        )
        VALUES (
            Source.Id, Source.SiteId, Source.ChampsId, Source.KitId,
            Source.CollectionDate, Source.MITSCollect, Source.FileName,
            Source.Active, Source.CreatedOn, Source.ModifiedOn,
            Source.UploadedOn, Source.CreatedBy, Source.ModifiedBy,
            Source.UploadedBy
            );
        """)
        # print(merge_sql)
        # deactivate any record not found in source MITS_SPECIMEN_COLLECT_VIEW_NAME 
        # but are in the MITSSpecimenCollection table
        # Set Active = 2 
        deactivate_deleted_sql = sa.text(f"""
            update MITSSpecimensCollected set Active = 2 , 
                                        ModifiedOn = getdate(),
                                        ModifiedBy = 'HIV_PROJECT_ETL'
            where FileName = 'adult_hiv_study'
            and Active = 1
            and not exists (select 1 from {SCHEMA_NAME}.{MITS_SPECIMEN_COLLECT_VIEW_NAME} source 
                where source.ChampsId = MITSSpecimensCollected.ChampsId
                and source.FileName = MITSSpecimensCollected.FileName
                and source.Active = 1
            ) ;
            """)
        with CONN.connect() as conn:
            result = conn.execute(merge_sql)
            result_deactivate_deleted = conn.execute(deactivate_deleted_sql)
            conn.commit()
            logger.info(f"Merged {result.rowcount} rows into MITSSpecimensCollected")
            logger.info(f"Deactivated {result_deactivate_deleted.rowcount} rows not found in source")
        logger.info('Finished upsert_mits_specimen_collect')
    except Exception as e:
        print(f"Error in upsert_mits_specimen_collect.py: {e}")
        logger.error(f"Error in upsert_mits_specimen_collect.py: {e}")