module "infrastructure" {
  source = "git::git@github.com:ZapNURSE/terraform-module-infra.git?ref=ACTR-29-configure-a-vpc-for-whole-infrastructure"

  aws_region   = lookup(var.aws_region, local.env)
  env          = local.env
  project_name = var.project_name
  cidr         = lookup(var.cidrs, local.env)
  # aws_peer_region = lookup(var.aws_region, local.env)

}
