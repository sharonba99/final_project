output "deployed_namespace" {
  description = "The namespace created for this environment"
  value       = kubernetes_namespace_v1.env_namespace.metadata[0].name
}

output "service_account_name" {
  description = "The service account to be used by the app"
  value       = kubernetes_service_account.app_sa.metadata[0].name
}

output "environment_stage" {
  description = "Current active workspace"
  value       = terraform.workspace
}