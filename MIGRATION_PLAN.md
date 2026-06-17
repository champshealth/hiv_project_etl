# On-prem → AWS EC2 ETL Migration Plan — HIV Project

## Overview

Move the HIV Project ETL pipeline from on-prem Emory servers (`cmpjobprod1`, `cmpsqlprd101`, `cmpsqldev101`) to AWS EC2 + RDS SQL Server with Secrets Manager, CloudWatch logging, and Slack notifications.

### Target Architecture

| Component | Current (On-prem) | Target (AWS) |
|-----------|-------------------|--------------|
| **Compute** | `cmpjobprod1` (Emory cron server) | EC2 (private subnet, SSM access) |
| **Database** | SQL Server on `cmpsqlprd101` / `cmpsqldev101` | RDS SQL Server (`champs-{env}-portal-sqlserver`) |
| **Python** | 3.9 (via `scripts_py39.env`) | **3.12** |
| **dbt** | dbt-core==1.3.7, dbt-sqlserver==1.3.2 | **Latest dbt-sqlserver** |
| **Credentials** | `~/.config/local_credentials` + `.env` + env vars | **AWS Secrets Manager** |
| **Logging** | Rotating JSON file (`logs/hiv_project_etl_log.jsonl`) | **File + CloudWatch Logs** (watchtower) |
| **Scheduling** | cron on `cmpjobprod1` via `script_runner.sh` | **EC2 cron/systemd** via `ec2_run.sh` |
| **Notifications** | Slack via `ci_slack.py` (reads `~/.config/local_credentials`) | Slack via Secrets Manager |

---

## Phase 1: Files to Create

### 1. `include/aws_secrets.py` — Secrets Manager Client

Single boto3 Secrets Manager client that fetches per-environment secrets using the default credential chain (IAM role on EC2, `AWS_PROFILE` locally).

**Key logic:**
- Accept `env` parameter (dev/stg/prod)
- Map env → AWS account ID: `{dev: 192914852225, stg: 298660930181, prod: 600942988942}`
- Three secret name patterns:
  - `champs-{env}-portal-db-credentials` — RDS host/port/user/password
  - `champs-{env}-redcap-tokens-hiv-etl` — All REDCap API tokens for the hiv_project_etl project
  - `champs-{env}-slack-token` — Slack bot token + channel ID (already exists)
- Functions:
  - `get_secret(env, secret_name)` — generic fetcher
  - `get_redcap_config(env)` — returns dict of REDCAP_URL + all tokens
  - `get_db_credentials(env)` — returns dict of host/port/user/password/database
  - `get_slack_config(env)` — returns token + channel
- No hardcoded `AWS_PROFILE` — uses default credential chain

### 2. `ec2_run.sh` — Cron Wrapper

```bash
#!/bin/bash
export APP_ENV=${1:-dev}  # override per environment: dev/stg/prod
cd /mnt/etl/hiv_project_etl
uv run python main.py >> /mnt/etl/hiv_project_etl/logs/cron_$(date +\%Y\%m\%d).log 2>&1
```

Usage: `ec2_run.sh dev` or `ec2_run.sh prod`

### 3. `pyproject.toml` — Project Metadata & Dependencies

Single source of truth for dependencies, used by `uv sync`:

```toml
[project]
name = "hiv_project_etl"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    "dbt-sqlserver>=1.8.0",
    "pandas>=2.2.3",
    "numpy>=1.26.0",
    "duckdb>=1.2.1",
    "pyodbc>=5.2.0",
    "SQLAlchemy>=2.0.38",
    "boto3>=1.35.0",
    "watchtower>=3.3.0",
    "slack-sdk>=3.29.0",
    "labkey>=3.3.0",
    "python-json-logger>=3.3.0",
    "requests>=2.32.3",
    "pyarrow>=19.0.1",
    "python-dotenv>=1.0.1",
    "pyyaml>=6.0",
]
```

`requirements.txt` can be kept as a `uv pip install -r requirements.txt` fallback, or removed entirely in favor of `pyproject.toml`.

---

## Phase 2: Files to Rewrite

### 3. `config/config.py` — Configuration Module

**Before:** Uses `python-dotenv`/`.env`, `configparser`/`local_credentials`, hardcoded `connect_db.conn_qa/prod/stg`.

**After:**
- Import `APP_ENV` from `os.environ.get('APP_ENV', 'dev')`
- Source REDCap API URL + all tokens from `get_redcap_config(APP_ENV)` (Secrets Manager)
- Set `CONN = get_engine(APP_ENV)` for database connection (single factory)
- Remove all `.env` loading, `configparser` calls, and `local_credentials` file reads
- Keep `config/redcap_tokens.yaml` structure but source token values from Secrets Manager instead of env vars, or remove the YAML layer entirely

**Connection mapping (current → new):**

| Current `ENV` | Current Connection | New RDS Target |
|---------------|-------------------|----------------|
| `dev` | `connect_db.conn_qa` | `champs-dev-portal-sqlserver` / `champs_qa` |
| `stg` | `connect_db.conn_stg` | `champs-stg-portal-sqlserver` / `champs_stg` |
| `prod` | `connect_db.conn_prod` | `champs-prod-portal-sqlserver` / `champs_prod` |

Only the main ETL connections (`conn_qa`, `conn_stg`, `conn_prod`) are needed. Auxiliary/reporting connections are not used by this ETL.

### 4. `include/ci_utils.py` — Database Connections

**Before:** Multiple hardcoded SQLAlchemy engines pointing to `cmpsqlprd101` / `cmpsqldev101`, reading password from `~/.config/local_credentials` via `configparser`.

**After:**
- Replace with a single `get_engine(env)` factory function
- Read RDS endpoint + credentials from `champs-{env}-portal-db-credentials` in Secrets Manager
- Build engine: `mssql+pyodbc://{user}:{pass}@{host}:{port}/{database}?driver=ODBC+Driver+18+for+SQL+Server`
- Use ODBC Driver 18 for SQL Server (already installed on EC2)
- Cache engine per env to avoid re-creating connections

### 5. `config/logging_config.py` — Add CloudWatch Logging

**Before:** File-based `RotatingFileHandler` only (1MB, 5 backups to `logs/hiv_project_etl_log.jsonl`).

**After:**
- Keep existing `RotatingFileHandler` unchanged
- Add `watchtower.CloudWatchLogHandler`:
  - `log_group = /aws/ec2/champs-{APP_ENV}-etl-reporting-ec2/etl-jobs`
  - `stream_name = hiv_project_etl/{JOB_ID}` (one stream per job run for easy debugging)
  - `send_interval = 10` seconds
- Keep JSON format with `jobid` field (via custom `log_record_factory`)
- Configure log group retention to **auto-expire after 30 days**

### 6. `include/ci_slack.py` — Slack Notifications

**Before:** Reads Slack token from `~/.config/local_credentials` via `configparser`.

**After:**
- Source token + channel ID from `get_slack_config(APP_ENV)` in Secrets Manager
- Keep all existing function signatures: `post_mesg()`, `post_mesg_channel()`, `file_upload()`

### 7. `dbt/hiv_project/dbt_project.yml` + `profiles.yml`

**Before:** `profiles.yml` at `~/.dbt/profiles.yml` on the server, using env vars like `{{ env_var('DB_SERVER') }}`.

**After:**
- Move `profiles.yml` **into the project** (e.g., `dbt/hiv_project/profiles.yml`) so it's self-contained
- `dbt_project.yml` already has `profile: hiv_project` — add `--profiles-dir` flag in dbt calls or set `DBT_PROFILES_DIR` env var
- Source DB credentials from environment variables that are populated from Secrets Manager before dbt runs
- The `ec2_run.sh` script can populate these vars, or the pipeline orchestrator (`main.py`) can set them before invoking dbt

---

## Phase 3: Files to Modify

### 8. `main.py` — Pipeline Orchestrator

Add Slack notification at the end of the pipeline:
- On **success**: post message with env, job ID, duration, steps summary
- On **failure**: post message with env, job ID, failed step, error message
- Uses `ci_slack.post_mesg()` (already wired via `log_checker.py`)

### 9. `script_runner.sh` — Retire

The on-prem `script_runner.sh` loads `scripts_py39.env` and activates the venv. On EC2 it is replaced by `ec2_run.sh`. No need to port this file.

### 10. `pyproject.toml` (or `requirements.txt`) — Version Bumps

Dependencies defined in `pyproject.toml` (see Phase 1.3). The key additions are `boto3` and `watchtower`. Update `dbt/hiv_project/packages.yml` to latest compatible dbt package versions.

**dbt packages** (`dbt/hiv_project/packages.yml`) — verify these work with latest dbt-sqlserver:

---

## Phase 4: Files to Delete

| File | Reason |
|------|--------|
| `.env` | All secrets move to Secrets Manager |
| `src/redcap_api_export.py.backup` | Cleanup |
| `include/ci_utils_local.py` | Replaced by SM-backed `ci_utils.py` |

---

## Phase 5: REDCap Token Strategy

**Current setup:** 4 REDCap projects with tokens in `.env`:
- `REDCAP_API_TOKEN_11_KE`, `_11_MZ`, `_11_SL`, `_11_ZA` — Project 1.1 (per-site)
- `REDCAP_API_TOKEN_31` — Project 3.1 (all sites)
- `REDCAP_API_TOKEN_61` — Project 6.1 (all sites)
- `REDCAP_API_TOKEN_CA` — Clinical Abstraction (all sites)
- `REDCAP_URL` = `https://champs-redcap.emory.edu/api/`

**New Secrets Manager secret:** `champs-{env}-redcap-tokens-hiv-etl`

Description: `RedCap API tokens for the hiv_project_etl project`

JSON payload:

```json
{
  "REDCAP_URL": "https://champs-redcap.emory.edu/api/",
  "REDCAP_API_TOKEN_11_KE": "...",
  "REDCAP_API_TOKEN_11_MZ": "...",
  "REDCAP_API_TOKEN_11_SL": "...",
  "REDCAP_API_TOKEN_11_ZA": "...",
  "REDCAP_API_TOKEN_31": "...",
  "REDCAP_API_TOKEN_61": "...",
  "REDCAP_API_TOKEN_CA": "..."
}
```

The `config/redcap_tokens.yaml` file that maps env var names to token dicts can either:
- **(A)** Be removed — `config.py` directly uses `get_redcap_config(env)` dict
- **(B)** Be kept — but tokens are injected as env vars from Secrets Manager before the YAML is read

**Recommendation:** Option A — simplify by removing the YAML indirection.

---

## Phase 6: Infrastructure (AWS Console)

| Component | Details |
|-----------|---------|
| **RDS instances** | Already exist: `champs-{env}-portal-sqlserver` with databases. Tables already exist in RDS. |
| **Secrets** | Create `champs-{env}-redcap-tokens-hiv-etl` in each env. Slack token `champs-{env}-slack-token` already exists. |
| **IAM role** | `champs-{env}-etl-reporting-ec2-role` must have: `SecretsManagerReadWrite` + `CloudWatchLogsFullAccess` |
| **CloudWatch log group** | `/aws/ec2/champs-{APP_ENV}-etl-reporting-ec2/etl-jobs` with **30-day retention** |
| **EC2** | Deploy to existing ETL reporting EC2 in each env (private subnet, no public IP, SSM access) |
| **Security group** | Allow outbound HTTPS (REDCap API, Slack). Allow outbound to RDS on port 1433. |
| **ODBC Driver 18** | Already installed on EC2 |
| **NAT / VPC endpoints** | `champs-redcap.emory.edu` is already reachable from private subnets (confirmed) |

---

## Phase 7: Deployment Steps

```bash
# 1. Tar project (exclude local artifacts)
tar --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='logs' --exclude='data' --exclude='venv' --exclude='.venv' \
    -czf /tmp/hiv_project_etl.tar.gz -C /path/to/project .

# 2. Upload to S3
aws s3 cp /tmp/hiv_project_etl.tar.gz s3://champs-aws-etl-scripts-dev/

# 3. On EC2 via SSM
aws s3 cp s3://champs-aws-etl-scripts-dev/hiv_project_etl.tar.gz /tmp/
mkdir -p /mnt/etl/hiv_project_etl
tar -xzf /tmp/hiv_project_etl.tar.gz -C /mnt/etl/hiv_project_etl
cd /mnt/etl/hiv_project_etl

# 4. Create Python 3.12 venv and install deps with uv
uv venv --python 3.12
uv sync            # installs from pyproject.toml
# or if keeping requirements.txt:
# uv pip install -r requirements.txt

# 5. Install dbt packages
cd dbt/hiv_project && uv run dbt deps && cd ../..

# 6. Test run
APP_ENV=dev uv run python main.py

# 7. Set up cron (runs daily at 2 AM)
chmod +x /mnt/etl/hiv_project_etl/ec2_run.sh
echo '0 2 * * * /mnt/etl/hiv_project_etl/ec2_run.sh dev' | crontab -
```

---

## Caveats & Watchpoints

| Issue | Detail |
|-------|--------|
| **REDCap EAV duplicate PKs** | The current staging tables use auto-generated GUID PKs with MERGE in dbt. Verify no duplicate conflicts after migration — likely not an issue for this project but worth a quick check. |
| **dbt profiles.yml location** | Migrating from `~/.dbt/profiles.yml` to project-local `dbt/hiv_project/profiles.yml`. Ensure `DBT_PROFILES_DIR` env var or `--profiles-dir` flag is set in `ec2_run.sh` / `main.py`. |
| **CaseStatus upsert** | The case status target table exists in RDS — no action needed. |
| **Project 6.1 indexes** | dbt model creates indexes via post-hook — RDS supports the same DDL. |
| **CloudWatch costs** | Per-job stream chosen for debugging. Retention set to 30 days to manage costs. |
| **SSO for local dev** | When running locally via `AWS_PROFILE`, SSO sessions expire. Wrap local runs with `aws sso login --profile {profile}` as needed. |
