# db_load_project_1_1/py
import duckdb
import pandas as pd
import sqlalchemy as sa
from config.config import CONN, DB_SCHEMA ,REDCAP_DATA_DICT_FILE_11, REDCAP_DATA_DICT_APPEND_FILE_11, DATA_DICT_TABLE_11, DATA_TABLE_11
from src.create_data_dict_df import create_data_dict_df
from src.logging_config import logger
# df = pd.read_csv('data/redcap_hiv_project1_1.csv')


def transform_project_1_1(df: pd.DataFrame) -> pd.DataFrame:
    df = df.astype(str)
    conn = duckdb.connect()
    conn.execute(" CREATE TABLE redcap_hiv_project1_1 AS SELECT * FROM df ")
    conn.execute(" COPY redcap_hiv_project1_1 TO 'data/redcap_hiv_project1_1.parquet' (FORMAT 'parquet') ")
    conn.execute(f"""CREATE or REPLACE table redcap_hiv_project1_1 as
                    select record,field_name,value 
                    FROM read_parquet('data/redcap_hiv_project1_1.parquet')
                """)
    
    # extract key fields site_id, catchment_id and champs_id from the exported data
    df_site = conn.execute(""" WITH site_cte as (
                                    SELECT record,
                                    MAX(CASE WHEN field_name = 'champs_id' THEN value END) AS champs_id,
                                    MAX(CASE WHEN field_name = 'site_id' THEN value END) AS site_id
                                    ,max(case when field_name like 'catchment_id%' THEN value END) AS catchment_id
                                    FROM redcap_hiv_project1_1
                                    WHERE (field_name in ('champs_id', 'site_id' ) or field_name like 'catchment_id%')
                                    GROUP BY record 
                                )
                                SELECT p.*, site_cte.site_id, site_cte.catchment_id, site_cte.champs_id 
                                from redcap_hiv_project1_1 p
                                join site_cte on p.record = site_cte.record 
                            """).fetch_df()
    #  write to csv for testing
    df_site.to_csv('data/redcap_project1_1.csv', index=False)
    return df_site

def db_load_project_1_1(df: pd.DataFrame) -> pd.DataFrame:
    logger.info('Starting db_load_project_1_1.py')
    try:
        df = transform_project_1_1(df).fillna('')
        engine = CONN
        with engine.connect() as conn:
            # data dictionary table
            data_dict_df = create_data_dict_df(REDCAP_DATA_DICT_FILE_11, REDCAP_DATA_DICT_APPEND_FILE_11)
            truncate_stg = sa.text(f"TRUNCATE TABLE stg.{DATA_DICT_TABLE_11}")
            conn.execute(truncate_stg)
            data_dict_df.to_sql(DATA_DICT_TABLE_11, conn, schema=DB_SCHEMA, if_exists='append', index=False) if not data_dict_df.empty else None
            
            # 1.1 stg data table
            df = df.rename(columns={'record': 'ReportId','site_id':'SiteId', 'catchment_id': 'CatchmentId'  ,'champs_id': 'ChampsId' , 
                                    'field_name': 'FieldName', 'value': 'FieldValue'})
            # print(df.keys())
            df = df.astype({'SiteId': str,'CatchmentId': str, 'ReportId': str, 'ChampsId':str ,'FieldName': str, 'FieldValue': str}) 
            df = df[['SiteId','CatchmentId', 'ReportId', 'ChampsId', 'FieldName', 'FieldValue']]
            # df.to_csv('data/redcap_hiv_project1_1_db_temp.csv', index=False)
            # print("df data type",df.dtypes)
            # TODO: add a warning that catchment_id are missing in the data
            # truncate table
            truncate_stg_table = sa.text(f"TRUNCATE TABLE stg.{DATA_TABLE_11}")
            conn.execute(truncate_stg_table)
            df.to_sql(DATA_TABLE_11, conn, schema='stg', if_exists='append', index=False)
            
            conn.commit()
            logger.info(f'Finished db_load_project_1_1.py. Loaded Project 1.1 data to {DATA_TABLE_11} table. ')
    except Exception as e:
        logger.error(f'Error in db_load_project_1_1.py: {e}')
        raise e
    return df