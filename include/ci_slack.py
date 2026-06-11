import os
import slack_sdk as slack
from slack_sdk.errors import SlackApiError
from include.aws_secrets import get_slack_config

_env = os.environ.get("APP_ENV", "dev")
_slack_config = get_slack_config(_env)
_slack_token = _slack_config["slack_token"]
_default_channel = _slack_config.get("channel_id")


def get_channel_id(channel_name):
    try:
        client = slack.WebClient(token=_slack_token)
        channel_name = channel_name.lstrip("#")
        result = client.conversations_list(types="public_channel,private_channel")
        for channel in result["channels"]:
            if channel["name"] == channel_name:
                return channel["id"]
        return None
    except SlackApiError as e:
        print(f"Error getting channel ID: {e}")
        return None


def file_upload(filenm, channels="logs"):
    client = slack.WebClient(token=_slack_token)
    channel_id = get_channel_id(channels) if channels else _default_channel
    title = os.path.basename(filenm)
    try:
        response = client.files_upload_v2(
            filename=title, file=filenm, channel=channel_id, title=title
        )
        print("SUCCESS: File uploaded. File ID: ", response["file"]["id"])
    except SlackApiError as e:
        print(f"Error uploading file: {e}")


def post_mesg(text, channel=None):
    try:
        client = slack.WebClient(token=_slack_token)
        channel_id = get_channel_id(channel) if channel else _default_channel
        if not channel_id:
            raise ValueError(f"Channel '{channel or 'default'}' not found")
        response = client.chat_postMessage(channel=channel_id, text=text)
        return response
    except SlackApiError as e:
        print(f"Error posting message: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def post_mesg_channel(text, channel):
    post_mesg(text=text, channel=channel)
