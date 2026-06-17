# EC2 → ECS Fargate + EventBridge Migration Plan

## Overview

Migrate the `hiv_project_etl` pipeline from EC2 `t3.micro` cron to ECS Fargate + EventBridge. Infrastructure via Terraform (per-environment directories, mirroring `integrated_pathogy_form_etl` pattern).

**Current runtime:** ~8 min 51 sec (step 1: 6:43, step 2: 1:13, step 3: 0:28)

---

## Resource Inventory (Discovered)

| Item | Dev | Stg | Prod |
|---|---|---|---|
| AWS Account | `192914852225` | `298660930181` | `600942988942` |
| SSO Profile | `CHAMPS-AWS-ADMINISTRATOR-DEV` | `CHAMPS-AWS-ADMINISTRATOR-STG` | `CHAMPS-AWS-ADMINISTRATOR-PROD` |
| VPC ID | `vpc-0b1d9fd90edb3858e` | TBD (tag lookup) | TBD (tag lookup) |
| Private Subnets | `subnet-0674c0e5e757765b5`, `subnet-0a184bafb8ee25a1b`, `subnet-067654239563b3c92` | TBD | TBD |
| RDS SQL Server SG | `sg-09fc3a2597d535742` | TBD | TBD |
| Network State Bucket | `champs-network-dev-terraform-backend-us-east-1` | `champs-network-stg-terraform-backend-us-east-1` | `champs-network-prod-terraform-backend-us-east-1` |
| Terraform State Bucket | `hiv-project-etl-dev-terraform-backend-us-east-1` | `hiv-project-etl-stg-terraform-backend-us-east-1` | `hiv-project-etl-prod-terraform-backend-us-east-1` |

---

## Code Changes (Done)

### `Dockerfile`

- Base: `python:3.12-slim-bookworm`
- ODBC Driver 18 for SQL Server, `uv` via pip
- `WORKDIR /app`, copy project, `RUN mkdir -p logs data`, `RUN uv sync`
- `CMD ["uv", "run", "python", "main.py"]`

### `.dockerignore`

Excludes `logs/`, `data/`, `venv/`, `.venv/`, `__pycache__/`, `.git/`, `.vscode/`, `*.md`, `docs/`

### `.github/workflows/deploy.yml`

On push to `main`: build `--platform linux/amd64` → ECR push (`:latest`, `:git-sha`)

### `src/logging_config.py`

- Added `StreamHandler(sys.stdout)` with JSON formatter
- Updated CloudWatch log group from `/aws/ec2/champs-{env}-etl-reporting-ec2/etl-jobs` → `/ecs/hiv-project-etl`

### `src/log_checker.py`

Replaced file-based log scanning with CloudWatch `filter_log_events`:
- Queries `/ecs/hiv-project-etl` for last 2 hours
- Filter pattern: `?ERROR ?CRITICAL`
- Pagination handled via `nextToken`
- Graceful error handling for missing log group

### `main.py`

- `_run_dbt()`: removed `/root/.local/bin/uv` hardcode, now just `"uv"`
- Added `resource.getrusage(RUSAGE_SELF).ru_maxrss` → peak RSS in MB appended to success Slack message

### `config/config.py`

Added `CLOUDWATCH_LOG_GROUP = "/ecs/hiv-project-etl"`

---

## Terraform Infrastructure

Directory structure (mirrors `integrated_pathogy_form_etl`):

```
terraform/envs/
├── dev/
│   ├── ecs.tf          # ECR repo, ECS cluster, task definition
│   ├── networking.tf   # Security group + egress rules
│   ├── iam.tf          # Task execution role, task role, scheduler role
│   ├── eventbridge.tf  # Scheduler schedule + CloudWatch alarm
│   ├── provider.tf     # AWS provider, profile, default tags
│   ├── backend.tf      # S3 backend state
│   ├── data.tf         # Data sources (VPC, subnets, AZs)
│   ├── locals.tf       # Local naming conventions
│   ├── variables.tf    # Variables
│   ├── outputs.tf      # Outputs (ECR URL, task def ARN, SG ID, etc.)
│   └── terraform.tfvars
├── stg/ (same files, environment-specific values)
└── prod/ (same files, environment-specific values)
```

### Naming Convention

Prefix: `champs-{env}-hiv-etl`

| Resource | Name Pattern |
|---|---|
| ECR repo | `champs-{env}-hiv-etl` |
| ECS cluster | `champs-{env}-hiv-etl` |
| Task def family | `champs-{env}-hiv-etl` |
| Task execution role | `champs-{env}-hiv-etl-exec-role` |
| Task role | `champs-{env}-hiv-etl-task-role` |
| Scheduler role | `champs-{env}-hiv-etl-scheduler-role` |
| Security group | `champs-{env}-hiv-etl-sg` |
| Log group | `/ecs/hiv-project-etl` |
| Schedule name | `champs-{env}-hiv-etl-schedule` |
| CloudWatch alarm | `champs-{env}-hiv-etl-memory-alarm` |
| Terraform state bucket | `hiv-project-etl-{env}-terraform-backend-us-east-1` |

### Resources Created Per Environment

**`ecs.tf`:**
- `aws_ecr_repository` — `force_delete = true`, `scan_on_push = true`
- `aws_ecs_cluster` — Fargate, Container Insights enabled
- `aws_ecs_task_definition` — 0.5 vCPU, 2 GB, awsvpc, `STEP=0`, `awslogs` driver to `/ecs/hiv-project-etl`
- `aws_cloudwatch_log_group` — 30-day retention

**`networking.tf`:**
- `aws_security_group` — in VPC
- `aws_vpc_security_group_egress_rule` — HTTPS (443) to 0.0.0.0/0
- `aws_vpc_security_group_egress_rule` — SQL Server (1433) to RDS SG

**`iam.tf`:**
- `aws_iam_role` (execution) — `ecs-tasks.amazonaws.com`, attachment: `AmazonECSTaskExecutionRolePolicy`
- `aws_iam_role` (task) — `ecs-tasks.amazonaws.com`, policy: Secrets Manager `GetSecretValue` on `champs-*-*`, S3 `GetObject`/`PutObject` on `champs-etl-artifacts`
- `aws_iam_role` (scheduler) — `scheduler.amazonaws.com`, policy: `ecs:RunTask` + `iam:PassRole` on task def + task role

**`eventbridge.tf`:**
- `aws_scheduler_schedule` — `cron(0 10 * * ? *)`, target: ECS `RunTask` with `APP_ENV` override
- `aws_cloudwatch_metric_alarm` — `MemoryUtilized >= 1638` (80% of 2 GB), `statistic: Maximum`, `period: 60`, `evaluation_periods: 1`, treat missing as `not breaching`

### Data Source Strategy

| Env | VPC Lookup | Subnet Lookup |
|---|---|---|
| dev | `terraform_remote_state(champs_network_dev)` | From same remote state |
| stg | `data.aws_vpc(tags.Name = champs-staging-vpc)` | `data.aws_subnets(tags.Name = champs-staging-private-*)` |
| prod | `terraform_remote_state(champs_network_prod)` | From same remote state |

### Environment-Specific Values

| Value | Dev | Stg | Prod |
|---|---|---|---|
| `environment` var | `dev` | `stg` | `prod` |
| AWS profile | `CHAMPS-AWS-ADMINISTRATOR-DEV` | `CHAMPS-AWS-ADMINISTRATOR-STG` | `CHAMPS-AWS-ADMINISTRATOR-PROD` |
| RDS SG ID | `sg-09fc3a2597d535742` | TBD | TBD |
| Network state bucket | `champs-network-dev-...` | `champs-network-stg-...` | `champs-network-prod-...` |
| Terraform state bucket | `hiv-project-etl-dev-...` | `hiv-project-etl-stg-...` | `hiv-project-etl-prod-...` |

---

## CI/CD

`.github/workflows/deploy.yml` — on push to `main`:
1. Checkout
2. Configure AWS credentials (OIDC)
3. ECR login
4. `docker build --platform linux/amd64`
5. Tag + push (`:latest`, `:git-sha`)

---

## Implementation Order (Per Environment)

1. `terraform init` → `terraform plan` → verify **no resources destroyed** → `terraform apply`
2. Build Docker image and push to ECR
3. Manual `aws ecs run-task` → verify logs in CloudWatch
4. If step 3 passes, enable EventBridge schedule
5. Disable old EC2 cron (`crontab -e`)

## Rollback

1. If Fargate run fails: isolate by step override (`STEP=1/2/3`)
2. If code bug: fix → rebuild → push → `aws ecs run-task`
3. If infra issue: re-enable EC2 cron, debug Terraform

## Cost Estimate

| Item | EC2 t3.micro | Fargate (0.5 vCPU / 2 GB, 30 runs) |
|---|---|---|
| Compute | ~$8.47/month | ~$0.25/month |
| EventBridge | $0 | ~$1.00/month |
| CloudWatch | ~$0.50 | ~$0.50 |
| ECR storage | $0 | ~$0.01 |
| **Total** | **~$8.97/month** | **~$1.76/month** |

---

## Completed Steps

- [x] Dockerfile created + tested
- [x] `.dockerignore` created
- [x] `src/logging_config.py` — stdout handler, CW group updated
- [x] `src/log_checker.py` — CloudWatch-based implementation
- [x] `main.py` — uv path fixed, peak RSS logging added
- [x] `config/config.py` — `CLOUDWATCH_LOG_GROUP` added
- [x] `.github/workflows/deploy.yml` created
- [ ] Dev Terraform — init, plan (verify no destroys), apply
- [ ] Dev ECR push + `run-task` test
- [ ] Dev EventBridge schedule enable
- [ ] Stg/prod Terraform (same pattern, env-specific values)
