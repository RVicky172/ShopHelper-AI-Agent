terraform {
  required_version = ">= 1.9"

  # State is kept locally (infra/terraform.tfstate, git-ignored). For a team you
  # would use an S3 backend with `use_lockfile = true`.

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.20"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = "ShopHelper"
      ManagedBy = "Terraform"
    }
  }
}

data "aws_caller_identity" "current" {}
