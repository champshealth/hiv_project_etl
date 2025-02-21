from config.config import REDCAP_API_TOKEN_11, REDCAP_EXPORT_FILE_11, REDCAP_API_TOKEN_31,  REDCAP_EXPORT_FILE_31, REDCAP_API_TOKEN_CA, REDCAP_EXPORT_FILE_CA
from src.redcap_api_export import redcap_api_export
from src.logging_config import logger
from src.db_load_project_1_1 import db_load_project_1_1
from src.db_load_project_3_1 import db_load_project_3_1
from src.db_upsert_consent_data import upsert_consent_records
from src.db_upsert_mits_proc_data import upsert_mits_proc_data
from src.db_upsert_death_notif_data import upsert_death_notif_data
from src.db_upsert_mits_specimen_collect import upsert_mits_specimen_collect
from src.db_load_abstraction import db_load_clinical_abstraction
from src.db_upsert_cplwidget_data import upsert_cpl_widget_aggregate

if __name__ == '__main__':
    logger.info('Starting main script')
    try:
        logger.info('Starting redcap_api_export.py')
        df = redcap_api_export([REDCAP_API_TOKEN_11], REDCAP_EXPORT_FILE_11)
        logger.info('Finished redcap_api_export.py')
        if not df.empty:
            df2 = db_load_project_1_1(df=df)
            upsert_consent_records()
            upsert_death_notif_data()
            del df

            # # 3.1 data load and upsert
            df = redcap_api_export([REDCAP_API_TOKEN_31], REDCAP_EXPORT_FILE_31)
            db_load_project_3_1(df=df)
            upsert_mits_proc_data()
            upsert_mits_specimen_collect()

            # # clinical abstraction data load
            df = redcap_api_export([REDCAP_API_TOKEN_CA], REDCAP_EXPORT_FILE_CA)
            db_load_clinical_abstraction(df=df)

            # CPL Widget upsert
            upsert_cpl_widget_aggregate()
            
        logger.info('Finished main script')
    except Exception as e:
        logger.error(f'ERROR: {e}')
        raise e

