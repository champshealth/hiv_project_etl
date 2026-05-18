"""Standalone test script for upsert_cpl_widget_aggregate.

Runs the optimized upsert in isolation against a non-production database
(stg or qa) without triggering the full pipeline.

Usage:
    uv run scripts/test_cplwidget_upsert.py --env stg   # targets conn_stg (default)
    uv run scripts/test_cplwidget_upsert.py --env qa    # targets conn_qa
"""
import argparse
import sys
import time
import os
from pathlib import Path

# Allow imports from the project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sqlalchemy as sa
from sqlalchemy import text as sa_text
from include.ci_utils_local import connect_db
from config.config import CPL_WIDGET_VIEW_NAME, DB_SCHEMA as SCHEMA_NAME
from src.db_upsert_cplwidget_data import upsert_cpl_widget_aggregate


_ENV_MAP = {
    "stg": connect_db.conn_stg,
    "qa": connect_db.conn_qa,
    "prod": connect_db.conn_prod,
}


def run_preflight_diagnostics(engine: sa.engine.Engine) -> None:
    """Run read-only diagnostic queries before the upsert and print results.

    Checks:
    - Row count of the source view (confirms view resolves and shows volume).
    - Existing indexes on both target tables.

    Args:
        engine: SQLAlchemy engine pointed at the target database.
    """
    print("\n=== Pre-flight Diagnostics ===")

    view_count_sql = sa_text(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.{CPL_WIDGET_VIEW_NAME}")
    index_sql = sa_text("""
        SELECT
            t.name AS table_name,
            i.name AS index_name,
            i.type_desc,
            STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS columns
        FROM sys.indexes i
        JOIN sys.tables t ON i.object_id = t.object_id
        JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
        JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE t.name IN ('CPLWidgetAggregate', 'CPLDetailWidgetAggregate')
          AND i.type > 0  -- exclude heaps
        GROUP BY t.name, i.name, i.type_desc
        ORDER BY t.name, i.name
    """)

    with engine.connect() as conn:
        print(f"\n[Source View] Counting rows in {SCHEMA_NAME}.{CPL_WIDGET_VIEW_NAME}...")
        t0 = time.perf_counter()
        row_count = conn.execute(view_count_sql).scalar()
        elapsed = time.perf_counter() - t0
        print(f"  Row count : {row_count:,}")
        print(f"  Elapsed   : {elapsed:.2f}s")

        print("\n[Indexes] Target table indexes:")
        rows = conn.execute(index_sql).fetchall()
        if rows:
            for row in rows:
                print(f"  {row.table_name:<35} {row.index_name:<50} ({row.columns})")
        else:
            print("  No indexes found on target tables.")

    print()


def main() -> None:
    """Parse args, run diagnostics, then execute the optimized upsert."""
    parser = argparse.ArgumentParser(description="Test upsert_cpl_widget_aggregate against non-prod DB.")
    parser.add_argument(
        "--env",
        choices=list(_ENV_MAP.keys()),
        default="stg",
        help="Target environment: 'stg' (default), 'qa', or 'prod'",
    )
    args = parser.parse_args()

    engine = _ENV_MAP[args.env]
    print(f"Target environment : {args.env.upper()}")
    print(f"Schema             : {SCHEMA_NAME}")
    print(f"Source view        : {CPL_WIDGET_VIEW_NAME}")

    run_preflight_diagnostics(engine)

    print("=== Running upsert_cpl_widget_aggregate ===")
    t_start = time.perf_counter()
    upsert_cpl_widget_aggregate(conn_override=engine)
    total_elapsed = time.perf_counter() - t_start
    print(f"\nTotal elapsed: {total_elapsed:.2f}s")
    print("Done.")


if __name__ == "__main__":
    main()
