import os
import yaml
import uuid
import datetime
from include.ci_utils import get_engine
from include.aws_secrets import get_redcap_config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ENV = os.environ.get("APP_ENV", "dev")
_redcap_secret = get_redcap_config(ENV)
REDCAP_URL = _redcap_secret["REDCAP_API_URL"]


def load_redcap_tokens(group):
    with open("config/redcap_tokens.yaml") as file:
        token_config = yaml.safe_load(file)

    tokens = []
    for token in token_config[f"tokens_{group}"]:
        env_key = token["env_key"]
        token_value = _redcap_secret.get(env_key)
        if token_value:
            tokens.append({
                "name": token["name"],
                "token": token_value,
                "description": token["description"],
            })
    return tokens


REDCAP_11_TOKENS = load_redcap_tokens("11")
REDCAP_31_TOKENS = load_redcap_tokens("31")
REDCAP_CA_TOKENS = load_redcap_tokens("ca")
REDCAP_61_TOKENS = load_redcap_tokens("61")

REDCAP_API_TOKEN_CA = _redcap_secret.get("REDCAP_API_TOKEN_CA")
REDCAP_API_TOKEN_31 = _redcap_secret.get("REDCAP_API_TOKEN_31")
ETL_USER_ID = "HIV_PROJECT_ETL"

DATA_DIR = "data"
LOG_DIR = "logs"
DATA_DICT_DIR = "data_dictionaries"
JOB_ID = uuid.uuid4()
JOB_DATE = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
FILE_DATETIME = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
LOG_FILE = os.path.join(LOG_DIR, "hiv_project_etl_log.jsonl")
ERROR_LEVELS = ["ERROR", "CRITICAL"]

REDCAP_DATA_DICT_FILE_11 = os.path.join(DATA_DICT_DIR, "AdultHIVProject1_1_DataDict_2024-12-13.csv")
REDCAP_DATA_DICT_FILE_CA = os.path.join(DATA_DICT_DIR, "AdultHIVClinicalAbstr_DataDict_2024-11-01.csv")
REDCAP_DATA_DICT_FILE_31 = os.path.join(DATA_DICT_DIR, "AdultHIVProject3_1_DataDict_2025-01-28.csv")
REDCAP_DATA_DICT_FILE_61 = os.path.join(DATA_DICT_DIR, "AdultHIVProject6_1_DataDict_2025-11-12.csv")

REDCAP_DATA_DICT_APPEND_FILE_11 = os.path.join(DATA_DICT_DIR, "AdultHIVProject1_1_DataDict_append.csv")
REDCAP_DATA_DICT_APPEND_FILE_CA = os.path.join(DATA_DICT_DIR, "AdultHIVClinicalAbstr_DataDict_append.csv")
REDCAP_DATA_DICT_APPEND_FILE_31 = os.path.join(DATA_DICT_DIR, "AdultHIVProject3_1_DataDict_append.csv")
REDCAP_DATA_DICT_APPEND_FILE_61 = os.path.join(DATA_DICT_DIR, "AdultHIVProject6_1_DataDict_2025-11-12_active.csv")

REDCAP_EXPORT_FILE_11 = os.path.join(DATA_DIR, f"redcap_export_11_{FILE_DATETIME}_{JOB_ID}")
REDCAP_EXPORT_FILE_31 = os.path.join(DATA_DIR, f"redcap_export_31_{FILE_DATETIME}_{JOB_ID}")
REDCAP_EXPORT_FILE_CA = os.path.join(DATA_DIR, f"redcap_export_ca_{FILE_DATETIME}_{JOB_ID}")
REDCAP_EXPORT_FILE_61 = os.path.join(DATA_DIR, f"redcap_export_61_{FILE_DATETIME}_{JOB_ID}")

DB_SCHEMA = os.environ.get("DB_SCHEMA", "hiv")
DATA_DICT_TABLE_11 = "HIVDataDictProj1_1"
DATA_TABLE_11 = "HIVProject1_1_stg"
DATA_DICT_TABLE_31 = "HIVDataDictProj3_1"
DATA_TABLE_31 = "HIVProject3_1_stg"
DATA_DICT_TABLE_CA = "HIVDataDictClinicalAbstr"
DATA_TABLE_CA = "HIVClinicalAbstract_stg"
DATA_DICT_TABLE_61 = "HIVDataDictProj6_1"
DATA_TABLE_61 = "HIVProject6_1_stg"

CLINICAL_ABSTRACTION_VIEW = "vw_HIVClinicalAbstraction"
CLINICAL_ABSTRACTION_FORM_COMPLETE_VIEW = "vw_HIVClinicalAbstractionFormComplete"

HIV_DEATH_NOTIFICATION_VIEW = "vw_HIVDeathNotification"
CONSENTTRACK_VIEW_NAME = "vw_HIVConsentTracking"
MITS_PROCEDURE_VIEW_NAME = "vw_HIVMITSProcedure"
MITS_SPECIMEN_COLLECT_VIEW_NAME = "vw_HIVMitsSpecimensCollect"
CPL_WIDGET_VIEW_NAME = "vw_HIVCPLWidgetAggregate"

CONN = get_engine(ENV)
