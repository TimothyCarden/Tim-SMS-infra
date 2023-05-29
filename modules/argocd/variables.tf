variable "argocd_namespace" {
  description = "the name of argocd namespace"
  type        = string
}
variable "release_name" {
  description = "the name of the argocd release"
  default     = "argocd"
  type        = string
}
variable "chart_version" {
  description = "the version of argocd chart"
  default     = "5.7.0"
  type        = string
}
variable "hostname" {
  type        = string
  description = "hostname of argocd"
}
variable "certificate_arn" {
  type        = string
  description = "certificate for argocd"
}

variable "cluster_endpoint" {
}

variable "cluster_name" {
}

variable "authority_data" {
}

variable "ingress_class_name"{
  default = "nginx-nlb"
}

variable "domain_name" {
  description = "Domain name"
  type        = string
}