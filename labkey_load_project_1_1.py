# This script targets the Python client API version 3.0.0 and later
import pandas as pd
import json
from labkey.api_wrapper import APIWrapper
from config.config import LABKEY_API_KEY, LABKEY_SERVER_URL, LABKEY_CONTAINER_PATH



server_url = 'labkey.emory.edu'
api_key = 'acb50305cd0ee388e37e1d95d314105f082581c30500be47a9b7363f19000226'

# #ssl_context = ssl.SSLContext()
# #ssl_context.verify_mode = ssl.CERT_NONE

server_context = APIWrapper(LABKEY_SERVER_URL, container_path=LABKEY_CONTAINER_PATH , api_key=LABKEY_API_KEY,
                            use_ssl=True)
# projects = server_context.get_projects()
# my_results = server_context.query.select_rows(
#     schema_name='lists',
#     query_name='hiv_project_1_1',
#     # columns=['icd10_code', 'description']
# )
# # rows key contains a list of records in the table
# df = pd.DataFrame(my_results['rows'])
# df.head()

# truncate_info = server_context.query.truncate_table(schema_name='lists', query_name='hiv_project_1_1')
# print(f"Delete all rows in table: {truncate_info["deletedRows"]} rows deleted")
# print(my_results)

# api = APIWrapper('labkey.emory.edu', container_path='CHAMPS/CHAMPS Data View', use_ssl=True)
# my_results = api.query.select_rows(
#     schema_name='lists',
#     query_name='hiv_project_1_1',
#     # columns=['icd10_code', 'description']
# )
# results = json.loads(json.dumps(my_results))
# print(results.keys())
# print(results['columnModel'])
# df = pd.DataFrame(results['rows'])
# print(df.keys())
# df.head()


# server_url = ''
# api_key = ''

server_context = APIWrapper(server_url, container_path='CHAMPS/CHAMPS Data View', api_key=api_key, use_ssl=True)

def delete_all_rows_list(schema_name, query_name) -> bool:
    """Deletes all rows from a LabKey list using truncateTable."""
    try:
        truncate_info = server_context.query.truncate_table(
            schema_name=schema_name, 
            query_name=query_name
        )
        print(f"Delete all rows in list: {query_name}. {truncate_info['deletedRows']} rows deleted")
        return True
    except Exception as e:
        print(f"Error truncating list {query_name} : {e}")
        return False

def add_rows(schema_name, query_name, csv_file_path):
    """Adds rows from a CSV file to a LabKey list (query_name param)."""
    try:
        df = pd.read_csv(csv_file_path)
        df = df.fillna('') 
        # Convert DataFrame to list of dictionaries for LabKey API
        rows_to_insert = df.to_dict(orient='records')
        response = server_context.query.insert_rows(
            schema_name=schema_name,
            query_name=query_name,
            rows=rows_to_insert
        )
        print(f"Labkey: Added {len(rows_to_insert)} rows to list {query_name}.")
        return response
    except Exception as e:
        print(f"Error adding rows: {e}")
        return None

if __name__ == '__main__':
    # Delete all rows from the list
    delete_all_rows_list('lists', 'hiv_project_1_1')
    add_rows('lists', 'hiv_project_1_1', 'data/pivoted_project_1_1_data.csv')

# # 1. Get existing data 
# my_results = server_context.query.select_rows(
#     schema_name='lists',
#     query_name='hiv_project_1_1'
# )
# df = pd.DataFrame(my_results['rows'])


# Add rows from a CSV
# add_rows('lists', 'hiv_project_1_1', 'path/to/your/file.csv')  # Replace with the actual path.

# Query again to verify changes
# my_results_after_changes = server_context.query.select_rows(
#     schema_name='lists',
#     query_name='hiv_project_1_1'
# )
# df_after_changes = pd.DataFrame(my_results_after_changes['rows'])
# print(df_after_changes.head())