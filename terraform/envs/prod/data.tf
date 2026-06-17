data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_availability_zones" "available" {
  state = "available"

  filter {
    name   = "region-name"
    values = [var.aws-region]
  }
}

data "terraform_remote_state" "network" {
  backend = "s3"

  config = {
    bucket = "champs-network-prod-terraform-backend-us-east-1"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}
