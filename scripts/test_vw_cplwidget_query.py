"""Benchmark and validation script for vw_HIVCPLWidgetAggregate query optimization.

Runs both the ORIGINAL and OPTIMIZED query SQL directly against the database
(bypassing dbt) and compares:
  - Row counts (must match)
  - Per-column NULL counts (should match)
  - Elapsed time

Usage:
    python scripts/test_vw_cplwidget_query.py --env qa
    python scripts/test_vw_cplwidget_query.py --env prod
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sqlalchemy as sa
from sqlalchemy import text as sa_text
from include.ci_utils_local import connect_db

_ENV_MAP = {
    "stg": connect_db.conn_stg,
    "qa": connect_db.conn_qa,
    "prod": connect_db.conn_prod,
}

# ---------------------------------------------------------------------------
# ORIGINAL query — two separate LEFT JOINs on vw_HIVProject3_1_rpt
# ---------------------------------------------------------------------------
ORIGINAL_SQL = """
SELECT 
    ct.ChampsId,
    dn.ReportId,
    dn.CatchmentId,
    DateOfDeathNotification,
    DATEDIFF(day, DateOfDeathNotification, getdate()) as DaysSinceDeathNotification,
    DeathNotificationSiteId,
    getdate() as DemographicsModifiedOn,
    mproc.CreatedOn as MITSProcedureModifiedOn,
    ca.CreatedOn as ChildAbstractionModifiedOn,
    sp.SitePathDiagModifiedOn,
    sp.SitePathFindingModifiedOn,
    sp.SitePathTissueModifiedOn,
    lab_placenta.LaboratoryResultsModifiedOn,
    lab_placenta.PlacentaExaminationModifiedOn,
    dn.SiteId as SiteGuid,
    Site.Name as SiteName
FROM hiv.vw_HIVDeathNotification dn
JOIN dbo.Site ON dn.SiteId = Site.Id
JOIN dbo.ConsentTracking ct ON dn.ReportId = ct.ReportId 
    AND ct.Active = 1 
    AND dn.SiteId = ct.SiteId
    AND dn.CatchmentId = ct.CatchmentId
LEFT JOIN (
    SELECT ChampsId, MAX(CAST(CreatedOn AS date)) AS CreatedOn
    FROM hiv.HIVClinicalAbstract
    GROUP BY ChampsId
) ca ON ct.ChampsId = ca.ChampsId
LEFT JOIN (
    SELECT [SiteId], [ChampsId], [FileName], CAST(CreatedOn AS date) CreatedOn
    FROM hiv.vw_HIVMitsProcedure
    WHERE SiteId IS NOT NULL
) mproc ON ct.ChampsId = mproc.ChampsId AND ct.[FileName] = mproc.[FileName]
LEFT JOIN (
    SELECT 
        ChampsId,
        FormName,  
        MAX(CAST(CreatedOn AS date)) AS SitePathDiagModifiedOn,
        MAX(CAST(CreatedOn AS date)) AS SitePathFindingModifiedOn,
        MAX(CAST(CreatedOn AS date)) AS SitePathTissueModifiedOn
    FROM hiv.vw_HIVProject3_1_rpt
    WHERE FormName = 'site_pathology_report'
    GROUP BY ChampsId, FormName
) sp ON ct.ChampsId = sp.ChampsId
LEFT JOIN (
    SELECT 
        ChampsId,
        MAX(CASE WHEN FormCategory = 'lab' THEN ModifiedDate END) AS LaboratoryResultsModifiedOn,
        MAX(CASE WHEN FormCategory = 'placenta' THEN ModifiedDate END) AS PlacentaExaminationModifiedOn
    FROM (
        SELECT 
            ChampsId,
            CASE 
                WHEN FormName IN ('ast','bld_microbiology_results','clinical_lab_results', 
                                  'csf_microbiology_results','lung_microbiology_results') THEN 'lab'
                WHEN FormName IN ('placenta_microscopic_examination','placenta_gross_examination') THEN 'placenta'
            END AS FormCategory,
            CAST(CreatedOn AS date) AS ModifiedDate
        FROM hiv.vw_HIVProject3_1_rpt
        WHERE FormName IN (
            'ast','bld_microbiology_results','clinical_lab_results',
            'csf_microbiology_results','lung_microbiology_results',
            'placenta_microscopic_examination','placenta_gross_examination'
        )
    ) src
    GROUP BY ChampsId
) lab_placenta ON ct.ChampsId = lab_placenta.ChampsId
"""

# ---------------------------------------------------------------------------
# OPTIMIZED query — single pass over vw_HIVProject3_1_rpt
# ---------------------------------------------------------------------------
OPTIMIZED_SQL = """
SELECT 
    ct.ChampsId,
    dn.ReportId,
    dn.CatchmentId,
    DateOfDeathNotification,
    DATEDIFF(day, DateOfDeathNotification, getdate()) as DaysSinceDeathNotification,
    DeathNotificationSiteId,
    getdate() as DemographicsModifiedOn,
    mproc.CreatedOn as MITSProcedureModifiedOn,
    ca.CreatedOn as ChildAbstractionModifiedOn,
    sp_lab.SitePathDiagModifiedOn,
    sp_lab.SitePathFindingModifiedOn,
    sp_lab.SitePathTissueModifiedOn,
    sp_lab.LaboratoryResultsModifiedOn,
    sp_lab.PlacentaExaminationModifiedOn,
    dn.SiteId as SiteGuid,
    Site.Name as SiteName
FROM hiv.vw_HIVDeathNotification dn
JOIN dbo.Site ON dn.SiteId = Site.Id
JOIN dbo.ConsentTracking ct ON dn.ReportId = ct.ReportId 
    AND ct.Active = 1 
    AND dn.SiteId = ct.SiteId
    AND dn.CatchmentId = ct.CatchmentId
LEFT JOIN (
    SELECT ChampsId, MAX(CAST(CreatedOn AS date)) AS CreatedOn
    FROM hiv.HIVClinicalAbstract
    GROUP BY ChampsId
) ca ON ct.ChampsId = ca.ChampsId
LEFT JOIN (
    SELECT [SiteId], [ChampsId], [FileName], CAST(CreatedOn AS date) CreatedOn
    FROM hiv.vw_HIVMitsProcedure
    WHERE SiteId IS NOT NULL
) mproc ON ct.ChampsId = mproc.ChampsId AND ct.[FileName] = mproc.[FileName]
LEFT JOIN (
    SELECT
        ChampsId,
        MAX(CASE WHEN FormName = 'site_pathology_report'   THEN CAST(CreatedOn AS date) END) AS SitePathDiagModifiedOn,
        MAX(CASE WHEN FormName = 'site_pathology_report'   THEN CAST(CreatedOn AS date) END) AS SitePathFindingModifiedOn,
        MAX(CASE WHEN FormName = 'site_pathology_report'   THEN CAST(CreatedOn AS date) END) AS SitePathTissueModifiedOn,
        MAX(CASE WHEN FormName IN ('ast','bld_microbiology_results','clinical_lab_results',
                                   'csf_microbiology_results','lung_microbiology_results')
                 THEN CAST(CreatedOn AS date) END) AS LaboratoryResultsModifiedOn,
        MAX(CASE WHEN FormName IN ('placenta_microscopic_examination','placenta_gross_examination')
                 THEN CAST(CreatedOn AS date) END) AS PlacentaExaminationModifiedOn
    FROM hiv.vw_HIVProject3_1_rpt
    WHERE FormName IN (
        'site_pathology_report',
        'ast','bld_microbiology_results','clinical_lab_results',
        'csf_microbiology_results','lung_microbiology_results',
        'placenta_microscopic_examination','placenta_gross_examination'
    )
    GROUP BY ChampsId
) sp_lab ON ct.ChampsId = sp_lab.ChampsId
"""

# columns to check NULL counts on for result validation
_NULLABLE_COLS = [
    "MITSProcedureModifiedOn",
    "ChildAbstractionModifiedOn",
    "SitePathDiagModifiedOn",
    "SitePathFindingModifiedOn",
    "SitePathTissueModifiedOn",
    "LaboratoryResultsModifiedOn",
    "PlacentaExaminationModifiedOn",
]


def run_query(engine: sa.engine.Engine, label: str, sql: str) -> tuple[int, dict, float]:
    """Execute the query, return (row_count, null_counts_per_col, elapsed_seconds).

    Args:
        engine: SQLAlchemy engine to use.
        label: Display label for progress output.
        sql: Raw T-SQL query string to execute.

    Returns:
        Tuple of (row_count, {col: null_count}, elapsed_seconds).
    """
    print(f"\n[{label}] Executing...")
    t0 = time.perf_counter()
    with engine.connect() as conn:
        rows = conn.execute(sa_text(sql)).fetchall()
    elapsed = time.perf_counter() - t0

    row_count = len(rows)
    null_counts: dict = {}
    if rows:
        col_names = list(rows[0]._fields)
        for col in _NULLABLE_COLS:
            if col in col_names:
                idx = col_names.index(col)
                null_counts[col] = sum(1 for r in rows if r[idx] is None)

    print(f"  Rows     : {row_count:,}")
    print(f"  Elapsed  : {elapsed:.2f}s")
    print(f"  NULL counts per column:")
    for col, cnt in null_counts.items():
        print(f"    {col:<40} {cnt:>6}")

    return row_count, null_counts, elapsed


def compare_results(
    orig_count: int, orig_nulls: dict,
    opt_count: int, opt_nulls: dict,
) -> bool:
    """Compare original vs optimized results and print a pass/fail summary.

    Args:
        orig_count: Row count from the original query.
        orig_nulls: NULL counts per column from the original query.
        opt_count: Row count from the optimized query.
        opt_nulls: NULL counts per column from the optimized query.

    Returns:
        True if all checks pass, False otherwise.
    """
    print("\n=== Validation ===")
    passed = True

    if orig_count == opt_count:
        print(f"  [PASS] Row count matches: {orig_count:,}")
    else:
        print(f"  [FAIL] Row count mismatch: original={orig_count:,}  optimized={opt_count:,}")
        passed = False

    for col in _NULLABLE_COLS:
        o = orig_nulls.get(col, "N/A")
        p = opt_nulls.get(col, "N/A")
        status = "PASS" if o == p else "FAIL"
        if status == "FAIL":
            passed = False
        print(f"  [{status}] {col:<40} original={o}  optimized={p}")

    return passed


def main() -> None:
    """Parse args and run before/after benchmark with result validation."""
    parser = argparse.ArgumentParser(description="Benchmark vw_HIVCPLWidgetAggregate query optimization.")
    parser.add_argument("--env", choices=list(_ENV_MAP.keys()), default="qa",
                        help="Target environment (default: qa)")
    parser.add_argument("--skip-original", action="store_true",
                        help="Skip the original query (only run optimized)")
    args = parser.parse_args()

    engine = _ENV_MAP[args.env]
    print(f"Environment : {args.env.upper()}")

    orig_count, orig_nulls, orig_elapsed = 0, {}, 0.0
    if not args.skip_original:
        orig_count, orig_nulls, orig_elapsed = run_query(engine, "ORIGINAL", ORIGINAL_SQL)
    else:
        print("\n[ORIGINAL] Skipped.")

    opt_count, opt_nulls, opt_elapsed = run_query(engine, "OPTIMIZED", OPTIMIZED_SQL)

    if not args.skip_original:
        all_passed = compare_results(orig_count, orig_nulls, opt_count, opt_nulls)

        print("\n=== Timing Summary ===")
        print(f"  Original  : {orig_elapsed:.2f}s")
        print(f"  Optimized : {opt_elapsed:.2f}s")
        if orig_elapsed > 0:
            improvement = (orig_elapsed - opt_elapsed) / orig_elapsed * 100
            print(f"  Improvement: {improvement:.1f}%")

        print(f"\n{'ALL CHECKS PASSED' if all_passed else 'ONE OR MORE CHECKS FAILED'}")
        sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
