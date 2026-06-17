locals {
  vpc_id             = data.terraform_remote_state.network.outputs.vpc_id
  private_subnet_ids = data.terraform_remote_state.network.outputs.private_subnets
  rds_sg_id          = "sg-0134d69791b5c66f4"

  name_prefix = "champs-${var.environment}-hiv-etl"

  ecs_cluster_name    = local.name_prefix
  task_def_family     = local.name_prefix
  container_name      = local.name_prefix
  ecr_repo_name       = local.name_prefix
  exec_role_name      = "${local.name_prefix}-exec-role"
  task_role_name      = "${local.name_prefix}-task-role"
  scheduler_role_name = "${local.name_prefix}-scheduler-role"
  sg_name             = "${local.name_prefix}-sg"
  log_group_name      = "/ecs/hiv-project-etl"
  schedule_name       = "${local.name_prefix}-schedule"
  alarm_name          = "${local.name_prefix}-memory-alarm"
}
