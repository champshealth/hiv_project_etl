provider "aws" {
  region  = var.aws-region
  profile = "CHAMPS-AWS-ADMINISTRATOR-DEV"

  default_tags {
    tags = {
      Project     = "CHAMPS"
      Environment = var.environment
      Compliance  = var.compliance
    }
  }
}
