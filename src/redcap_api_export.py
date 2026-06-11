import os
import gc
import tempfile
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import duckdb
from config.config import REDCAP_URL
from requests.exceptions import RequestException
from src.logging_config import logger


def _get_eav_columns(flat_df):
    columns = ['record', 'field_name', 'value']
    has_repeat_instrument = 'redcap_repeat_instrument' in flat_df.columns
    has_repeat_instance = 'redcap_repeat_instance' in flat_df.columns
    has_site_id = 'site_id' in flat_df.columns

    if has_site_id:
        columns.insert(1, 'site_id')
    if has_repeat_instrument:
        idx = 1 if not has_site_id else 2
        columns.insert(idx, 'redcap_repeat_instrument')
    if has_repeat_instance:
        idx = 1
        if has_site_id:
            idx += 1
        if has_repeat_instrument:
            idx += 1
        columns.insert(idx, 'redcap_repeat_instance')

    return columns, has_site_id, has_repeat_instrument, has_repeat_instance


def _process_flat_chunk(flat_df, record_id_col, columns, has_site_id,
                        has_repeat_instrument, has_repeat_instance):
    conn = duckdb.connect()
    try:
        conn.execute("CREATE TEMPORARY TABLE t AS SELECT * FROM flat_df")

        id_cols = [f'"{record_id_col}" AS record']
        if has_site_id:
            id_cols.append('"site_id"')
        if has_repeat_instrument:
            id_cols.append('redcap_repeat_instrument')
        if has_repeat_instance:
            id_cols.append('redcap_repeat_instance')

        exclude_cols = [record_id_col, 'site_id', 'redcap_repeat_instrument',
                        'redcap_repeat_instance']
        field_cols = [c for c in flat_df.columns if c not in exclude_cols]

        unpivot_query = f"""
            SELECT
                {', '.join(id_cols)},
                field_name,
                value::VARCHAR as value
            FROM t
            UNPIVOT (
                value FOR field_name IN ({', '.join([f'"{c}"' for c in field_cols])})
            )
            WHERE value IS NOT NULL AND TRIM(value::VARCHAR) != ''
        """

        eav_df = conn.execute(unpivot_query).fetchdf()

        if not eav_df.empty:
            checkbox_mask = eav_df['field_name'].str.contains('___', na=False)
            if checkbox_mask.any():
                cb = eav_df[checkbox_mask].copy()
                non_cb = eav_df[~checkbox_mask]
                cb.loc[cb['value'] == '1', 'value'] = \
                    cb.loc[cb['value'] == '1', 'field_name'].str.extract(r'___(.+)$')[0]
                cb['field_name'] = cb['field_name'].str.replace(r'___.*$', '', regex=True)
                cb = cb[cb['value'] != '0']
                eav_df = pd.concat([non_cb, cb], ignore_index=True)

        eav_df = eav_df[columns]
        for col in eav_df.columns:
            eav_df[col] = eav_df[col].astype(str)

        return eav_df
    finally:
        conn.close()


def _promote_site_id(eav_df):
    if 'site_id' in eav_df.columns:
        return eav_df
    site_rows = eav_df[eav_df['field_name'] == 'site_id'].copy()
    if site_rows.empty:
        return eav_df
    site_map = site_rows.set_index('record')['value'].to_dict()
    eav_df = eav_df[eav_df['field_name'] != 'site_id']
    eav_df.insert(1, 'site_id', eav_df['record'].map(site_map).fillna(''))
    return eav_df


def _stringify(records):
    for record in records:
        for key, value in record.items():
            if value is not None:
                record[key] = str(value)


def redcap_api_export(redcap_tokens, output_file, use_eav=True):
    if redcap_tokens and isinstance(redcap_tokens[0], list):
        redcap_tokens = [t for sublist in redcap_tokens for t in sublist]

    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    all_dfs = []
    skip_projects = []

    for token_info in redcap_tokens:
        project_name = token_info['name']
        if project_name in skip_projects:
            logger.warning(f"Skipping known problematic project: {project_name}")
            continue

        token = str(token_info['token'])

        try:
            if use_eav:
                data = {
                    'token': token, 'content': 'record', 'action': 'export',
                    'format': 'json', 'type': 'eav', 'rawOrLabel': 'raw',
                    'rawOrLabelHeaders': 'raw', 'exportCheckboxLabel': 'true',
                    'exportSurveyFields': 'false', 'exportDataAccessGroups': 'false',
                    'returnFormat': 'json',
                }
                resp = session.post(REDCAP_URL, data=data, timeout=(10, 300))
                resp.raise_for_status()
                records = resp.json()
                if not records:
                    continue
                _stringify(records)
                df = pd.DataFrame(records)
                df = _promote_site_id(df)
                if project_name == "south_africa" and 'site_id' not in df.columns:
                    df.insert(1, 'site_id', '001')
                all_dfs.append(df)
                logger.info(f"Fetched {len(df)} EAV rows for {project_name}")
            else:
                page = 1
                page_size = 5000
                temp_dir = tempfile.mkdtemp(prefix="redcap_eav_")
                part_files = []
                try:
                    while True:
                        data = {
                            'token': token, 'content': 'record', 'action': 'export',
                            'format': 'json', 'type': 'flat', 'rawOrLabel': 'raw',
                            'rawOrLabelHeaders': 'raw', 'exportCheckboxLabel': 'true',
                            'exportSurveyFields': 'false', 'exportDataAccessGroups': 'false',
                            'returnFormat': 'json', 'page': page, 'pageSize': page_size,
                        }
                        resp = session.post(REDCAP_URL, data=data, timeout=(10, 300))
                        resp.raise_for_status()
                        records = resp.json()
                        if not records:
                            break

                        _stringify(records)
                        flat_df = pd.DataFrame(records)

                        if project_name == "south_africa" and output_file.endswith("redcap_export_11"):
                            if 'site_id' not in flat_df.columns:
                                flat_df['site_id'] = "001"
                            else:
                                flat_df['site_id'] = "001"

                        columns, has_site_id, has_repeat_instrument, has_repeat_instance = \
                            _get_eav_columns(flat_df)
                        eav_df = _process_flat_chunk(
                            flat_df, flat_df.columns[0],
                            columns, has_site_id,
                            has_repeat_instrument, has_repeat_instance
                        )

                        part_path = os.path.join(temp_dir, f"part_{page:04d}.parquet")
                        eav_df.to_parquet(part_path, index=False)
                        part_files.append(part_path)
                        logger.info(f"Page {page}: {len(flat_df)} flat -> {len(eav_df)} EAV rows")

                        del flat_df, eav_df, records
                        gc.collect()
                        page += 1

                    if part_files:
                        dfs = [pd.read_parquet(p) for p in part_files]
                        df = pd.concat(dfs, ignore_index=True)
                        all_dfs.append(df)
                        logger.info(f"Fetched {len(df)} total EAV rows for {project_name}")
                finally:
                    for p in part_files:
                        try: os.remove(p)
                        except OSError: pass
                    try: os.rmdir(temp_dir)
                    except OSError: pass

        except RequestException as e:
            logger.error(f"Error fetching {project_name}: {e}")
            continue

    if not all_dfs:
        return None

    final_df = pd.concat(all_dfs, ignore_index=True)

    if 'redcap_repeat_instance' in final_df.columns:
        final_df['redcap_repeat_instance'] = final_df['redcap_repeat_instance'].astype(str)

    final_df.to_csv(output_file + ".csv", index=False)
    try:
        final_df.to_parquet(output_file + ".parquet", index=False)
    except Exception as e:
        logger.warning(f"Error writing parquet: {e}")

    return final_df


def _fetch_record_ids(session, token):
    """Fetch only the record ID column to minimize memory."""
    meta_data = {
        'token': token, 'content': 'metadata', 'format': 'json', 'returnFormat': 'json'
    }
    resp = session.post(REDCAP_URL, data=meta_data, timeout=30)
    resp.raise_for_status()
    fields = resp.json()
    record_id_field = fields[0]['field_name']

    id_data = {
        'token': token, 'content': 'record', 'action': 'export',
        'format': 'json', 'type': 'flat', 'fields[0]': record_id_field,
        'rawOrLabel': 'raw', 'exportSurveyFields': 'false',
        'exportDataAccessGroups': 'false', 'returnFormat': 'json'
    }
    resp = session.post(REDCAP_URL, data=id_data, timeout=(30, 600))
    resp.raise_for_status()
    records = resp.json()
    ids = [r[record_id_field] for r in records]
    logger.info(f"Fetched {len(ids)} record IDs (field: {record_id_field})")
    return ids, record_id_field


def redcap_export_flat_partitioned(redcap_tokens, output_dir, batch_size=50):
    """Export flat-mode data partitioned by record ID for memory efficiency.
    Returns list of parquet file paths."""
    if redcap_tokens and isinstance(redcap_tokens[0], list):
        redcap_tokens = [t for sublist in redcap_tokens for t in sublist]

    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    os.makedirs(output_dir, exist_ok=True)
    part_files = []

    for token_info in redcap_tokens:
        project_name = token_info['name']
        token = str(token_info['token'])

        all_ids, record_id_field = _fetch_record_ids(session, token)

        batches = [all_ids[i:i+batch_size] for i in range(0, len(all_ids), batch_size)]
        logger.info(f"Partitioned {len(all_ids)} records into {len(batches)} batches of {batch_size}")

        for batch_num, batch_ids in enumerate(batches):
            data = {
                'token': token, 'content': 'record', 'action': 'export',
                'format': 'json', 'type': 'flat', 'rawOrLabel': 'raw',
                'rawOrLabelHeaders': 'raw', 'exportCheckboxLabel': 'true',
                'exportSurveyFields': 'false', 'exportDataAccessGroups': 'false',
                'returnFormat': 'json',
            }
            for i, rid in enumerate(batch_ids):
                data[f'records[{i}]'] = rid

            resp = session.post(REDCAP_URL, data=data, timeout=(30, 600))
            resp.raise_for_status()
            records = resp.json()
            if not records:
                continue

            _stringify(records)
            flat_df = pd.DataFrame(records)

            columns, has_site_id, has_repeat_instrument, has_repeat_instance = \
                _get_eav_columns(flat_df)
            eav_df = _process_flat_chunk(
                flat_df, flat_df.columns[0],
                columns, has_site_id,
                has_repeat_instrument, has_repeat_instance
            )

            part_path = os.path.join(output_dir, f"{project_name}_b{batch_num:04d}.parquet")
            eav_df.to_parquet(part_path, index=False)
            part_files.append(part_path)
            logger.info(f"Batch {batch_num+1}/{len(batches)}: {len(flat_df)} flat -> {len(eav_df)} EAV rows")

            del flat_df, eav_df, records
            gc.collect()

        logger.info(f"Export complete for {project_name}: {len(batches)} batches")

    session.close()
    return sorted(part_files)
