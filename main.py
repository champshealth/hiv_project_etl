import os
import subprocess
import datetime
from config.config import (REDCAP_11_TOKENS, REDCAP_31_TOKENS, REDCAP_CA_TOKENS, REDCAP_61_TOKENS, 
                     REDCAP_API_TOKEN_31, REDCAP_API_TOKEN_CA, REDCAP_EXPORT_FILE_11, 
                     REDCAP_EXPORT_FILE_31, REDCAP_EXPORT_FILE_CA, REDCAP_EXPORT_FILE_61, ENV)
from src.redcap_api_export import redcap_api_export
from src.logging_config import logger
from src.db_load_project_1_1 import db_load_project_1_1
from src.db_load_project_3_1 import db_load_project_3_1
from src.db_load_project_6_1 import db_load_project_6_1
from src.db_upsert_consent_data import upsert_consent_records
from src.db_upsert_mits_proc_data import upsert_mits_proc_data
from src.db_upsert_death_notif_data import upsert_death_notif_data
from src.db_upsert_mits_specimen_collect import upsert_mits_specimen_collect
from src.db_load_abstraction import db_load_clinical_abstraction
from src.db_upsert_cplwidget_data import upsert_cpl_widget_aggregate
from src.log_checker import check_log_and_notify

if __name__ == '__main__':
    logger.info('Starting main script')
    try:
        logger.info('Starting redcap_api_export.py')
        df = redcap_api_export(REDCAP_11_TOKENS, REDCAP_EXPORT_FILE_11)
        logger.info('Finished redcap_api_export.py')
        if not df.empty:
            # print(df.shape)
            df2 = db_load_project_1_1(df=df)

            # del df

            # 3.1 data load and upsert
            # FUTURE state will use REDCAP_31_TOKENS
            df = redcap_api_export(REDCAP_31_TOKENS, REDCAP_EXPORT_FILE_31)
            db_load_project_3_1(df=df)


            # clinical abstraction data load
            df = redcap_api_export(REDCAP_CA_TOKENS, REDCAP_EXPORT_FILE_CA)
            db_load_clinical_abstraction(df=df)
            
            # project 6.1 data load
            df = redcap_api_export(REDCAP_61_TOKENS, REDCAP_EXPORT_FILE_61)
            db_load_project_6_1(df=df)

            # run dbt step to load the data into the hiv schema
            # Run dbt commands in the dbt project directory as a subprocess
            dbt_project_dir = "dbt/hiv_project"

            process = subprocess.run(
                ["dbt", "run", "--target", ENV],
                cwd=dbt_project_dir,
                capture_output=True,
                text=True
            )
            # check for any errors in the dbt run
            if process.returncode != 0:
                # Get both stderr and stdout since DBT writes error details to stdout
                error_output = process.stderr
                stdout_output = process.stdout

                # Extract the last 15 lines from stdout for error details
                stdout_lines = stdout_output.splitlines()
                if stdout_lines:
                    last_lines = '\n'.join(stdout_lines[-15:]) if len(stdout_lines) > 15 else stdout_output
                    logger.error(f"DBT run failed with error. Last lines from output:\n{last_lines}")
                    logger.error(f"stderr output: {error_output}")
                    raise Exception(f"DBT run failed. Error details: {last_lines}")
                else:
                    logger.error(f"DBT run failed with error:\n{error_output}")
                    raise Exception(f"DBT run failed with error:\n{error_output}")
            else:
                success_output = process.stdout
                logger.info(f"DBT run completed successfully with output:\n{success_output}")

            upsert_consent_records()
            upsert_death_notif_data()
            upsert_mits_proc_data()
            upsert_mits_specimen_collect()

            # CPL Widget upsert
            upsert_cpl_widget_aggregate()

        logger.info('Finished main script')
        check_log_and_notify()
    except Exception as e:
        logger.error(f'ERROR: {e}')
        check_log_and_notify()
        raise e