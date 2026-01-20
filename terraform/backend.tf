# --- Backend Configuration ---
# Stores the state file remotely in S3 and handles locking with DynamoDB.
# Currently commented out for local Minikube development.

# terraform {
#   backend "s3" {
#     bucket         = "my-project-terraform-state"
#     key            = "global/k8s/terraform.tfstate"
#     region         = "us-east-1"
#     dynamodb_table = "terraform-locks"
#     encrypt        = true
#   }
# }