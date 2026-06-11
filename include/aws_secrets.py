import json
import os
import boto3
from botocore.exceptions import ClientError

ACCOUNT_MAP = {
    "dev": "192914852225",
    "stg": "298660930181",
    "prod": "600942988942",
}

_secret_cache = {}


def _resolve_region():
    region = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION")
    if region:
        return region
    try:
        import urllib.request
        token = urllib.request.urlopen(
            "http://169.254.169.254/latest/api/token",
            data=b"", timeout=2,
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"}
        ).read().decode()
        az = urllib.request.urlopen(
            "http://169.254.169.254/latest/meta-data/placement/availability-zone",
            timeout=2, headers={"X-aws-ec2-metadata-token": token}
        ).read().decode()
        return az.rstrip("abcdefghijklmnopqrstuvwxyz")
    except Exception:
        return "us-east-1"


def get_secret(env, secret_name):
    cache_key = f"{env}:{secret_name}"
    if cache_key in _secret_cache:
        return _secret_cache[cache_key]

    full_name = f"champs-{env}-{secret_name}"
    session = boto3.session.Session(region_name=_resolve_region())
    client = session.client(service_name="secretsmanager")

    try:
        response = client.get_secret_value(SecretId=full_name)
    except ClientError as e:
        raise RuntimeError(f"Failed to fetch secret {full_name}: {e}")

    secret = json.loads(response["SecretString"])
    _secret_cache[cache_key] = secret
    return secret


def get_redcap_config(env):
    secret = get_secret(env, "redcap-tokens-hiv-etl")
    return secret


def get_db_credentials(env):
    secret = get_secret(env, "portal-db-credentials")
    return secret


def get_slack_config(env):
    secret = get_secret(env, "slack-token")
    return secret
