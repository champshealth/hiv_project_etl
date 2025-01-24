import logging
from pythonjsonlogger import jsonlogger
import os
import datetime
import pytz
from logging.handlers import RotatingFileHandler
from config.config import LOG_DIR, JOB_ID

LOG_FILE = os.path.join(LOG_DIR, "hiv_project_etl_log.jsonl")

# Define a custom log record factory that adds the jobid=JOB_ID and formats asctime
def log_record_factory(*args, **kwargs):
    record = old_log_record_factory(*args, **kwargs)
    record.jobid = JOB_ID
    local_tz = pytz.timezone('America/New_York')
    local_dt = datetime.datetime.fromtimestamp(record.created).astimezone(local_tz)
    record.log_date = local_dt.strftime("%Y-%m-%d %H:%M:%S.%f%z")  # Create a NEW field
    return record

# Replace the old log record factory with custom log_record_factory
old_log_record_factory = logging.getLogRecordFactory()
logging.setLogRecordFactory(log_record_factory)

# Get the root logger
logger = logging.getLogger()

# Ensure no other formatters are set on handlers (if applicable)
if logger.hasHandlers():
    for handler in logger.handlers:
        handler.setFormatter(None)  # Clear any existing formatters

# Configure rotating file handler
handler = RotatingFileHandler(LOG_FILE, maxBytes=1024 * 1024, backupCount=5)  # 1MB size, keep 5 backups

# Define JSON formatter with desired asctime format
formatter = jsonlogger.JsonFormatter('%(log_date)s %(levelname)s %(message)s %(process)d %(jobid)s')


handler.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(handler)