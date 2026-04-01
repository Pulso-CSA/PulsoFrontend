# Golden module: Azure VNet
resource "null_resource" "vnet_placeholder" {
  triggers = { env = var.env }
}
