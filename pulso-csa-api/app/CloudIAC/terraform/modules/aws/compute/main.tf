# Golden module: AWS EC2
resource "null_resource" "compute_placeholder" {
  triggers = {
    env = var.env
  }
}
