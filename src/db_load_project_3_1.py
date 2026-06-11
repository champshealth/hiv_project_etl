import pandas as pd
import sqlalchemy as sa
import gc
from src.create_data_dict_df import create_data_dict_df
from src.logging_config import logger
from config.config import CONN, DB_SCHEMA ,REDCAP_DATA_DICT_FILE_31, REDCAP_DATA_DICT_APPEND_FILE_31, DATA_DICT_TABLE_31, DATA_TABLE_31
import pyodbc
import concurrent.futures
import multiprocessing
# from ci_utils import connect_db

# CSV_FILE_NAME = 'data/redcap_hiv_3_1.csv'
# STG_TABLE_NAME = 'HIVProject3_1_stg'
# df = pd.read_csv(CSV_FILE_NAME, dtype=str, na_filter=False)
# DATA_DICT_FILE_NAME = 'data/AdultHIVProject3_1_DataDict_2024-11-07.csv'
# DATA_DICT_APPEND_FILE_NAME = 'data/AdultHIVProject3_1_DataDict_append.csv'

def db_load_project_3_1(df: pd.DataFrame = None, parquet_files: list = None) -> None:
    logger.info('Starting db_load_project_3_1')
    if (df is None or df.empty) and not parquet_files:
        logger.info('No 3.1 data to load')
        return
    try:
        engine = CONN
        with engine.connect() as conn:
            data_dict_df = create_data_dict_df(REDCAP_DATA_DICT_FILE_31, REDCAP_DATA_DICT_APPEND_FILE_31)

            truncate_data_dict = sa.text(f"TRUNCATE TABLE stg.{DATA_DICT_TABLE_31}")
            conn.execute(truncate_data_dict)

            if not data_dict_df.empty:
                data_dict_insert = data_dict_df.to_sql(DATA_DICT_TABLE_31, conn, schema='stg', if_exists='append', index=False)
                logger.info(f'Loaded {data_dict_insert} rows into Project 3.1 DATA DICTIONARY table: {DATA_DICT_TABLE_31}.')
            else:
                logger.info(f'No data dictionary rows to load for Project 3.1.')

            truncate_stg = sa.text(f"TRUNCATE TABLE stg.{DATA_TABLE_31}")
            conn.execute(truncate_stg)

            if parquet_files:
                total_rows = 0
                for pf in parquet_files:
                    chunk_df = pd.read_parquet(pf)
                    if chunk_df.empty:
                        continue
                    chunk_df.columns = chunk_df.rename(columns={
                        'record': 'ChampsId', 'redcap_repeat_instrument': 'RepeatInstrument',
                        'redcap_repeat_instance': 'RepeatInstance',
                        'field_name': 'FieldName', 'value': 'FieldValue'
                    }).columns
                    rows = fast_insert_with_executemany(conn, DATA_TABLE_31, 'stg', chunk_df, batch_size=1000)
                    total_rows += rows
                    logger.info(f'Loaded parquet file {pf}: {rows} rows')
                    del chunk_df
                    gc.collect()
                logger.info(f'Finished db_load_project_3_1. Loaded {total_rows} rows from {len(parquet_files)} files.')
            else:
                df.columns = df.rename(columns={
                    'record': 'ChampsId', 'redcap_repeat_instrument': 'RepeatInstrument',
                    'redcap_repeat_instance': 'RepeatInstance',
                    'field_name': 'FieldName', 'value': 'FieldValue'
                }).columns
                chunk_size = 1000
                total_rows = 0
                total_chunks = (len(df) + chunk_size - 1) // chunk_size
                logger.info(f'Loading data in {total_chunks} chunks of {chunk_size} rows each...')
                for i in range(0, len(df), chunk_size):
                    chunk_df = df[i:i+chunk_size]
                    rows_added = fast_insert_with_executemany(conn, DATA_TABLE_31, 'stg', chunk_df, batch_size=chunk_size)
                    total_rows += rows_added
                    logger.info(f'Loaded chunk {(i//chunk_size)+1}/{total_chunks} with {rows_added} rows.')
                logger.info(f'Finished db_load_project_3_1. Loaded {total_rows} rows into Project 3.1 data table: {DATA_TABLE_31}.')

    except Exception as e:
        logger.error(f'Error in db_load_project_3_1.py: {e}')
        raise e

def fast_insert_with_executemany(conn, table_name, schema, dataframe, batch_size=1000):
    """
    Optimized function to insert data using executemany with pyodbc
    
    Args:
        conn: SQLAlchemy connection
        table_name: Target table name
        schema: Target schema name
        dataframe: Pandas DataFrame to insert
        batch_size: Number of rows per batch
        
    Returns:
        Total number of rows inserted
    """
    # Get the raw DBAPI connection
    raw_conn = conn.connection
    
    # Create column list for the INSERT statement
    columns = list(dataframe.columns)
    column_str = ', '.join([f"[{col}]" for col in columns])
    
    # Create parameterized query with placeholders
    placeholder_str = ', '.join(['?' for _ in columns])
    insert_stmt = f"INSERT INTO {schema}.{table_name} ({column_str}) VALUES ({placeholder_str})"
    
    # Convert DataFrame to list of tuples for executemany
    # Ensure all data is properly converted to strings if they're mixed types
    dataframe = dataframe.astype(str)
    data = [tuple(row) for row in dataframe.values]
    
    # Execute in batches
    total_rows = 0
    cursor = raw_conn.cursor()
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        try:
            cursor.fast_executemany = True  # Enable fast_executemany for better performance
            cursor.executemany(insert_stmt, batch)
            rows_in_batch = len(batch)
            total_rows += rows_in_batch
            logger.info(f'Inserted batch of {rows_in_batch} rows ({total_rows}/{len(dataframe)} total)')
        except Exception as e:
            logger.error(f"Error inserting batch: {e}")
            # If fast_executemany fails, try the regular executemany
            try:
                logger.info("Falling back to regular executemany...")
                cursor.fast_executemany = False
                for row in batch:
                    cursor.execute(insert_stmt, row)
                rows_in_batch = len(batch)
                total_rows += rows_in_batch
                logger.info(f'Inserted batch of {rows_in_batch} rows ({total_rows}/{len(dataframe)} total) using fallback method')
            except Exception as inner_e:
                logger.error(f"Error in fallback insert: {inner_e}")
                raise inner_e
    
    # Commit the transaction
    raw_conn.commit()
    
    return total_rows