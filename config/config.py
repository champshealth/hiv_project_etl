import dotenv
import os
import uuid
import datetime
from include.ci_utils import connect_db
dotenv.load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# pre-requisite: create a .env file in the root directory of the project
# and add the following environment variables
REDCAP_API_TOKEN_11 = os.getenv('REDCAP_API_TOKEN_11')
REDCAP_API_TOKEN_CA = os.getenv('REDCAP_API_TOKEN_CA')
REDCAP_API_TOKEN_31 = os.getenv('REDCAP_API_TOKEN_31')
REDCAP_URL = os.getenv('REDCAP_URL')

LABKEY_SERVER_URL = os.getenv('LABKEY_SERVER_URL')
LABKEY_API_KEY = os.getenv('LABKEY_API_KEY')
LABKEY_CONTAINER_PATH = os.getenv('LABKEY_CONTAINER_PATH')

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
# CONN = connect_db.conn_qa
CONN = connect_db.conn_stg
