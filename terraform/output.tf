output "app_client_id" {
  value = module.infrastructure.app_client_id
}

output "cognito_user_pool_id" {
  value = module.infrastructure.cognito_user_pool_id
}

output "distribution_id" {
  value = module.infrastructure.distribution_id
}

output "bucket_name" {
  value = module.infrastructure.bucket_name
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
   value = module.infrastructure.sql_to_s3_replication_task_arn != null ? module.infrastructure.sql_to_s3_replication_task_arn : (null)
}

output "sql_to_postgres_replication_task_arn" {
  value = module.infrastructure.sql_to_postgres_replication_task_arn != null ? module.infrastructure.sql_to_postgres_replication_task_arn : (null)
}