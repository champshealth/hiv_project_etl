"""
Project 6.1 data loader.

This module provides functionality to load and process Project 6.1 data from REDCap into the database.
"""
import pandas as pd
import sqlalchemy as sa
from src.create_data_dict_df import create_data_dict_df
from src.logging_config import logger
from config.config import CONN, DB_SCHEMA, REDCAP_DATA_DICT_FILE_61, REDCAP_DATA_DICT_APPEND_FILE_61, DATA_DICT_TABLE_61, DATA_TABLE_61

def db_load_project_6_1(df: pd.DataFrame = None) -> None:
    """
    Load Project 6.1 data from REDCap into the database.
    
    Args:
        df: DataFrame containing the project 6.1 data. If None, the function will return early.
    """
    logger.info('Starting db_load_project_6_1')
    
    if df is None or df.empty:
        logger.info('No 6.1 data to load')
        return
        
    try:
        engine = CONN
        with engine.connect() as conn:
            # Create and load data dictionary
            data_dict_df = create_data_dict_df(REDCAP_DATA_DICT_FILE_61, REDCAP_DATA_DICT_APPEND_FILE_61)

            # Truncate the data dictionary table
            truncate_data_dict = sa.text(f"TRUNCATE TABLE stg.{DATA_DICT_TABLE_61}")
            conn.execute(truncate_data_dict)
            
            # Load data dictionary data
            if not data_dict_df.empty:
                data_dict_insert = data_dict_df.to_sql(
                    DATA_DICT_TABLE_61, 
                    conn, 
                    schema='stg', 
                    if_exists='append', 
                    index=False
                )
                logger.info(f'Loaded {data_dict_insert} rows into Project 6.1 DATA DICTIONARY table: {DATA_DICT_TABLE_61}.')
            else:
                logger.info('No data dictionary rows to load for Project 6.1.')

            # Rename columns to match the staging table column names
            df = df.rename(columns={
                'record': 'PacketVersionId',
                'redcap_repeat_instrument': 'RepeatInstrument',
                'redcap_repeat_instance': 'RepeatInstance', 
                'field_name': 'FieldName', 
                'value': 'FieldValue',
                'champs_id': 'ChampsId'  # This will be added in the next step if it exists
            })
            
            # Extract ChampsId from the data where field_name is 'champs_id'
            if 'ChampsId' not in df.columns:
                # Create a mapping of PacketVersionId to ChampsId
                champs_id_mapping = df[df['FieldName'] == 'champs_id'].set_index('PacketVersionId')['FieldValue']
                # Add ChampsId column by mapping from PacketVersionId
                df['ChampsId'] = df['PacketVersionId'].map(champs_id_mapping)
                # Forward fill ChampsId within each PacketVersionId group
                df['ChampsId'] = df.groupby('PacketVersionId')['ChampsId'].ffill()
            
            # Ensure ChampsId is not null (required field) and trim whitespace
            if df['ChampsId'].isnull().any():
                logger.warning('Some records are missing ChampsId. These will be set to empty string.')
                df['ChampsId'] = df['ChampsId'].fillna('')
            
            # Trim whitespace from ChampsId
            df['ChampsId'] = df['ChampsId'].str.strip()
            
            # Filter out records with ChampsId is not equal to 9 characters
            invalid_champs = df[df['ChampsId'].str.len() != 9]['ChampsId'].unique()
            if len(invalid_champs) > 0:
                logger.error(f'Found {len(invalid_champs)} invalid ChampsId values (length != 9): {invalid_champs.tolist()}')
                # Filter out invalid ChampsId records
                initial_count = len(df)
                df = df[df['ChampsId'].str.len() == 9]
                filtered_count = initial_count - len(df)
                if filtered_count > 0:
                    logger.warning(f'Filtered out {filtered_count} records with invalid ChampsId (length != 9)')

            # Truncate the 6.1 staging table
            truncate_stg = sa.text(f"TRUNCATE TABLE stg.{DATA_TABLE_61}")
            conn.execute(truncate_stg)

            # Load data in chunks for better performance
            chunk_size = 1000
            total_rows = 0
            total_chunks = (len(df) + chunk_size - 1) // chunk_size
            logger.info(f'Loading data in {total_chunks} chunks of {chunk_size} rows each...')
            
            for i in range(0, len(df), chunk_size):
                chunk_df = df[i:i+chunk_size]
                rows_added = fast_insert_with_executemany(conn, DATA_TABLE_61, 'stg', chunk_df, batch_size=chunk_size)
                total_rows += rows_added
                logger.info(f'Loaded chunk {(i//chunk_size)+1}/{total_chunks} with {rows_added} rows.')
            
            logger.info(f'Finished db_load_project_6_1. Loaded {total_rows} rows into Project 6.1 data table: {DATA_TABLE_61}.')

    except Exception as e:
        logger.error(f'Error in db_load_project_6_1: {e}')
        raise e

def fast_insert_with_executemany(conn, table_name, schema, dataframe, batch_size=1000):
    """
    Optimized function to insert data using executemany with pyodbc.
    
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
    insert_stmt = sa.text(f"INSERT INTO {schema}.{table_name} ({column_str}) VALUES ({placeholder_str})")
    insert_stmt = str(insert_stmt)  # Convert to string for pyodbc compatibility
    
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
