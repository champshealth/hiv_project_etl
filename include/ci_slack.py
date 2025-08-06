# ci_slack.py
#!/usr/bin/env python3
import configparser
import os
from pathlib import Path
import requests
import slack_sdk as slack
from slack_sdk.errors import SlackApiError

proxy_endpoint = 'http://webproxy.emory.net:3128'
local_creds_file = os.path.join(str(Path.home()),'.config','local_credentials')

config = configparser.ConfigParser()
config.read(local_creds_file)
slack_token = config['slack']['slack_token']

# get channel id for the channel name
def get_channel_id( channel_name):
    try:
        client = slack.WebClient(token=slack_token)
        channel_name = channel_name.lstrip('#')
        result = client.conversations_list(types="public_channel,private_channel")
        for channel in result["channels"]:
            # print(channel["name"], channel["id"])
            if channel["name"] == channel_name:
                return channel["id"]
        return None
    except SlackApiError as e:
        print(f"Error getting channel ID: {e}")
        return None

def file_upload_old(filenm, channels=None):
    try:
        url = 'https://slack.com/api/files.upload'

        # headers = {'Authorization': 'Bearer xoxp-xxxx' ,
        # 'Content-type':  'multipart/form-data'}

        data = {
            'token': slack_token,
            "channels": "#logs" if channels == None else channels ,
            "filename": os.path.basename(filenm),
            'title': os.path.basename(filenm)
        }
        response = requests.post(url=url, data=data, files={
                                 "file": open(filenm, "rb")})

        # print(response.text)
    except Exception as e:
        print(e)

def file_upload(filenm, channels="logs"):
    client = slack.WebClient(token=slack_token)
    channel_id = get_channel_id( "logs") if channels == None else get_channel_id( channels)
    # print(channel_id)
    file_path = filenm
    title = os.path.basename(filenm)
    try:
        response = client.files_upload_v2(
            filename=title,
            file=file_path,
            channel=channel_id,
            title=title
        )
        print('SUCCESS: File uploaded. File ID: ', response['file']['id'])
    except SlackApiError as e:
        print(f"Error uploading file: {e}")  

def post_mesg_old(text, channel=None):
    try:
        url = 'https://slack.com/api/chat.postMessage'
        headers = {'Content-type': 'application/json; charset=utf-8',
                   'Authorization': 'Bearer ' + slack_token, }
        data = {
            "channel": "logs" if channel == None else channel,
            "text": text
        }
        response = requests.post(url=url, json=data, headers=headers)
        # print(response.json())

    except Exception as e:
        print(e)

def post_mesg(text, channel=None):
    """
    Post a message to a Slack channel using slack_sdk
    Args:
        text: Message text to post
        channel: Channel name or ID (defaults to 'logs' if None)
    """
    try:
        client = slack.WebClient(token=slack_token)
        channel_id = get_channel_id(channel) if channel else get_channel_id("logs")
        
        if not channel_id:
            raise ValueError(f"Channel '{channel}' not found")
            
        response = client.chat_postMessage(
            channel=channel_id,
            text=text
        )
        return response
    except SlackApiError as e:
        print(f"Error posting message: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def post_mesg_channel (text,channel):
    # slackr.chat.post_message(channel, text)
    post_mesg(text=text, channel=channel)