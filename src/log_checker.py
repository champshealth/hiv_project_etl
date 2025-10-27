import json
import datetime
from include.ci_slack import post_mesg_channel
from config.config import LOG_FILE, ERROR_LEVELS


def get_current_date():
    """Gets the current date in YYYY-MM-DD format."""
    return datetime.datetime.now().strftime("%Y-%m-%d")

def parse_log_entry(line):
    """Parses a log entry from JSON."""
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        print(f"Warning: Skipping invalid JSON line: {line.strip()}")  # Handle bad JSON
        return None

def check_for_errors(log_file, current_date):
    """Checks the log file for errors on the current date."""
    errors = []
    with open(log_file, "r") as f:
        lines = f.readlines()
        last_lines = lines[-2000:]  # Get the last 2000 lines from the log file
        for line in last_lines:
            log_entry = parse_log_entry(line)
            if log_entry is None:
                continue #Skip if the JSON is bad.

            log_date = log_entry.get("asctime", "").split(" ")[0] #Extract the date part.
            log_level = log_entry.get("levelname", "")
            # Check if the log entry is from today and has an error level
            if log_date == current_date and log_level in ERROR_LEVELS:
                errors.append(log_entry)
    return errors


def format_slack_message(errors):
    """Formats the error messages for Slack."""
    if not errors:
        return "*HIV Project ETL:* Successful. NO errors found in the log file for today."

    message = f"*HIV Project ETL:* ERRORS found in log file ({get_current_date()}):\n"
    for error in errors:
        message += f"```{json.dumps(error, indent=2)}```\n"  # Format nicely as code
    return message

def check_log_and_notify():
    current_date = get_current_date()
    errors = check_for_errors(LOG_FILE, current_date)
    slack_message = format_slack_message(errors)
    post_mesg_channel(text=slack_message, channel="#logs")

# if __name__ == "__main__":
#     current_date = get_current_date()
#     errors = check_for_errors(LOG_FILE, current_date)
#     slack_message = format_slack_message(errors)
#     post_mesg_channel(text=slack_message, channel="#logs")