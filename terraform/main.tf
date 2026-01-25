terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.0.0"
    }
  }
}

provider "kubernetes" {
}

resource "kubernetes_namespace_v1" "env_namespace" {
  metadata {
    name = "urlshortener"
    labels = {
      environment = terraform.workspace
      managed_by  = "terraform"
    }
  }
  lifecycle {
    ignore_changes = [metadata]
  }
}

resource "kubernetes_service_account_v1" "app_sa" {
  metadata {
    name      = "${var.app_name}-sa"
    namespace = kubernetes_namespace_v1.env_namespace.metadata[0].name
  }
}

resource "kubernetes_role_v1" "pod_reader" {
  metadata {
    name      = "pod-reader"
    namespace = kubernetes_namespace_v1.env_namespace.metadata[0].name
  }

  rule {
    api_groups = [""]
    resources  = ["pods", "services"]
    verbs      = ["get", "list", "watch"]
  }
}

resource "kubernetes_role_binding_v1" "bind_sa" {
  metadata {
    name      = "bind-sa-reader"
    namespace = kubernetes_namespace_v1.env_namespace.metadata[0].name
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role_v1.pod_reader.metadata[0].name
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account_v1.app_sa.metadata[0].name
    namespace = kubernetes_namespace_v1.env_namespace.metadata[0].name
  }
}

resource "kubernetes_secret_v1" "docker_registry" {
  metadata {
    name      = "registry-credentials"
    namespace = kubernetes_namespace_v1.env_namespace.metadata[0].name
  }

  type = "kubernetes.io/dockerconfigjson"

  data = {
    ".dockerconfigjson" = jsonencode({
      auths = {
        "https://index.docker.io/v1/" = {
          auth = "dXNlcm5hbWU6cGFzc3dvcmQ="
        }
      }
    })
  }
}

resource "kubernetes_network_policy_v1" "allow_app_traffic" {
  metadata {
    name      = "allow-ingress"
    namespace = kubernetes_namespace_v1.env_namespace.metadata[0].name
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
