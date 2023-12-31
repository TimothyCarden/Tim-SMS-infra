variable "aws_region" {
  type = map(string)
  default = {
    dev   = "us-west-2"
    prod  = "us-west-2"
    stage  = "us-west-2"
  }
}

variable "project_name" {
  type    = string
  default = "actriv"
}

variable "florence_project_name" {
  type    = string
  default = "florence"
}


variable "cidrs" {
  type = map(string)
  default = {
    dev   = "10.12.0.0/16"
    prod  = "10.13.0.0/16"
    stage  = "10.14.0.0/16"
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
  type = map(string)
  default = {
    dev   = "db.t4g.medium"
    prod  = "db.t4g.medium"
    stage  = "db.t4g.medium"
  }
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
    dev    = 550
    prod   = 450
    stage   = 250
  }
}

variable "db_backup_retention_period" {
  type = map(number)
  default = {
    dev   = 7
    prod  = 7
    stage  = 7
  }
}

variable "db_user" {
  type    = string
  default = "postgres"
}

variable "db_sg_rule" {
  type    = string
  default = "postgresql-tcp"
}

variable "customer_gateway_ip_address" {
  type = string
  default = "52.151.239.113"
}

variable "repl_instance_engine_version" {
  type        = string
  description = "replication_instance_engine_version"
  default     = "3.4.7"
}

variable "repl_instance_class" {
  type        =  map(string)
  description = "replication_instance_class"
  default = {
    dev   = "dms.t3.large"
    prod  = "dms.t3.large"
    stage  = "dms.t3.large"
  }
}

variable "enable_multi_az" {
  description = "If set to true, it will create multi az DMS"
  type   =  map(bool)
  default = {
    dev   = false
    prod  = false
    stage  = false
  }
}

variable "enable_replication_from_azure" {

  description = "If set to true, it will create endpoint for azure db"
  type   =  map(bool)
  default = {
    dev   = false
    prod  = true
    stage  = false
  }
}

# variable "source_endpoint_database_password" {
#   type        = string
#   # sensitive   = true
# }


variable "redshift_node_type" {
  type = map(string)
  default = {
    dev   = "ra3.xlplus"
    prod  = "ra3.xlplus"
    stage  = "ra3.xlplus"
  }
  description = "redshift node type"
}

variable "eks_instance_types" {
  type = map(string)
  default = {
    dev   = "t3.medium"
    prod  = "t3.medium"
    stage  = "t3.medium"
  }
}

variable "namespace_service_accounts" {
  type = map(string)
  default = {
    dev   = "default:secret-manager-service-account"
    prod  = "default:secret-manager-service-account"
    stage  = "default:secret-manager-service-account"
  }
}


variable "bucket_name" {
  type = map(string)
  default = {
    prod  = "app.app.actriv.com"
    dev   = "app.dev.actriv.com"
    stage = "app.stage.actriv.com"
  }
}

variable "bucket_name_custom_data" {
  type = map(string)
  default = {
    prod  = "custom.data.app.actriv.com"
    dev   = "custom.data.dev.actriv.com"
    stage = "custom.data.stage.actriv.com"
  }
}

variable "florence_bucket_name" {
  type = map(string)
  default = {
    prod  = "florence-app.app.actriv.com"
    dev   = "florence-app.dev.actriv.com"
    stage = "florence-app.stage.actriv.com"
  }
}

variable "endpoint" {
  type = map(string)
  default = {
    prod  = "app.actriv.com"
    dev   = "dev.actriv.com"
    stage  = "stage.actriv.com"
  }
}

variable "florence_endpoint" {
  type = map(string)
  default = {
    prod  = "florence.app.actriv.com"
    dev   = "florence.dev.actriv.com"
    stage  = "florence.stage.actriv.com"
  }
}


variable "service_name" {
  type    = string
  default = ""
}

variable "florence_service_name" {
  type    = string
  default = ""
}

variable "domain_name" {
  type = map(string)
  default = {
    prod  = "app.actriv.com"
    dev   = "dev.actriv.com"
    stage =  "stage.actriv.com"
  }
}

variable "florence_domain_name" {
  type = map(string)
  default = {
    prod  = "florence.app.actriv.com"
    dev   = "florence.dev.actriv.com"
    stage =  "florence.stage.actriv.com"
  }
}

variable "github_token"{
  default = "example"
}


