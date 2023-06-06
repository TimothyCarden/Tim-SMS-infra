terraform {
   required_providers {

    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.10"
    }

    helm = {
      source  = "hashicorp/helm"
      version = "2.5.1"
    }
  }


  backend "s3" {
    region               = "us-west-2"
    bucket               = "actriv-develop-terraform-remote-state-us-west-2"
    workspace_key_prefix = "workspaces"
    key                  = "sms-infrastructure/state.tfstate"
    encrypt              = true
  }
}

provider "aws" {
  region = lookup(var.aws_region, local.env)
}

provider "helm" {
  # Several Kubernetes authentication methods are possible: https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs#authentication
  kubernetes {
    config_path = "~/.kube/config"
  }

}

provider "kubernetes" {
  config_path = "~/.kube/config"
}
