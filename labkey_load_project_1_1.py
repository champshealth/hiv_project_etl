# This script targets the Python client API version 3.0.0 and later
import pandas as pd
import json
from labkey.api_wrapper import APIWrapper
from config.config import ENV
# from config.config import LABKEY_API_KEY, LABKEY_SERVER_URL, LABKEY_CONTAINER_PATH
from src.extract_hiv_ddl_definitions import extract_hiv_table_ddl_definitions


# server_context = APIWrapper(f"{LABKEY_SERVER_URL}", container_path=f"{LABKEY_CONTAINER_PATH}" , 
#                             api_key=f"{LABKEY_API_KEY}", use_ssl=True)

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
    extract_hiv_table_ddl_definitions()