import sys
import os
import sqlalchemy as sa

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from include.ci_utils import get_engine


def test_connection():
    print("Testing RDS database connections...\n")

    for env in ("dev", "stg", "prod"):
        print(f"Testing {env} environment...", end=" ")
        try:
            conn = get_engine(env)
            with conn.connect() as connection:
                result = connection.execute(
                    sa.text("SELECT count(*) FROM sys.objects")
                )
                count = result.scalar()
                print("OK")
                print(f"   Object count: {count}")
        except Exception as e:
            print("FAILED")
            print(f"   Error: {e}")
        print()


if __name__ == "__main__":
    test_connection()
