# Golden module: GCP VPC
resource "null_resource" "vpc_placeholder" {
  triggers = { env = var.env }
}
