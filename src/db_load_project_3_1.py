import pandas as pd
import sqlalchemy as sa
from src.create_data_dict_df import create_data_dict_df
from src.logging_config import logger
from config.config import CONN, DB_SCHEMA ,REDCAP_DATA_DICT_FILE_31, REDCAP_DATA_DICT_APPEND_FILE_31, DATA_DICT_TABLE_31, DATA_TABLE_31
# from ci_utils import connect_db

# CSV_FILE_NAME = 'data/redcap_hiv_3_1.csv'
# STG_TABLE_NAME = 'HIVProject3_1_stg'
# df = pd.read_csv(CSV_FILE_NAME, dtype=str, na_filter=False)
# DATA_DICT_FILE_NAME = 'data/AdultHIVProject3_1_DataDict_2024-11-07.csv'
# DATA_DICT_APPEND_FILE_NAME = 'data/AdultHIVProject3_1_DataDict_append.csv'

def db_load_project_3_1(df: pd.DataFrame = None) -> None:
    logger.info('Starting db_load_project_3_1')
    if df is None or df.empty:
        logger.info('No 3.1 data to load')
        return
    try:
        engine = CONN
        with engine.connect() as conn:
            #  use function create_data_dict_df to create data dictionary file
            data_dict_df = create_data_dict_df(REDCAP_DATA_DICT_FILE_31, REDCAP_DATA_DICT_APPEND_FILE_31)

            # truncate the data dictionary table
            truncate_data_dict = sa.text(f"TRUNCATE TABLE {DB_SCHEMA}.{DATA_DICT_TABLE_31}")
            conn.execute(truncate_data_dict)
            data_dict_df.to_sql(DATA_DICT_TABLE_31, conn, schema=DB_SCHEMA, if_exists='append', index=False) if not data_dict_df.empty else None

            # rename df columns to match the staging table columns names
            df.columns = df.rename(columns= {'record': 'ChampsId','redcap_repeat_instrument': 'RepeatInstrument',
                                            'redcap_repeat_instance': 'RepeatInstance', 
                                            'field_name': 'FieldName', 'value': 'FieldValue'}).columns

            #  truncate the 3.1 staging table
            truncate_stg = sa.text(f"TRUNCATE TABLE {DB_SCHEMA}.{DATA_TABLE_31}")
            conn.execute(truncate_stg)

            df.to_sql(DATA_TABLE_31, conn, schema=DB_SCHEMA, if_exists='append', index=False)
            logger.info(f'Finished db_load_project_3_1. Loaded Project 3.1 data to {DATA_TABLE_31} table.')
            conn.commit()

    except Exception as e:
        logger.error(f'Error in db_load_project_3_1.py: {e}')
        raise e