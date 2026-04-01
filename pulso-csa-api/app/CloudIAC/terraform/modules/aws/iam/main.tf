# Golden module: AWS IAM
resource "null_resource" "iam_placeholder" {
  triggers = { env = var.env }
}
