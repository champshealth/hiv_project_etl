import pandas as pd
import sqlalchemy as sa
from src.create_data_dict_df import create_data_dict_df
from src.logging_config import logger
from config.config import CONN, DB_SCHEMA ,REDCAP_DATA_DICT_FILE_CA, REDCAP_DATA_DICT_APPEND_FILE_CA, DATA_DICT_TABLE_CA, DATA_TABLE_CA

def db_load_clinical_abstraction(df: pd.DataFrame) -> None:
    logger.info('Starting db_load_clinical_abstraction')
    if df.empty:
        logger.info('No clinical abstraction data to load')
        return
    try:
        engine = CONN
        with engine.connect() as conn:
            #  use function create_data_dict_df to create data dictionary file
            data_dict_df = create_data_dict_df(REDCAP_DATA_DICT_FILE_CA, REDCAP_DATA_DICT_APPEND_FILE_CA)

            # truncate the data dictionary table
            truncate_data_dict = sa.text(f"TRUNCATE TABLE {DB_SCHEMA}.{DATA_DICT_TABLE_CA}")
            conn.execute(truncate_data_dict)
            data_dict_df.to_sql(DATA_DICT_TABLE_CA, conn, schema=DB_SCHEMA, if_exists='append', index=False) if not data_dict_df.empty else None

            # create df with unique record, field_name, and value columns where value == 'am1_country'
            # This will be used to create a new column called 'SiteId' in the original df 
            # The 'SiteId' column will contain the value of the 'value' column from the df_am1_country df for each record
            df_am1_country = df[(df['field_name'] == 'am1_country') & (df['value'] != '')][['record', 'value']]
            df_am1_country = df_am1_country.rename(columns={'value': 'SiteId'})
            # print(df_am1_country.head())

            # merge with original df
            df = df.merge(df_am1_country, on=['record'], how='left')

            # rename df columns to match the staging table columns names
            df = df.rename(columns={'record': 'ChampsId', 'field_name': 'FieldName', 'value': 'FieldValue'})
            df = df[['SiteId', 'ChampsId', 'FieldName', 'FieldValue']]

            # df.columns = df.rename(columns= {'record': 'ChampsId','redcap_repeat_instrument': 'RepeatInstrument',
            #                                 'redcap_repeat_instance': 'RepeatInstance', 
            #                                 'field_name': 'FieldName', 'value': 'FieldValue'}).columns

            #  truncate the clinical abstraction staging table
            truncate_stg = sa.text(f"TRUNCATE TABLE {DB_SCHEMA}.{DATA_TABLE_CA}")
            conn.execute(truncate_stg)

            df.to_sql(DATA_TABLE_CA, conn, schema=DB_SCHEMA, if_exists='append', index=False)
            logger.info(f'Finished db_load_clinical_abstraction. Loaded clinical abstraction data to {DATA_TABLE_CA} table.')

            rows_loaded = conn.execute(sa.text(f"SELECT COUNT(*) FROM {DB_SCHEMA}.{DATA_TABLE_CA}")).scalar()
            logger.info(f'Loaded {rows_loaded} rows into clinical abstraction staging table.')
            conn.commit()

    except Exception as e:
        logger.error(f'Error in db_load_clinical_abstraction.py: {e}')
        raise e