# AWS Networking (VPC)

Módulo golden para VPC AWS com subnets privadas.

## Uso

```hcl
module "vpc" {
  source = "../../../modules/aws/networking"
  env    = "dev"
  availability_zones = ["us-east-1a", "us-east-1b"]
  tags = { Environment = "dev", Project = "pulso" }
}
```
