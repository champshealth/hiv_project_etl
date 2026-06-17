provider "aws" {
  region  = var.aws-region
  profile = "CHAMPS-AWS-ADMINISTRATOR-STG"

  default_tags {
    tags = {
      Project     = "CHAMPS"
      Environment = var.environment
      Compliance  = var.compliance
    }
  }
}
