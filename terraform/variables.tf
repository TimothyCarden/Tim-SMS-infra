variable "aws_region" {
  type = map(string)
  default = {
    dev   = "us-east-1"
  }
}

variable "project_name" {
  type    = string
  default = "sms"
}


variable "cidrs" {
  type = map(string)
  default = {
    dev   = "10.12.0.0/16"
  }
}

variable "db_engine" {
  type        = string
  default     = "postgres"
  description = "DB engine"
}

variable "db_engine_version" {
  type        = string
  default     = "14"
  description = "DB engine version"
}

variable "db_family" {
  type        = string
  default     = "postgres14"
  description = "DB engine family"
}

variable "db_major_engine_version" {
  type        = string
  default     = "14"
  description = "DB engine major version"
}

variable "db_instance_type" {
  type        = string
  default     = "db.t4g.medium"
  description = "Size of the RDS DB instance"
}

variable "db_port" {
  type        = number
  default     = 5432
  description = "DB port"
}

variable "db_name_suffix" {
  type    = string
  default = "postgres"
}

variable "db_storage" {
  type        = map(number)
  description = "Allocated DB storage in GB"
  default = {
    dev   = 200
  }
}

variable "db_backup_retention_period" {
  type = map(number)
  default = {
    dev   = 7
  }
}

variable "db_user" {
  type    = string
  default = "postgres"
}

variable "db_password" {
  type = string
  # sensitive = true
}

variable "db_sg_rule" {
  type    = string
  default = "postgresql-tcp"
}
