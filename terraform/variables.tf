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
