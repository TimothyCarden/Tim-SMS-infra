variable "aws_region" {
  type = map(string)
  default = {
    dev   = "us-west-2"
    prod  = "us-west-2"
    test  = "us-west-2"
  }
}

variable "project_name" {
  type    = string
  default = "actriv"
}


variable "cidrs" {
  type = map(string)
  default = {
    dev   = "10.12.0.0/16"
    prod  = "10.13.0.0/16"
    test  = "10.14.0.0/16"
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
    test  = "db.t4g.medium"
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
    dev    = 400
    prod   = 200
    test   = 200
  }
}

variable "db_backup_retention_period" {
  type = map(number)
  default = {
    dev   = 7
    prod  = 7
    test  = 7
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
    test  = "dms.t3.large"
  }
}

variable "enable_multi_az" {
  description = "If set to true, it will create multi az DMS"
  type   =  map(bool)
  default = {
    dev   = false
    prod  = false
    test  = false
  }
}

variable "enable_replication_from_azure" {

  description = "If set to true, it will create endpoint for azure db"
  type   =  map(bool)
  default = {
    dev   = false
    prod  = true
    test  = false
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
    test  = "ra3.xlplus"
  }
  description = "redshift node type"
}

variable "eks_instance_types" {
  type = map(string)
  default = {
    dev   = "t3.medium"
    prod  = "t3.medium"
    test  = "t3.medium"
  }
}

variable "namespace_service_accounts" {
  type = map(string)
  default = {
    dev   = "default:secret-manager-service-account"
    prod  = "default:secret-manager-service-account"
    test  = "default:secret-manager-service-account"
  }
}


variable "bucket_name" {
  type = map(string)
  default = {
    prod  = "app.actrusfm.com"
    dev   = "app.dev.actrusfm.com"
    test = "app.stage.actrusfm.com"
  }
}

variable "endpoint" {
  type = map(string)
  default = {
    prod  = "actrusfm.com"
    dev   = "dev.actrusfm.com"
    test  = "test.actrusfm.com"
  }
}


variable "service_name" {
  type    = string
  default = ""
}

variable "domain_name" {
  type = map(string)
  default = {
    prod  = "actrusfm.com"
    dev   = "dev.actrusfm.com"
    test =  "test.actrusfm.com"
  }
}

