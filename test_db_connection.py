import sys
import os
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy import text as sa_text
# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from include.ci_utils import connect_db

def test_connection():
    print("Testing database connections...\n")
    
    # List of connections to test with their display names
    # Skipping champs_dev as per user request
    connections = [
        ("Production Reporting", connect_db.conn_prod_rpt),
        ("QA Reporting", connect_db.conn_qa_rpt),
        ("Production", connect_db.conn_prod),
        ("Staging", connect_db.conn_stg)
    ]
    
    for name, conn in connections:
        print(f"Testing {name} connection...", end=" ")
        try:
            # Try to connect and execute a simple query
            with conn.connect() as connection:
                result = connection.execute(sa_text("SELECT count(*) count_objects  FROM sys.objects"))
                count = result.scalar()
                print("✓ Success!")
                print(f"   Server count: {count}...\n")
        except Exception as e:
            print("✗ Failed!")
            print(f"   Error: {str(e)}\n")

if __name__ == "__main__":
    test_connection()
