output "deployed_namespace" {
  value = kubernetes_namespace_v1.env_namespace.metadata[0].name
}

output "service_account_name" {
  value = kubernetes_service_account_v1.app_sa.metadata[0].name
}

output "environment_stage" {
  value = terraform.workspace
}

#output "vpc_id" {
#  value       = module.vpc.vpc_id
#}

#output "eks_cluster_name" {
#  value       = module.eks.cluster_name
#}

#output "ecr_repository_url" {
#  value       = aws_ecr_repository.app_repo.repository_url
#}
