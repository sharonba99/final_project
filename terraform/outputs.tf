output "deployed_namespace" {
  value = kubernetes_namespace_v1.env_namespace.metadata[0].name
}

output "service_account_name" {
  value = kubernetes_service_account_v1.app_sa.metadata[0].name
}

output "environment_stage" {
  value = terraform.workspace
}