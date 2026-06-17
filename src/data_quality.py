import json
import datetime
import boto3
from botocore.exceptions import ClientError
from src.logging_config import logger

_NOTIFY_INTERVAL_DAYS = 7
_STATE_KEY_TEMPLATE = "{prefix}/champs_id_warnings_state.json"

_warnings: list[dict] = []


def record_champs_id_warning(site_id: str, champs_id: str, report_count: int) -> None:
    """Accumulate an invalid-ChampsId warning for the current pipeline run."""
    _warnings.append({
        "SiteId": site_id,
        "ChampsId": champs_id,
        "ReportCount": report_count,
    })


def _merge_warnings(existing: list[dict], new: list[dict]) -> list[dict]:
    """Merge new warnings into existing, summing ReportCount for duplicates."""
    index = {(w["SiteId"], w["ChampsId"]): w for w in existing}
    for w in new:
        key = (w["SiteId"], w["ChampsId"])
        if key in index:
            index[key]["ReportCount"] += w["ReportCount"]
        else:
            index[key] = dict(w)
    return list(index.values())


def _read_state(s3, bucket: str, key: str) -> dict:
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        return json.loads(obj["Body"].read())
    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
            return {}
        raise


def _write_state(s3, bucket: str, key: str, state: dict) -> None:
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(state, indent=2),
        ContentType="application/json",
    )


def _format_slack_message(warnings: list[dict], week_of: str) -> str:
    rows = "\n".join(
        f"  • `{w['ChampsId']}` (SiteId: {w['SiteId']}, Reports: {w['ReportCount']})"
        for w in sorted(warnings, key=lambda x: (x["SiteId"], x["ChampsId"]))
    )
    return (
        f":warning: *HIV ETL — ChampsId Data Quality Digest* (week of {week_of})\n\n"
        f"The following invalid ChampsIds were detected and *excluded* from staging.\n"
        f"Please correct in REDCap. Valid format: 4 letters + 5 digits (e.g. `MZHA00001`)\n\n"
        f"{rows}"
    )


def flush_champs_id_warnings(env: str, bucket: str, prefix: str) -> None:
    """
    At end of pipeline run: accumulate warnings into S3 state.
    If last Slack notification was >=7 days ago (or never), post digest and reset.
    No-op if no warnings were recorded this run.
    """
    if not _warnings:
        return

    from include.ci_slack import post_mesg_channel

    s3 = boto3.client("s3")
    state_key = _STATE_KEY_TEMPLATE.format(prefix=prefix)
    today = datetime.date.today()

    state = _read_state(s3, bucket, state_key)
    last_notified_str = state.get("last_notified")
    accumulated = state.get("warnings", [])

    merged = _merge_warnings(accumulated, _warnings)

    should_notify = True
    if last_notified_str:
        last_notified = datetime.date.fromisoformat(last_notified_str)
        should_notify = (today - last_notified).days >= _NOTIFY_INTERVAL_DAYS

    if should_notify:
        message = _format_slack_message(merged, str(today))
        post_mesg_channel(text=message, channel="#logs")
        logger.info(f"Posted ChampsId DQ digest to Slack ({len(merged)} unique invalid IDs)")
        new_state = {"last_notified": str(today), "warnings": []}
    else:
        logger.info(
            f"ChampsId DQ warnings accumulated ({len(merged)} total). "
            f"Next Slack digest in {_NOTIFY_INTERVAL_DAYS - (today - datetime.date.fromisoformat(last_notified_str)).days} day(s)."
        )
        new_state = {"last_notified": last_notified_str, "warnings": merged}

    _write_state(s3, bucket, state_key, new_state)
    _warnings.clear()
