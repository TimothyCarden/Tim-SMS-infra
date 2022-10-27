data "aws_ssm_parameter" "rds_db_password" {
  name = "CTMS_POSTGRES_DB_PASSWORD"
}

data "aws_ssm_parameter" "redshift_master_password" {
  name = "CTMS_REDSHIFT_PASSWORD"
}

data "aws_ssm_parameter" "sql_server_password" {
  name = "CTMS_AZURE_DB_PASSWORD"
}