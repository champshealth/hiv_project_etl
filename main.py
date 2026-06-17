import os
import subprocess
import datetime
from config.config import (REDCAP_11_TOKENS, REDCAP_31_TOKENS, REDCAP_CA_TOKENS, REDCAP_61_TOKENS, 
                     REDCAP_EXPORT_FILE_11, REDCAP_EXPORT_FILE_31, REDCAP_EXPORT_FILE_CA, 
                     REDCAP_EXPORT_FILE_61, ENV, ETL_ARTIFACTS_BUCKET, ETL_ARTIFACTS_PREFIX)
import tempfile
import gc
from src.redcap_api_export import redcap_api_export, redcap_export_flat_partitioned
from src.logging_config import logger
from src.db_load_project_1_1 import db_load_project_1_1
from src.db_load_project_3_1 import db_load_project_3_1
from src.db_load_project_6_1 import db_load_project_6_1
from src.db_upsert_consent_data import upsert_consent_records
from src.db_upsert_consent_auth import upsert_consent_auth_records
from src.db_upsert_mits_proc_data import upsert_mits_proc_data
from src.db_upsert_death_notif_data import upsert_death_notif_data
from src.db_upsert_mits_specimen_collect import upsert_mits_specimen_collect
from src.db_load_abstraction import db_load_clinical_abstraction
from src.db_upsert_cplwidget_data import upsert_cpl_widget_aggregate
from src.log_checker import check_log_and_notify
from src.data_quality import flush_champs_id_warnings

def _export_db_creds():
    from include.aws_secrets import get_db_credentials
    _dbc = get_db_credentials(ENV)
    os.environ['DB_HOST'] = _dbc['host']
    os.environ['DB_PORT'] = str(_dbc.get('port', 1433))
    os.environ['DB_NAME'] = _dbc['database']
    os.environ['DB_USER'] = _dbc['username']
    os.environ['DB_PASSWORD'] = _dbc['password']


def _run_dbt():
    dbt_project_dir = "dbt/hiv_project"
    _uv = "/root/.local/bin/uv" if os.path.exists("/root/.local/bin/uv") else "uv"

    lock_file = os.path.join(dbt_project_dir, "package-lock.yml")
    packages_file = os.path.join(dbt_project_dir, "packages.yml")
    needs_deps = not os.path.exists(lock_file) or (
        os.path.exists(packages_file) and
        os.path.getmtime(packages_file) > os.path.getmtime(lock_file)
    )
    if needs_deps:
        deps = subprocess.run(
            [_uv, "run", "dbt", "deps", "--profiles-dir", "."],
            cwd=dbt_project_dir, capture_output=True, text=True,
        )
        if deps.returncode != 0:
            logger.error(f"dbt deps failed: {deps.stderr}")
            raise Exception(f"dbt deps failed: {deps.stderr}")
    else:
        logger.info("dbt packages are up to date, skipping dbt deps")

    process = subprocess.run(
        [_uv, "run", "dbt", "run", "--profiles-dir", ".", "--target", ENV],
        cwd=dbt_project_dir,
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        error_output = process.stderr
        stdout_output = process.stdout
        stdout_lines = stdout_output.splitlines()
        if stdout_lines:
            last_lines = (
                '\n'.join(stdout_lines[-15:])
                if len(stdout_lines) > 15
                else stdout_output
            )
            logger.error(f"DBT run failed with error. Last lines from output:\n{last_lines}")
            logger.error(f"stderr output: {error_output}")
            raise Exception(f"DBT run failed. Error details: {last_lines}")
        else:
            logger.error(f"DBT run failed with error:\n{error_output}")
            raise Exception(f"DBT run failed with error:\n{error_output}")
    else:
        logger.info(f"DBT run completed successfully:\n{process.stdout}")


if __name__ == '__main__':
    from include.ci_slack import post_mesg

    step = int(os.environ.get('STEP', '0'))

    logger.info('Starting main script (step=%d)', step)
    try:
        if step == 0 or step == 1:
            logger.info('Starting redcap_api_export.py')
            df = redcap_api_export(REDCAP_11_TOKENS, REDCAP_EXPORT_FILE_11, use_eav=True)
            logger.info('Finished redcap_api_export.py')
            if df is not None and not df.empty:
                df2 = db_load_project_1_1(df=df)

                _tmpdir = tempfile.mkdtemp(prefix="redcap_31_eav_")
                part_files = []
                try:
                    part_files = redcap_export_flat_partitioned(REDCAP_31_TOKENS, _tmpdir)
                    db_load_project_3_1(parquet_files=part_files)
                finally:
                    for f in part_files:
                        try: os.remove(f)
                        except OSError: pass
                    try: os.rmdir(_tmpdir)
                    except OSError: pass
                    del part_files
                gc.collect()

                df = redcap_api_export(REDCAP_CA_TOKENS, REDCAP_EXPORT_FILE_CA, use_eav=True)
                db_load_clinical_abstraction(df=df)

                df = redcap_api_export(REDCAP_61_TOKENS, REDCAP_EXPORT_FILE_61, use_eav=True)
                db_load_project_6_1(df=df)

        if step == 0 or step == 2:
            _export_db_creds()
            _run_dbt()

        if step == 0 or step == 3:
            upsert_consent_records()
            upsert_consent_auth_records()
            upsert_death_notif_data()
            upsert_mits_proc_data()
            upsert_mits_specimen_collect()
            upsert_cpl_widget_aggregate()

        logger.info('Finished main script')
        flush_champs_id_warnings(env=ENV, bucket=ETL_ARTIFACTS_BUCKET, prefix=ETL_ARTIFACTS_PREFIX)
        check_log_and_notify()
        post_mesg(f"✅ ETL pipeline ({ENV}) completed successfully")
    except Exception as e:
        logger.error(f'ERROR: {e}')
        check_log_and_notify()
        post_mesg(f"❌ ETL pipeline ({ENV}) failed: {e}")
        raise e