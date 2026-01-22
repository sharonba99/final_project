terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.0.0"
    }
  }
}

provider "kubernetes" {
  # config_path = "~/.kube/config" 
}

# 1. Namespace (Created dynamically based on workspace: dev/prod)
resource "kubernetes_namespace" "env_namespace" {
  metadata {
    name = "${var.app_name}-${terraform.workspace}"
    labels = {
      environment = terraform.workspace
      managed_by  = "terraform"
    }
  }
}

# 2. Service Account (Identity)
resource "kubernetes_service_account" "app_sa" {
  metadata {
    name      = "${var.app_name}-sa"
    namespace = kubernetes_namespace.env_namespace.metadata[0].name
  }
}

# 3. Role (Permissions)
resource "kubernetes_role" "pod_reader" {
  metadata {
    name      = "pod-reader"
    namespace = kubernetes_namespace.env_namespace.metadata[0].name
  }

  rule {
    api_groups = [""]
    resources  = ["pods", "services"]
    verbs      = ["get", "list", "watch"]
  }
}

# 4. Role Binding (Connecting Identity to Permissions)
resource "kubernetes_role_binding" "bind_sa" {
  metadata {
    name      = "bind-sa-reader"
    namespace = kubernetes_namespace.env_namespace.metadata[0].name
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.pod_reader.metadata[0].name
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.app_sa.metadata[0].name
    namespace = kubernetes_namespace.env_namespace.metadata[0].name
  }
}

# 5. Secret (Registry Credentials)
resource "kubernetes_secret" "docker_registry" {
  metadata {
    name      = "registry-credentials"
    namespace = kubernetes_namespace.env_namespace.metadata[0].name
  }

  type = "kubernetes.io/dockerconfigjson"

  data = {
    ".dockerconfigjson" = jsonencode({
      auths = {
        "https://index.docker.io/v1/" = {
          auth = "dXNlcm5hbWU6cGFzc3dvcmQ=" # Placeholder
        }
      }
    })
  }
}

# 6. Network Policy (Security)
resource "kubernetes_network_policy" "allow_app_traffic" {
  metadata {
    name      = "allow-ingress"
    namespace = kubernetes_namespace.env_namespace.metadata[0].name
  }

  spec {
    pod_selector {}
    policy_types = ["Ingress"]
    ingress {
      from {
        ip_block {
          cidr = "0.0.0.0/0"
        }
      }
    }
  }
}