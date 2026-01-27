# # Container Registry
# resource "aws_ecr_repository" "app_repo" {
#   name                 = var.app_name
#   image_tag_mutability = "MUTABLE"
#   force_delete         = true
# }

# # EKS Cluster
# module "eks" {
#   source  = "terraform-aws-modules/eks/aws"
#   version = "19.15.0"

#   cluster_name    = "${var.app_name}-cluster"
#   cluster_version = "1.27"

#   vpc_id                         = module.vpc.vpc_id
#   subnet_ids                     = module.vpc.private_subnets
#   cluster_endpoint_public_access = true

#   eks_managed_node_groups = {
#     general = {
#       desired_size = 2
#       min_size     = 1
#       max_size     = 3
#       instance_types = ["t3.medium"]
#     }
#   }
# }