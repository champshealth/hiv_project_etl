import sqlalchemy as sa
from src.logging_config import logger
from config.config import CONN, CONSENT_AUTH_VIEW_NAME, DB_SCHEMA as SCHEMA_NAME, ETL_USER_ID, JOB_ID


def upsert_consent_auth_records(conn_override: sa.engine.Engine = None) -> None:
    """Upsert ConsentAuthorization records from the consent authorization source view.

    Args:
        conn_override: Optional SQLAlchemy engine to use instead of the default CONN.
                       Useful for testing against non-production databases.
    """
    engine = conn_override if conn_override is not None else CONN
    logger.info('Starting upsert_consent_auth_records')
    try:
        materialize_sql = sa.text(f"""
        IF OBJECT_ID('tempdb..#tmp_consent_auth') IS NOT NULL
            DROP TABLE #tmp_consent_auth;
        SELECT * INTO #tmp_consent_auth
        FROM {SCHEMA_NAME}.{CONSENT_AUTH_VIEW_NAME};
        """)

        merge_sql = sa.text(f"""
        MERGE INTO dbo.ConsentAuthorization AS Target
        USING #tmp_consent_auth AS Source
        ON (
            Target.AuthId              = Source.AuthId
            AND Target.ChampsId        = Source.ChampsId
            AND Target.Protocol        = Source.Protocol
            AND Target.ConsentType     = Source.ConsentType
            AND Target.AuthorizationCode = Source.AuthorizationCode
        )
        WHEN MATCHED AND Target.[HASH] != CONVERT(nvarchar(32), hashbytes('MD5', UPPER(
                ISNULL(Source.AuthId,'') + ISNULL(Source.ChampsId,'') + ISNULL(Source.Action,'') +
                ISNULL(Source.Protocol,'') + ISNULL(Source.ConsentType,'') + ISNULL(Source.AuthorizationCode,'') +
                '' + '' + '' + '' + '' +
                ISNULL(CONVERT(nvarchar(32), Source.EventDate, 127),'')
            )), 2) THEN
            UPDATE SET
                Target.Action = Source.Action,
                Target.EventDate = Source.EventDate,
                Target.VersionOfDataSpecification = Source.VersionOfDataSpecification,
                Target.ModifiedOn = Source.ModifiedOn,
                Target.UploadedOn = Source.UploadedOn,
                Target.ModifiedBy = '{ETL_USER_ID}'
        WHEN NOT MATCHED THEN
            INSERT (
                Id, JobId, AuthId, ChampsId, SiteId,
                Protocol, ConsentType, AuthorizationCode, Action,
                Active, Valid, VersionOfDataSpecification,
                EventDate, FileName,
                CreatedOn, ModifiedOn, UploadedOn,
                CreatedBy, UploadedBy
            )
            VALUES (
                Source.Id, '{JOB_ID}', Source.AuthId, Source.ChampsId, Source.SiteId,
                Source.Protocol, Source.ConsentType, Source.AuthorizationCode, Source.Action,
                Source.Active, Source.Valid, Source.VersionOfDataSpecification,
                Source.EventDate, Source.FileName,
                Source.CreatedOn, Source.ModifiedOn, Source.UploadedOn,
                '{ETL_USER_ID}', '{ETL_USER_ID}'
            )
        ;
        """)

        deactivate_deleted_sql = sa.text(f"""
        UPDATE dbo.ConsentAuthorization
        SET Active = 2,
            ModifiedOn = GETDATE(),
            ModifiedBy = '{ETL_USER_ID}'
        WHERE FileName = 'adult_hiv_study'
        AND Active = 1
        AND NOT EXISTS (
            SELECT 1 FROM #tmp_consent_auth t
            WHERE t.AuthId = ConsentAuthorization.AuthId
            AND t.ChampsId = ConsentAuthorization.ChampsId
            AND t.Protocol = ConsentAuthorization.Protocol
            AND t.ConsentType = ConsentAuthorization.ConsentType
            AND t.AuthorizationCode = ConsentAuthorization.AuthorizationCode
        )
        """)

        with engine.connect() as conn:
            conn.execute(materialize_sql)
            result = conn.execute(merge_sql)
            conn.commit()
            result_deactivate = conn.execute(deactivate_deleted_sql)
            conn.commit()
            logger.info(f"Merged {result.rowcount} rows into ConsentAuthorization")
            logger.info(f"Deactivated {result_deactivate.rowcount} rows not found in source")

        logger.info('Finished upsert_consent_auth_records')

    except Exception as e:
        logger.error(f"Error in upsert_consent_auth_records: {e}")
        raise e
