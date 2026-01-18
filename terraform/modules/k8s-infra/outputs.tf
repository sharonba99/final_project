output "namespace_name" {
  value = kubernetes_namespace.env_namespace.metadata[0].name
}