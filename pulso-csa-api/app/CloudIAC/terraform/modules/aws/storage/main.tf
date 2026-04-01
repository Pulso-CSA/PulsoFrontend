# Golden module: AWS S3
resource "null_resource" "storage_placeholder" {
  triggers = { env = var.env }
}
