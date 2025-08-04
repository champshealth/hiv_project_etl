# This script targets the Python client API version 3.0.0 and later
import pandas as pd
import json
import sqlalchemy as sa
import duckdb
from typing import Optional, List
from labkey.api_wrapper import APIWrapper
from config.config import ENV, CONN
from config.config import LABKEY_API_KEY, LABKEY_SERVER_URL, LABKEY_CONTAINER_PATH
from src.extract_hiv_ddl_definitions import extract_hiv_table_ddl_definitions
from src.logging_config import logger


# package_1_all_sql = "src/queries/package1_all.sql"



def get_hiv_project1_1_data() -> pd.DataFrame:
    """
    Query the vw_HIVProject1_1 view from the SQL Server database and return the results as a pandas DataFrame.
    
    Returns:
        pd.DataFrame: A DataFrame containing the data from the vw_HIVProject1_1 view
    """
    try:
        query = """ select s.id, a.SiteId, s.Name, CatchmentId, ReportId, ChampsId, 
                FieldName, FieldValue
			from vw_HIVProject1_1 (nolock) a join Site s on a.SiteId = s.SiteId
            """
        with CONN.connect() as connection:
            df = pd.read_sql_query(sa.text(query), connection)
        logger.info(f"Successfully retrieved {len(df)} rows from vw_HIVProject1_1")
        return df
    except Exception as e:
        logger.error(f"Error querying vw_HIVProject1_1: {str(e)}")
        raise


def pivot_hiv_project1_1_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot the HIV Project 1.1 data using DuckDB.
    
    Args:
        df: DataFrame returned from get_hiv_project1_1_data()
        
    Returns:
        pd.DataFrame: Pivoted DataFrame with FieldNames as columns and max(FieldValue) as values
    """
    try:
        logger.info("Starting to pivot HIV Project 1.1 data")
        
        # Initialize DuckDB in-memory database
        con = duckdb.connect(database=':memory:')
        
        # Register the DataFrame as a DuckDB table
        con.register('hiv_data', df)
        
        # Get unique FieldNames for pivoting
        field_names = con.execute("""
            SELECT DISTINCT FieldName FROM hiv_data WHERE FieldName IS NOT NULL
        """).fetchdf()['FieldName'].tolist()
        
        if not field_names:
            logger.warning("No field names found for pivoting")
            return pd.DataFrame()
        
        # Create a CASE statement for each field name
        case_statements = []
        for field in field_names:
            # Clean the field name to be a valid SQL identifier
            safe_field = field.replace('"', '""')
            case_statements.append(
                f"MAX(CASE WHEN FieldName = '{safe_field}' THEN FieldValue ELSE NULL END) AS \"{safe_field}\""
            )
        
        # Build the pivot query
        pivot_query = f"""
        SELECT 
            id,
            SiteId,
            Name,
            CatchmentId,
            ReportId,
            ChampsId,
            {', '.join(case_statements)}
        FROM hiv_data
        GROUP BY id, SiteId, Name, CatchmentId, ReportId, ChampsId
        """
        
        # Execute the pivot query
        pivoted_df = con.execute(pivot_query).fetchdf()
        
        logger.info(f"Successfully pivoted data. Result has {len(pivoted_df)} rows and {len(pivoted_df.columns)} columns")
        return pivoted_df
        
    except Exception as e:
        logger.error(f"Error pivoting HIV Project 1.1 data: {str(e)}")
        raise


# Initialize LabKey server context
server_context = APIWrapper(f"{LABKEY_SERVER_URL}", container_path=f"{LABKEY_CONTAINER_PATH}" , 
                          api_key=f"{LABKEY_API_KEY}", use_ssl=True)

# def delete_all_rows_list(schema_name, query_name) -> bool:
#     """Deletes all rows from a LabKey list using truncateTable."""
#     try:
#         truncate_info = server_context.query.truncate_table(
#             schema_name=schema_name, 
#             query_name=query_name
#         )
#         print(f"Delete all rows in list: {query_name}. {truncate_info['deletedRows']} rows deleted")
#         return True
#     except Exception as e:
#         print(f"Error truncating list {query_name} : {e}")
#         return False

# def add_rows(schema_name, query_name, csv_file_path):
#     """Adds rows from a CSV file to a LabKey list (query_name param)."""
#     try:
#         df = pd.read_csv(csv_file_path)
#         df = df.fillna('') 
#         # Convert DataFrame to list of dictionaries for LabKey API
#         rows_to_insert = df.to_dict(orient='records')
#         response = server_context.query.insert_rows(
#             schema_name=schema_name,
#             query_name=query_name,
#             rows=rows_to_insert
#         )
#         print(f"Labkey: Added {len(rows_to_insert)} rows to list {query_name}.")
#         return response
#     except Exception as e:
#         print(f"Error adding rows: {e}")
#         return None

if __name__ == '__main__':
    # Delete all rows from the list
    # delete_all_rows_list('lists', 'hiv_project_1_1')
    # add_rows('lists', 'hiv_project_1_1', 'data/pivoted_project_1_1_data.csv')
    print(ENV)
    # extract_hiv_table_ddl_definitions()