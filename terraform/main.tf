terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.0.0"
    }
  }
  
  # backend "s3" {
  #   bucket = "my-bucket"
  #   key    = "state"
  # }
}

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "minikube"
}

module "k8s_infrastructure" {
  source      = "./modules/k8s-infra"
  app_name    = "final-project"
  environment = terraform.workspace
}