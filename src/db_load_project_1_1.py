# db_load_project_1_1/py
import duckdb
import pandas as pd
import sqlalchemy as sa
from config.config import CONN, DB_SCHEMA ,REDCAP_DATA_DICT_FILE_11, REDCAP_DATA_DICT_APPEND_FILE_11, DATA_DICT_TABLE_11, DATA_TABLE_11
from src.create_data_dict_df import create_data_dict_df
from src.logging_config import logger
import concurrent.futures
import multiprocessing
import pyodbc
from sqlalchemy.engine import Engine
from sqlalchemy.sql import text as sa_text
from typing import List, Dict, Any
# df = pd.read_csv('data/redcap_hiv_project1_1.csv')


def process_chunk(chunk_df):
    """Process a chunk of data"""
    conn = duckdb.connect()
    conn.execute("CREATE TABLE chunk_df AS SELECT * FROM chunk_df")
    
    # Extract key fields similar to transform_project_1_1 function
    result = conn.execute("""WITH site_cte as (
                            SELECT record,
                            MAX(CASE WHEN field_name = 'champs_id' THEN value END) AS champs_id,
                            MAX(CASE WHEN field_name = 'site_id' THEN value END) AS site_id
                            ,max(case when field_name like 'catchment_id%' THEN value END) AS catchment_id
                            FROM chunk_df
                            WHERE (field_name in ('champs_id', 'site_id' ) or field_name like 'catchment_id%')
                            GROUP BY record 
                        )
                        SELECT p.*, site_cte.site_id, site_cte.catchment_id, site_cte.champs_id 
                        from chunk_df p
                        join site_cte on p.record = site_cte.record 
                    """).fetch_df()
    return result

def transform_project_1_1(df: pd.DataFrame) -> pd.DataFrame:
    df = df.astype(str)

    # For small datasets, just use the original method
    if len(df) < 10000:
        conn = duckdb.connect()
        conn.execute(" CREATE TABLE redcap_hiv_project1_1_df AS SELECT * FROM df ")
        conn.execute(f"""CREATE or REPLACE table redcap_hiv_project1_1 as
                        select record,field_name,value 
                        FROM redcap_hiv_project1_1_df
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
    else:
        # For larger datasets, use parallel processing
        logger.info(f"Processing {len(df)} rows with parallel execution")
        # Split data into chunks for parallel processing
        num_processes = min(multiprocessing.cpu_count(), 4)  # Limit to 4 processes max
        chunk_size = len(df) // num_processes
        chunks = [df[i:i+chunk_size] for i in range(0, len(df), chunk_size)]
        
        # Process chunks in parallel
        results = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_processes) as executor:
            futures = [executor.submit(process_chunk, chunk) for chunk in chunks]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        
        # Combine results
        df_site = pd.concat(results, ignore_index=True)
        
    # write to csv for testing
    df_site.to_csv('data/redcap_project1_1.csv', index=False)
    return df_site

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

def db_load_project_1_1(df: pd.DataFrame) -> pd.DataFrame:
    logger.info('Starting db_load_project_1_1.py')
    try:
        df = transform_project_1_1(df).fillna('')
        engine = CONN
        
        with engine.connect() as conn:
            # data dictionary table
            data_dict_df = create_data_dict_df(REDCAP_DATA_DICT_FILE_11, REDCAP_DATA_DICT_APPEND_FILE_11)
            # print(data_dict_df.shape)
            
            conn.execute(sa.text(f"TRUNCATE TABLE stg.{DATA_DICT_TABLE_11}"))

            data_dict_insert = data_dict_df.to_sql(DATA_DICT_TABLE_11, conn, schema='stg', if_exists='append', index=False) if not data_dict_df.empty else None
            logger.info(f'db_load_project_1_1.py. Loaded {data_dict_insert} rows into Project 1.1 DATA DICTIONARY table: {DATA_DICT_TABLE_11}.')

            # 1.1 stg data table
            df = df.rename(columns={'record': 'ReportId','site_id':'SiteId', 'catchment_id': 'CatchmentId'  ,'champs_id': 'ChampsId' , 
                                    'field_name': 'FieldName', 'value': 'FieldValue'})
            # print(df.keys())
            df = df.astype({'SiteId': str,'CatchmentId': str, 'ReportId': str, 'ChampsId':str ,'FieldName': str, 'FieldValue': str}) 
            df = df[['SiteId','CatchmentId', 'ReportId', 'ChampsId', 'FieldName', 'FieldValue']]
         
            # warning that catchment_id are missing in the data, provide a count of the missing catchment_id by site_id, ReportId
            missing_catchment_id = df[df['CatchmentId'] == '']
            if not missing_catchment_id.empty:
                logger.warning(f'Missing catchment_id in Project 1.1 data: {missing_catchment_id.groupby(["SiteId", "ReportId"]).size()}')

            # truncate table
            truncate_stg_table = sa.text(f"TRUNCATE TABLE stg.{DATA_TABLE_11}")
            conn.execute(truncate_stg_table)
            
            # Load data in chunks of 1000 rows for better performance
            chunk_size = 1000
            total_rows = 0
            
            # Display progress info
            total_chunks = (len(df) + chunk_size - 1) // chunk_size
            logger.info(f'Loading data in {total_chunks} chunks of {chunk_size} rows each...')
            
            for i in range(0, len(df), chunk_size):
                chunk_df = df[i:i+chunk_size]
                # Remove method='multi' which is causing the SQL Server error
                rows_added = fast_insert_with_executemany(conn, DATA_TABLE_11, 'stg', chunk_df, batch_size=chunk_size)
                total_rows += rows_added
                logger.info(f'Loaded chunk {(i//chunk_size)+1}/{total_chunks} with {rows_added} rows.')
            
            # conn.commit()

            logger.info(f'Finished db_load_project_1_1.py. Loaded {total_rows} rows into Project 1.1 data table: {DATA_TABLE_11}.')
    except Exception as e:
        logger.error(f'Error in db_load_project_1_1.py: {e}')
        raise e
    return df