resource "aws_scheduler_schedule" "main" {
  name                = local.schedule_name
  schedule_expression = "cron(0 10 * * ? *)"
  state               = "DISABLED"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_ecs_cluster.main.arn
    role_arn = aws_iam_role.scheduler.arn

    ecs_parameters {
      task_definition_arn = aws_ecs_task_definition.main.arn
      launch_type         = "FARGATE"

      network_configuration {
        subnets          = local.private_subnet_ids
        security_groups  = [aws_security_group.main.id]
        assign_public_ip = false
      }
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "memory" {
  alarm_name          = local.alarm_name
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "MemoryUtilized"
  namespace           = "ECS/ContainerInsights"
  period              = "60"
  statistic           = "Maximum"
  threshold           = "1638"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_task_definition.main.family
  }

  alarm_description = "Fargate HIV ETL task memory utilization >= 80% of 2048 MB"
  ok_actions        = []
  alarm_actions     = []

  tags = {
    Name = local.alarm_name
  }
}
