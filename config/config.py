import os
import yaml
from dotenv import load_dotenv
import uuid
import datetime
from include.ci_utils import connect_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv()
REDCAP_URL = os.getenv('REDCAP_URL')

def load_redcap_tokens(group):
    """Load REDCap tokens with their metadata from YAML config for specific group"""
    with open('config/redcap_tokens.yaml', 'r') as file:
        token_config = yaml.safe_load(file)
    
    tokens = []
    for token in token_config[f'tokens_{group}']:
        env_value = os.getenv(token['env_key'])
        if env_value:
            tokens.append({
                'name': token['name'],
                'token': env_value,
                'description': token['description']
            })
    return tokens

# Load tokens for each project group
REDCAP_11_TOKENS = load_redcap_tokens('11')
REDCAP_31_TOKENS = load_redcap_tokens('31')
REDCAP_CA_TOKENS = load_redcap_tokens('ca')

# Legacy token variables - kept for backward compatibility
REDCAP_API_TOKEN_CA = os.getenv('REDCAP_API_TOKEN_CA')
REDCAP_API_TOKEN_31 = os.getenv('REDCAP_API_TOKEN_31')
ETL_USER_ID = 'HIV_PROJECT_ETL'

DATA_DIR = 'data'
LOG_DIR = 'logs'
DATA_DICT_DIR = 'data_dictionaries'
JOB_ID = uuid.uuid4()
JOB_DATE = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
FILE_DATETIME = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

# Pre-requisite: these redcap data dict files should be in the data_dictionaires directory
#  and add the following files to the data directory
REDCAP_DATA_DICT_FILE_11 = os.path.join(DATA_DICT_DIR, 'AdultHIVProject1_1_DataDict_2024-12-11.csv')
REDCAP_DATA_DICT_FILE_CA = os.path.join(DATA_DICT_DIR, 'AdultHIVClinicalAbstr_DataDict_2024-10-30.csv') 
REDCAP_DATA_DICT_FILE_31 = os.path.join(DATA_DICT_DIR, 'AdultHIVProject3_1_DataDict_2025-01-28.csv')

# these files are appended to the data dict files since they are not included in the REDCap data dictionary exports
#  but are found in the data exports. Example: form_complete fields
REDCAP_DATA_DICT_APPEND_FILE_11 = os.path.join(DATA_DICT_DIR,'AdultHIVProject1_1_DataDict_append.csv')
REDCAP_DATA_DICT_APPEND_FILE_CA = os.path.join(DATA_DICT_DIR,'AdultHIVClinicalAbstr_DataDict_append.csv')
REDCAP_DATA_DICT_APPEND_FILE_31 = os.path.join(DATA_DICT_DIR,'AdultHIVProject3_1_DataDict_append.csv')

# redcap data export files for backup
# these files will be strored as parquet files
REDCAP_EXPORT_FILE_11 = os.path.join(DATA_DIR, f'redcap_export_11_{FILE_DATETIME}_{JOB_ID}')
REDCAP_EXPORT_FILE_CA = os.path.join(DATA_DIR, f'redcap_export_ca_{FILE_DATETIME}_{JOB_ID}')
REDCAP_EXPORT_FILE_31 = os.path.join(DATA_DIR, f'redcap_export_31_{FILE_DATETIME}_{JOB_ID}')

DB_SCHEMA = os.getenv('DB_SCHEMA')
DATA_DICT_TABLE_11 = 'HIVDataDictProj1_1'
DATA_TABLE_11 = 'HIVProject1_1_stg'

DATA_DICT_TABLE_31 = 'HIVDataDictProj3_1'
DATA_TABLE_31 = 'HIVProject3_1_stg'

DATA_DICT_TABLE_CA = 'HIVDataDictClinicalAbstr'
DATA_TABLE_CA = 'HIVClinicalAbstract_stg'

CLINICAL_ABSTRACTION_VIEW = 'vw_HIVClinicalAbstraction'
CLINICAL_ABSTRACTION_FORM_COMPLETE_VIEW = 'vw_HIVClinicalAbstractionFormComplete'

# deathnotification data objects
HIV_DEATH_NOTIFICATION_VIEW = 'vw_HIVDeathNotification'

# consent data objects
CONSENTTRACK_VIEW_NAME = 'vw_HIVConsentTracking'

# MITSProcedure data objects
MITS_PROCEDURE_VIEW_NAME = 'vw_HIVMITSProcedure'

# MITS Specimen Collection data objects
MITS_SPECIMEN_COLLECT_VIEW_NAME = 'vw_HIVMitsSpecimensCollect'

# cpl widget data objects
CPL_WIDGET_VIEW_NAME = 'vw_HIVCPLWidgetAggregate'

# TODO: move this to the .env file later
CONN = connect_db.conn_qa()
# CONN = connect_db.conn_stg()
