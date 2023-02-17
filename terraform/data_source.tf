# =================================
# RDS Password
# =================================

data "aws_secretsmanager_secret" "rds_password" {
  name = "${local.env}/PostgreDatabasePassword"
}
data "aws_secretsmanager_secret_version" "rds_password" {
  secret_id = data.aws_secretsmanager_secret.rds_password.id
}

# =================================
# Redshift Password
# =================================

data "aws_secretsmanager_secret" "redshift_password" {
  name = "${local.env}/RedshiftPassword"
}
data "aws_secretsmanager_secret_version" "redshift_password" {
  secret_id = data.aws_secretsmanager_secret.redshift_password.id
}

# =================================
# CTMS Sql server
# =================================

data "aws_secretsmanager_secret" "azure_sql_password" {
  name = "${local.env}/AzureSqlServerPassword"
}
data "aws_secretsmanager_secret_version" "azure_sql_password" {
  secret_id = data.aws_secretsmanager_secret.azure_sql_password.id
}

# =================================
# FCM Api Key
# =================================

data "aws_secretsmanager_secret" "fcm_api_key" {
  name = "${local.env}/FCMApiKEY"
}
data "aws_secretsmanager_secret_version" "fcm_api_key" {
  secret_id = data.aws_secretsmanager_secret.fcm_api_key.id
}