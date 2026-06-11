#!/bin/bash
set -a
export APP_ENV=${1:-dev}
export LOG_DIR=/mnt/etl/hiv_project_etl/logs
mkdir -p "$LOG_DIR"
cd /mnt/etl/hiv_project_etl

logfile="$LOG_DIR/cron_$(date +\%Y\%m\%d).log"

# Load DB credentials from Secrets Manager into environment for dbt
eval "$(uv run python -c "
from include.aws_secrets import get_db_credentials
c = get_db_credentials('${APP_ENV}')
print(f'DB_HOST={c[\"host\"]}')
print(f'DB_PORT={c[\"port\"]}')
print(f'DB_NAME={c[\"database\"]}')
print(f'DB_USER={c[\"username\"]}')
print(f'DB_PASSWORD={c[\"password\"]}')
")"

# Run steps sequentially to avoid OOM on t3.micro (916 MB total)
echo "=== STEP 1: Data export + load ===" >> "$logfile"
STEP=1 uv run python main.py >> "$logfile" 2>&1
s1=$?

echo "=== STEP 2: dbt run ===" >> "$logfile"
STEP=2 uv run python main.py >> "$logfile" 2>&1
s2=$?

echo "=== STEP 3: Upserts ===" >> "$logfile"
STEP=3 uv run python main.py >> "$logfile" 2>&1
s3=$?

echo "=== DONE (exit codes: s1=$s1 s2=$s2 s3=$s3) ===" >> "$logfile"
