terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket       = "hiv-project-etl-prod-terraform-backend-us-east-1"
    key          = "terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }
}
