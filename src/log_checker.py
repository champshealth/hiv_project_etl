import datetime
import boto3
from include.ci_slack import post_mesg_channel
from config.config import CLOUDWATCH_LOG_GROUP, ERROR_LEVELS


def get_current_date():
    return datetime.datetime.now().strftime("%Y-%m-%d")


def check_log_and_notify():
    current_date = get_current_date()
    client = boto3.client("logs")

    now = int(datetime.datetime.now().timestamp() * 1000)
    two_hours_ago = now - (2 * 60 * 60 * 1000)
    pattern = " ".join(f"?{lvl}" for lvl in ERROR_LEVELS)

    events = []
    kwargs = {
        "logGroupName": CLOUDWATCH_LOG_GROUP,
        "filterPattern": pattern,
        "startTime": two_hours_ago,
        "endTime": now,
    }

    try:
        while True:
            response = client.filter_log_events(**kwargs)
            events.extend(response.get("events", []))
            if "nextToken" not in response:
                break
            kwargs["nextToken"] = response["nextToken"]
    except client.exceptions.ResourceNotFoundException:
        post_mesg_channel(
            text=(
                f"*HIV Project ETL:* CloudWatch log group "
                f"`{CLOUDWATCH_LOG_GROUP}` not found."
            ),
            channel="#logs",
        )
        return
    except Exception as e:
        post_mesg_channel(
            text=f"*HIV Project ETL:* Error querying CloudWatch logs: {e}",
            channel="#logs",
        )
        return

    if not events:
        message = (
            f"*HIV Project ETL:* Successful. "
            f"NO errors found in CloudWatch logs ({current_date})."
        )
    else:
        message = (
            f"*HIV Project ETL:* {len(events)} error(s) found "
            f"in CloudWatch logs ({current_date}):\n"
        )
        for e in events[:20]:
            message += f"```{e['message']}```\n"
        if len(events) > 20:
            message += f"... and {len(events) - 20} more."

    post_mesg_channel(text=message, channel="#logs")
