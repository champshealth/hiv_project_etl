import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlalchemy as sa
from config.config import CONN

with CONN.connect() as c:
    # Check staging table columns
    print("=== STG TABLE COLUMNS ===")
    r = c.execute(sa.text("SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'stg' AND TABLE_NAME = 'HIVProject1_1_stg' ORDER BY ORDINAL_POSITION"))
    for row in r: print(row)

    # Check for dup unique_key combos in staging table
    print("\n=== DUPS IN STAGING ===")
    r2 = c.execute(sa.text("SELECT SiteId, CatchmentId, ReportId, FieldName, FieldValue, COUNT(*) as cnt FROM stg.HIVProject1_1_stg GROUP BY SiteId, CatchmentId, ReportId, FieldName, FieldValue HAVING COUNT(*) > 1"))
    dups = r2.fetchall()
    print(f"Count: {len(dups)}")
    for d in dups[:5]: print(d)

    if not dups:
        # Check for dup SiteId/CatchmentId/ReportId/FieldName (excl FieldValue)
        r3 = c.execute(sa.text("SELECT SiteId, CatchmentId, ReportId, FieldName, COUNT(*) as cnt FROM stg.HIVProject1_1_stg GROUP BY SiteId, CatchmentId, ReportId, FieldName HAVING COUNT(*) > 1 ORDER BY cnt DESC"))
        dups2 = r3.fetchall()
        print(f"\n=== DUPS EXCL FieldValue: {len(dups2)} ===")
        for d in dups2[:5]: print(d)

    # Count total rows
    r4 = c.execute(sa.text("SELECT COUNT(*) FROM stg.HIVProject1_1_stg"))
    print(f"\nTotal stg rows: {r4.scalar()}")

    # Check target mart table counts
    r5 = c.execute(sa.text("SELECT isDeleted, COUNT(*) FROM hiv.HIVProject1_1 GROUP BY isDeleted"))
    print(f"\n=== MART TABLE ===")
    for row in r5: print(row)
