module "infrastructure" {
  source = "git::git@github.com:ZapNURSE/terraform-module-infra.git?ref=develop"

  aws_region                        = lookup(var.aws_region, local.env)
  env                               = local.env
  project_name                      = var.project_name
  cidr                              = lookup(var.cidrs, local.env)
  # aws_peer_region = lookup(var.aws_region, local.env)
  db_storage                        = lookup(var.db_storage, local.env)
  db_backup_retention_period        = lookup(var.db_backup_retention_period, local.env)
  db_user                           = var.db_user
  db_password                       = local.db_password
  db_engine                         = var.db_engine
  db_engine_version                 = var.db_engine_version
  db_major_engine_version           = var.db_major_engine_version
  db_family                         = var.db_family
  db_instance_type                  = lookup(var.db_instance_type, local.env)
  db_port                           = var.db_port
  db_name_suffix                    = var.db_name_suffix
  db_sg_rule                        = var.db_sg_rule
  repl_instance_engine_version      = var.repl_instance_engine_version
  repl_instance_class               = lookup(var.repl_instance_class, local.env)
  enable_multi_az                   = lookup(var.enable_multi_az, local.env)
  redshift_master_password          = local.redshift_password
  redshift_node_type                = lookup(var.redshift_node_type, local.env)
  eks_instance_types                = lookup(var.eks_instance_types, local.env)
  customer_gateway_ip_address       = var.customer_gateway_ip_address
  source_endpoint_database_password = local.azure_sql_password
  enable_replication_from_azure     = lookup(var.enable_replication_from_azure, local.env)
  namespace_service_accounts        = lookup(var.namespace_service_accounts, local.env)
  bucket_name                       = lookup(var.bucket_name, local.env)
  endpoint                          = lookup(var.endpoint, local.env)
  service_name                      = var.service_name
  domain_name                       = lookup(var.domain_name, local.env)
  fcm_api_key                       = local.fcm_api_key
}

