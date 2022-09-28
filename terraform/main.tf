module "infrastructure" {
  source = "git::git@github.com:ZapNURSE/terraform-module-infra.git?ref=ACTR-26-spin-up-dms-instance-with-instance-type-dms-t-3-medium"

  aws_region   = lookup(var.aws_region, local.env)
  env          = local.env
  project_name = var.project_name
  cidr         = lookup(var.cidrs, local.env)
  # aws_peer_region = lookup(var.aws_region, local.env)
  db_storage                        = lookup(var.db_storage, local.env)
  db_backup_retention_period        = lookup(var.db_backup_retention_period, local.env)
  db_user                           = var.db_user
  db_password                       = var.db_password
  db_engine                         = var.db_engine
  db_engine_version                 = var.db_engine_version
  db_major_engine_version           = var.db_major_engine_version
  db_family                         = var.db_family
  db_instance_type                  = var.db_instance_type
  db_port                           = var.db_port
  db_name_suffix                    = var.db_name_suffix
  db_sg_rule                        = var.db_sg_rule
  customer_gateway_ip_address       = var.customer_gateway_ip_address
  repl_instance_engine_version      = var.repl_instance_engine_version
  repl_instance_class               = var.repl_instance_class
  source_endpoint_database_password = var.source_endpoint_database_password
}
