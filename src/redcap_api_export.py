# redcap_api_export.py
# this script will export the REDCap API data as a pandas dataframe
# IMPORTANT: Note that redcap api export is using flat format instead of eav format
# due to eav format returning no data possibly due to Data Access Group (DAG)
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
from config.config import REDCAP_URL
from requests.exceptions import RequestException
from src.logging_config import logger

def convert_flat_to_eav(flat_df):
    """Convert flat dataframe to EAV format with checkbox field handling"""
    # Get the record identifier column (usually first column)
    record_id_col = flat_df.columns[0]

    
    # Check for redcap_repeat* columns to include in id_vars for unpivot (melt)
    has_repeat_instrument = 'redcap_repeat_instrument' in flat_df.columns
    has_repeat_instance = 'redcap_repeat_instance' in flat_df.columns
    
    # Define id_vars with record_id_col initially
    id_vars = [record_id_col]
    
    # include repeat columns in id_vars if they exist for melt
    if has_repeat_instrument:
        id_vars.append('redcap_repeat_instrument')
    if has_repeat_instance:
        id_vars.append('redcap_repeat_instance')
    
    # melt unpivot the flat dataframe to mimc redcap EAV format
    # ouput column ->  record, redcap_repeat_instrument, redcap_repeat_instance, field_name, value
    eav_df = flat_df.melt(
        id_vars=id_vars, 
        var_name='field_name', 
        value_name='value'
    )
    
    # rename the record_id_col to 'record' to match default eav EAV format
    eav_df = eav_df.rename(columns={record_id_col: 'record'})

    # Handle checkbox fields using fields with double underscorE
    checkbox_mask = eav_df['field_name'].str.contains('___', na=False)
    checkbox_rows = eav_df[checkbox_mask].copy()
    non_checkbox_rows = eav_df[~checkbox_mask]
    
    # For checkbox fields where value=1, extract code and update field name
    # and remove ___code from field names
    #  for example fieldname___ch01234 will be converted to fieldname with value ch01234
    if not checkbox_rows.empty:
        # Extract the code from field name when value is 1
        checkbox_rows.loc[checkbox_rows['value'] == '1', 'value'] = \
            checkbox_rows.loc[checkbox_rows['value'] == '1', 'field_name'].str.extract(r'___(.+)$')[0]
        
        # Remove ___code from field names
        checkbox_rows['field_name'] = checkbox_rows['field_name'].str.replace(r'___.*$', '', regex=True)
        
        # Filter out rows where value is 0
        checkbox_rows = checkbox_rows[checkbox_rows['value'] != '0']
        
        # Combine checkbox and non-checkbox rows
        eav_df = pd.concat([non_checkbox_rows, checkbox_rows])
    
    # Drop rows where value is None, NaN, or blank
    eav_df = eav_df.dropna(subset=['value'])
    eav_df = eav_df[eav_df['value'].astype(str).str.strip() != '']
    
    # Convert all values to strings
    eav_df['value'] = eav_df['value'].astype(str)
    
    # Ensure columns are in the correct order for REDCap EAV format
    columns = ['record', 'field_name', 'value']
    
    # Add repeat columns if they exist
    if 'redcap_repeat_instrument' in eav_df.columns:
        columns.insert(1, 'redcap_repeat_instrument')
    if 'redcap_repeat_instance' in eav_df.columns:
        columns.insert(2 if 'redcap_repeat_instrument' in eav_df.columns else 1, 'redcap_repeat_instance')
    
    # Reorder and sort
    eav_df = eav_df[columns]
    eav_df = eav_df.sort_values(['record', 'field_name'])
    
    return eav_df

def redcap_api_export(redcap_tokens: list, output_file) -> pd.DataFrame:
    """
    Export the REDCap API data as a pandas dataframe.
    
    Args:
        redcap_tokens: List of dictionaries containing token metadata
        output_file: Path for output files
    """
    # Flatten the tokens list if it's nested
    if redcap_tokens and isinstance(redcap_tokens[0], list):
        redcap_tokens = [token for sublist in redcap_tokens for token in sublist]

    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504]
    )
    
    # Update the session configuration
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    # Add timeouts
    session.timeout = (5, 30)  # (connect timeout, read timeout)

    all_dfs = []
    skip_projects = []
    
    for token_info in redcap_tokens:
        project_name = token_info['name']
        
        # Skip projects that are known to have issues
        if project_name in skip_projects:
            logger.warning(f"Skipping known problematic project: {project_name}")
            continue
            
        logger.info(f"Fetching data for project: {project_name}")
        data = {
            'token': str(token_info['token']),
            'content': 'record',
            'action': 'export',
            'format': 'json',
            'type': 'flat',
            'rawOrLabel': 'raw',
            'rawOrLabelHeaders': 'raw',
            'exportCheckboxLabel': 'true',
            'exportSurveyFields': 'false',
            'exportDataAccessGroups': 'false',
            'returnFormat': 'json'
        }

        try:
            response = session.post(REDCAP_URL, data=data)
            response.raise_for_status()

            json_data = response.json()
            if json_data:
                # Convert all values to strings to preserve leading zeros and prevent numeric conversion
                for record in json_data:
                    for key, value in record.items():
                        if value is not None:
                            record[key] = str(value)
                            
                df = pd.DataFrame(json_data)
                # write to csv for debugging
                # print(f"Writing flat data to CSV for project {project_name}")
                # df.to_csv(f"data/redcap_{project_name}_flat.csv", index=False)
                df = convert_flat_to_eav(df)
                # df['redcap_project'] = project_name
                all_dfs.append(df)
                logger.info(f"Successfully processed data for {project_name} with {len(df)} rows")
            else:
                logger.warning(f"No data returned for project: {project_name}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from REDCap API for project {project_name}: {e}")

    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        
        # Convert redcap_repeat_instance to string before writing
        if 'redcap_repeat_instance' in final_df.columns:
            final_df['redcap_repeat_instance'] = final_df['redcap_repeat_instance'].astype(str)
        
        final_df.to_csv(output_file + ".csv", index=False)
        try:
            final_df.to_parquet(output_file + ".parquet", index=False)
        except Exception as e:
            logger.warning(f"Error writing parquet file: {e}")
        
        return final_df
    
    return None