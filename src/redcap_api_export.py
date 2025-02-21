# redcap_api_export.py
# this script will export the REDCap API data as a pandas dataframe
import requests
import pandas as pd
from config.config import REDCAP_URL
from requests.exceptions import RequestException
from src.logging_config import logger

def redcap_api_export(redcap_tokens: list, output_file ) -> pd.DataFrame:
    """Export the REDCap API data as a pandas dataframe."""

    all_dfs = []
    for redcap_token in redcap_tokens:
        data = {
            'token': redcap_token,
            'content': 'record',
            'action': 'export',
            'format': 'json',
            'type': 'eav',
            'csvDelimiter': '',
            'rawOrLabel': 'raw',
            'rawOrLabelHeaders': 'raw',
            'exportCheckboxLabel': 'true', # ignored if 'type': 'eav'
            'exportSurveyFields': 'false',
            'exportDataAccessGroups': 'false',
            'returnFormat': 'json'
        }

        try:
            response = requests.post(REDCAP_URL, data=data)
            response.raise_for_status()  # Raise an exception for non-200 status codes

            data = response.json()
            if data:
                df = pd.DataFrame(data)
                all_dfs.append(df)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from REDCap API: {e}")

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