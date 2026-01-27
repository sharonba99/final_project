# terraform {
#   required_version = ">= 1.0"

#   required_providers {
#     aws = {
#       source  = "hashicorp/aws"
#       version = "~> 5.0"
#     }
#     kubernetes = {
#       source  = "hashicorp/kubernetes"
#       version = "~> 2.0"
#     }
#   }

#  # S3 bucket
#   backend "s3" {
#     bucket         = "my-project-terraform-state"
#     key            = "eks/terraform.tfstate"
#     region         = "us-east-1"
#     dynamodb_table = "terraform-locks"
#     encrypt        = true
#   }
# }

# provider "aws" {
#   region = var.aws_region
# }