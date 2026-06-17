"""Standalone test script for upsert_consent_auth_records.

Runs the consent authorization upsert in isolation against a non-production database
without triggering the full pipeline.

Usage:
    uv run python scripts/test_consent_auth_upsert.py --env dev --dry-run   # diagnostics only
    uv run python scripts/test_consent_auth_upsert.py --env dev             # full upsert
    uv run python scripts/test_consent_auth_upsert.py --env stg
"""
import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sqlalchemy as sa
from sqlalchemy import text as sa_text
from include.ci_utils import get_engine

CONSENT_AUTH_VIEW_NAME = 'vw_HIVConsentAuthorization'
SCHEMA_NAME = os.environ.get('DB_SCHEMA', 'hiv')

_ENV_MAP = {
    "dev": lambda: get_engine("dev"),
    "stg": lambda: get_engine("stg"),
    "prod": lambda: get_engine("prod"),
}


def run_preflight_diagnostics(engine: sa.engine.Engine) -> None:
    """Run read-only diagnostic queries before the upsert."""
    print("\n=== Pre-flight Diagnostics ===")

    view_count_sql = sa_text(
        f"SELECT COUNT(*) FROM {SCHEMA_NAME}.{CONSENT_AUTH_VIEW_NAME}"
    )
    view_sample_sql = sa_text(f"""
        SELECT TOP 5
            AuthId, ChampsId, SiteId, Protocol, ConsentType,
            AuthorizationCode, Action, EventDate, FileName
        FROM {SCHEMA_NAME}.{CONSENT_AUTH_VIEW_NAME}
    """)
    target_count_sql = sa_text("""
        SELECT COUNT(*) FROM dbo.ConsentAuthorization
        WHERE FileName = 'adult_hiv_study' AND Active = 1
    """)
    index_sql = sa_text("""
        SELECT
            i.name AS index_name,
            i.type_desc,
            STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS columns
        FROM sys.indexes i
        JOIN sys.tables t ON i.object_id = t.object_id
        JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
        JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE t.name = 'ConsentAuthorization'
          AND i.type > 0
        GROUP BY i.name, i.type_desc
        ORDER BY i.name
    """)

    with engine.connect() as conn:
        print(f"\n[Source View] Counting rows in {SCHEMA_NAME}.{CONSENT_AUTH_VIEW_NAME}...")
        t0 = time.perf_counter()
        view_count = conn.execute(view_count_sql).scalar()
        elapsed = time.perf_counter() - t0
        print(f"  Row count : {view_count:,}")
        print(f"  Elapsed   : {elapsed:.2f}s")

        print("\n[Source View] Sample rows (top 5):")
        rows = conn.execute(view_sample_sql).fetchall()
        if rows:
            for row in rows:
                print(f"  AuthId={row.AuthId}  ChampsId={row.ChampsId}  "
                      f"ConsentType={row.ConsentType}  EventDate={row.EventDate}")
        else:
            print("  (no rows returned)")

        print("\n[Target Table] Active rows in dbo.ConsentAuthorization (FileName='adult_hiv_study', Active=1):")
        target_count = conn.execute(target_count_sql).scalar()
        print(f"  Row count : {target_count:,}")

        print("\n[Indexes] ConsentAuthorization indexes:")
        idx_rows = conn.execute(index_sql).fetchall()
        if idx_rows:
            for row in idx_rows:
                print(f"  {row.index_name:<55} ({row.columns})")
        else:
            print("  No indexes found.")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test upsert_consent_auth_records against non-prod DB."
    )
    parser.add_argument(
        "--env",
        choices=list(_ENV_MAP.keys()),
        default="dev",
        help="Target environment: 'dev' (default), 'stg', or 'prod'",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run diagnostics only — skip the upsert write",
    )
    args = parser.parse_args()

    engine = _ENV_MAP[args.env]()
    print(f"Target environment : {args.env.upper()}")
    print(f"Schema             : {SCHEMA_NAME}")
    print(f"Source view        : {CONSENT_AUTH_VIEW_NAME}")

    run_preflight_diagnostics(engine)

    if args.dry_run:
        print("=== Dry run — skipping upsert. ===")
        return

    from src.db_upsert_consent_auth import upsert_consent_auth_records
    print("=== Running upsert_consent_auth_records ===")
    t_start = time.perf_counter()
    upsert_consent_auth_records(conn_override=engine)
    total_elapsed = time.perf_counter() - t_start
    print(f"\nTotal elapsed: {total_elapsed:.2f}s")
    print("Done.")


if __name__ == "__main__":
    main()
