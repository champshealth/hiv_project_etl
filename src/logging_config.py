import os
import logging
import datetime
import pytz
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
import watchtower
import boto3
from config.config import LOG_DIR, JOB_ID, ENV

LOG_FILE = os.path.join(LOG_DIR, "hiv_project_etl_log.jsonl")
_CLOUDWATCH_LOG_GROUP = f"/aws/ec2/champs-{ENV}-etl-reporting-ec2/etl-jobs"


def log_record_factory(*args, **kwargs):
    record = old_log_record_factory(*args, **kwargs)
    record.jobid = JOB_ID
    local_tz = pytz.timezone("America/New_York")
    local_dt = datetime.datetime.fromtimestamp(record.created).astimezone(local_tz)
    record.log_date = local_dt.strftime("%Y-%m-%d %H:%M:%S.%f%z")
    return record


old_log_record_factory = logging.getLogRecordFactory()
logging.setLogRecordFactory(log_record_factory)

logger = logging.getLogger()

if logger.hasHandlers():
    for handler in logger.handlers:
        handler.setFormatter(None)

file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1024 * 1024, backupCount=5)
formatter = jsonlogger.JsonFormatter(
    "%(log_date)s %(levelname)s %(message)s %(process)d %(jobid)s"
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

try:
    _region = os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
    _cw_client = boto3.client("logs", region_name=_region)
    cw_handler = watchtower.CloudWatchLogHandler(
        log_group=_CLOUDWATCH_LOG_GROUP,
        stream_name=f"hiv_project_etl/{JOB_ID}",
        send_interval=10,
        boto3_client=_cw_client,
    )
    cw_handler.setFormatter(formatter)
    logger.addHandler(cw_handler)
except Exception as _cw_err:
    logger.warning("CloudWatch logging unavailable — continuing with file-only logging: %s", _cw_err)

logger.setLevel(logging.INFO)