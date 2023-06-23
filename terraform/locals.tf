locals {
  env                = terraform.workspace
  db_password        = data.aws_secretsmanager_secret_version.rds_password.secret_string
  redshift_password  = data.aws_secretsmanager_secret_version.redshift_password.secret_string
  azure_sql_password = data.aws_secretsmanager_secret_version.azure_sql_password.secret_string
  fcm_api_key        = data.aws_secretsmanager_secret_version.fcm_api_key.secret_string
  argo_password      = data.aws_secretsmanager_secret_version.argo_password.secret_string
}

