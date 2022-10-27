terraform {
  # required_providers {
  #   aws = {
  #     source  = "hashicorp/aws"
  #     version = "3.62.0"
  #   }
  # }


  backend "s3" {
    region               = "us-west-2"
    bucket               = "actriv-dev-terraform-remote-state-us-west-2"
    workspace_key_prefix = "workspaces"
    key                  = "sms-infrastructure/state.tfstate"
    encrypt              = true
  }
}

provider "aws" {
  region = lookup(var.aws_region, local.env)
}
