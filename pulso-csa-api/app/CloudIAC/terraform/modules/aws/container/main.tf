# Golden module: AWS ECS
resource "null_resource" "container_placeholder" {
  triggers = { env = var.env }
}
