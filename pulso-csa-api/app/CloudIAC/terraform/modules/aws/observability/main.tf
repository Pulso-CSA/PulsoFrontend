# Golden module: AWS CloudWatch
resource "null_resource" "observability_placeholder" {
  triggers = { env = var.env }
}
