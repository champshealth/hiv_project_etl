# redcap_api_export.py
# this script will export the REDCap API data as a pandas dataframe
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
from config.config import REDCAP_URL
from requests.exceptions import RequestException
from src.logging_config import logger

def redcap_api_export(redcap_tokens: list, output_file ) -> pd.DataFrame:
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
        total=3,  # number of retries
        backoff_factor=1,  # wait 1, 2, 4 seconds between retries
        status_forcelist=[500, 502, 503, 504]  # HTTP status codes to retry on
    )
    
    # Create session with retry strategy
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    all_dfs = []
    for token_info in redcap_tokens:
        logger.info(f"Fetching data for project: {token_info['name']}")
        data = {
            'token': token_info['token'],
            'content': 'record',
            'action': 'export',
            'format': 'json',
            'type': 'eav',
            'csvDelimiter': '',
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

            data = response.json()
            if data:
                df = pd.DataFrame(data)
                # Add project identifier to the dataframe
                df['redcap_project'] = token_info['name']
                all_dfs.append(df)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from REDCap API for project {token_info['name']}: {e}")

    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        
        # Convert redcap_repeat_instance to string before writing
        if 'redcap_repeat_instance' in final_df.columns:
            final_df['redcap_repeat_instance'] = final_df['redcap_repeat_instance'].astype(str)
        
        # Store output as csv and parquet
        final_df.to_csv(output_file + ".csv", index=False)
        try:
            final_df.to_parquet(output_file + ".parquet", index=False)
        except Exception as e:
            logger.warning(f"Error writing parquet file in script `redcap_api_export` : {e}")
            logger.warning("Continuing with CSV output only")
        
        return final_df
    else:
        return None