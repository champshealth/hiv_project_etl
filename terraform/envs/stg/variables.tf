variable "aws-region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, stg, prod)"
  type        = string
  default     = "stg"
}

variable "compliance" {
  description = "Compliance framework"
  type        = string
  default     = "N/A"
}
