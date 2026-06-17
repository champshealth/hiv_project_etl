provider "aws" {
  region  = var.aws-region
  profile = "CHAMPS-AWS-ADMINISTRATOR-PROD"

  default_tags {
    tags = {
      Project     = "CHAMPS"
      Environment = var.environment
      Compliance  = var.compliance
    }
  }
}
