variable "env" {
  type        = string
  description = "Environment"
}

variable "tags" {
  type    = map(string)
  default = {}
}
