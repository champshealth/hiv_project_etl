resource "aws_ecr_repository" "main" {
  name         = local.ecr_repo_name
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = local.ecr_repo_name
  }
}

resource "aws_ecs_cluster" "main" {
  name = local.ecs_cluster_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = local.ecs_cluster_name
  }
}

resource "aws_ecs_task_definition" "main" {
  family                   = local.task_def_family
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name  = local.container_name
      image = "${aws_ecr_repository.main.repository_url}:latest"
      essential = true

      environment = [
        { name = "STEP", value = "0" },
        { name = "APP_ENV", value = var.environment },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = local.log_group_name
          "awslogs-region"        = var.aws-region
          "awslogs-stream-prefix" = var.environment
        }
      }
    }
  ])

  tags = {
    Name = local.task_def_family
  }
}

resource "aws_cloudwatch_log_group" "main" {
  name              = local.log_group_name
  retention_in_days = 30

  tags = {
    Name = local.task_def_family
  }
}
