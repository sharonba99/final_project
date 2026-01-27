# module "s3_access_role" {
#   source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
#   version = "5.20.0"

#   role_name = "${var.app_name}-s3-role"

#   oidc_providers = {
#     main = {
#       provider_arn               = module.eks.oidc_provider_arn
#       namespace_service_accounts = ["urlshortener:${var.app_name}-sa"]
#     }
#   }
 # IAM Role
#   role_policy_arns = {
#     policy = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
#   }
# }