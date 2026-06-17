resource "aws_security_group" "main" {
  name        = local.sg_name
  description = "Security group for HIV ETL Fargate tasks"
  vpc_id      = local.vpc_id

  tags = {
    Name = local.sg_name
  }
}

resource "aws_vpc_security_group_egress_rule" "https" {
  security_group_id = aws_security_group.main.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  description       = "Allow HTTPS to REDCap API and Slack"
}

resource "aws_vpc_security_group_egress_rule" "rds" {
  security_group_id            = aws_security_group.main.id
  referenced_security_group_id = local.rds_sg_id
  from_port                    = 1433
  to_port                      = 1433
  ip_protocol                  = "tcp"
  description                  = "Allow SQL Server to CHAMPS DB"
}

