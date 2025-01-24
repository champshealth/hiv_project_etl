# redcap_api_export.py
# this script will export the REDCap API data as a pandas dataframe
import requests
import pandas as pd
from config.config import REDCAP_URL
from requests.exceptions import RequestException

def redcap_api_export(redcap_token, file_name) -> pd.DataFrame:
    """Export the REDCap API data as a pandas dataframe."""
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

        try:
            data = response.json()
            # Check for empty response and return None
            if not data:  
                return None 
            df = pd.DataFrame(data)
            df.to_csv(file_name, index=False)
            return df

        except requests.exceptions.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}") from e

    except RequestException as e:
        raise RequestException(f"Error fetching data from REDCap API: {e}") from e