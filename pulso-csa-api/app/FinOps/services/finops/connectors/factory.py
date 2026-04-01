#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Cloud Connector Factory❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from typing import Optional

from models.finops.finops_models import AWSCredentials, AzureCredentials, GCPCredentials
from services.finops.connectors.aws_connector import AWSConnector
from services.finops.connectors.azure_connector import AzureConnector
from services.finops.connectors.base import BaseCloudConnector
from services.finops.connectors.gcp_connector import GCPConnector


def get_connector(
    cloud: str,
    aws_creds: Optional[AWSCredentials] = None,
    azure_creds: Optional[AzureCredentials] = None,
    gcp_creds: Optional[GCPCredentials] = None,
) -> Optional[BaseCloudConnector]:
    """Retorna o conector apropriado para o provider."""
    if cloud == "aws" and aws_creds:
        return AWSConnector(
            access_key_id=aws_creds.access_key_id,
            secret_access_key=aws_creds.secret_access_key,
            session_token=aws_creds.session_token,
            role_arn=aws_creds.role_arn,
            external_id=aws_creds.external_id,
            region=aws_creds.region,
        )
    if cloud == "azure" and azure_creds:
        return AzureConnector(
            tenant_id=azure_creds.tenant_id,
            client_id=azure_creds.client_id,
            client_secret=azure_creds.client_secret,
            subscription_id=azure_creds.subscription_id,
        )
    if cloud == "gcp" and gcp_creds:
        return GCPConnector(
            service_account_json=gcp_creds.service_account_json,
            project_id=gcp_creds.project_id,
        )
    return None


class CloudConnectorFactory:
    """Factory para criar conectores por provider."""

    @staticmethod
    def create(
        cloud: str,
        aws_creds: Optional[AWSCredentials] = None,
        azure_creds: Optional[AzureCredentials] = None,
        gcp_creds: Optional[GCPCredentials] = None,
    ) -> Optional[BaseCloudConnector]:
        return get_connector(cloud, aws_creds, azure_creds, gcp_creds)
