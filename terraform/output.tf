output "app_client_id" {
  value = module.infrastructure.app_client_id
}

output "cognito_user_pool_id" {
  value = module.infrastructure.cognito_user_pool_id
}

output "florence_app_client_id" {
  value = module.infrastructure.florence_app_client_id
}

output "florence_cognito_user_pool_id" {
  value = module.infrastructure.florence_cognito_user_pool_id
}

output "cognito_admin_pool_id" {
  value = module.infrastructure.cognito_admin_pool_id
}

output "admin_app_client_id" {
  value = module.infrastructure.admin_app_client_id
}

output "distribution_id" {
  value = module.infrastructure.distribution_id
}

output "bucket_name" {
  value = module.infrastructure.bucket_name
}

output "bucket_name_raw_data" {
  value = module.infrastructure.bucket_name_raw_data
}

output "bucket_name_custom_data" {
  value = module.infrastructure.bucket_name_custom_data
}

output "florence_distribution_id" {
  value = module.infrastructure.florence_distribution_id
}

output "florence_bucket_name" {
  value = module.infrastructure.florence_bucket_name
}

output "postgres_to_s3_replication_task_arn" {
  value = module.infrastructure.postgres_to_s3_replication_task_arn
}

output "postgres_to_kinesis_replication_task_arn" {
  value = module.infrastructure.postgres_to_kinesis_replication_task_arn
}

output "workforce_to_s3_replication_task_arn" {
  value = module.infrastructure.workforce_to_s3_replication_task_arn
}

output "sql_to_s3_replication_task_arn" {
   value = length(module.infrastructure.sql_to_postgres_replication_task_arn) > 0 ? module.infrastructure.sql_to_s3_replication_task_arn[0] : (null)
}

output "sql_to_postgres_replication_task_arn" {
  value = length(module.infrastructure.sql_to_postgres_replication_task_arn) > 0 ? module.infrastructure.sql_to_postgres_replication_task_arn[0] : (null)
}

output "certificate_arn" {
  value = module.infrastructure.certificate_arn
}