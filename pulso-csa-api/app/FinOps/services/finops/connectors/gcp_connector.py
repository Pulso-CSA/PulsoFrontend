#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮GCP Connector – Billing + Compute❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from datetime import datetime, timedelta
from typing import Any, Optional

from services.finops.connectors.base import BaseCloudConnector


class GCPConnector(BaseCloudConnector):
    """Conector GCP: Cloud Billing, Compute Engine, Cloud Storage."""

    def __init__(
        self,
        service_account_json: Optional[dict] = None,
        project_id: Optional[str] = None,
    ) -> None:
        self._sa_json = service_account_json
        self._project_id = project_id

    def _get_credentials(self):
        """Retorna credenciais google-auth."""
        try:
            from google.oauth2 import service_account
            if self._sa_json:
                return service_account.Credentials.from_service_account_info(self._sa_json)
            return None
        except ImportError:
            raise RuntimeError("google-auth não instalado")

    def preflight(self) -> tuple[bool, str]:
        """Valida credenciais e projeto."""
        try:
            creds = self._get_credentials()
            if not creds:
                return False, "Credenciais GCP não fornecidas"
            from google.cloud import resourcemanager_v3
            client = resourcemanager_v3.ProjectsClient(credentials=creds)
            client.get_project(name=f"projects/{self._project_id or 'unknown'}")
            return True, "Credenciais válidas"
        except Exception as e:
            return False, f"GCP preflight falhou: {type(e).__name__}: {str(e)[:200]}"

    def collect_billing(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Billing Export via BigQuery ou Billing API (simplificado)."""
        try:
            from google.cloud import billing_v1
            creds = self._get_credentials()
            client = billing_v1.CloudBillingClient(credentials=creds)
            project_name = f"projects/{self._project_id}"
            billing_info = client.get_project_billing_info(name=project_name)
            return {
                "total_cost_usd": None,
                "billing_enabled": billing_info.billing_enabled,
                "note": "Custo detalhado exige BigQuery Billing Export habilitado",
                "period": {"start": start_date, "end": end_date},
            }
        except ImportError:
            return {"error": "google-cloud-billing não instalado", "total_cost_usd": None}
        except Exception as e:
            return {"error": str(e)[:200], "total_cost_usd": None}

    def collect_inventory(self) -> dict[str, Any]:
        """Inventário: Compute Engine, Cloud Storage buckets."""
        try:
            from google.cloud import compute_v1
            from google.cloud import storage
            creds = self._get_credentials()
            inv: dict[str, Any] = {"vms": [], "buckets": 0}
            project = self._project_id or ""
            instances = compute_v1.InstancesClient(credentials=creds)
            for zone in ["us-central1-a", "us-east1-b"]:
                try:
                    for vm in instances.list(project=project, zone=zone):
                        inv["vms"].append({"id": vm.id, "name": vm.name, "machine_type": vm.machine_type.split("/")[-1]})
                except Exception:
                    pass
            inv["vms"] = inv["vms"][:50]
            storage_client = storage.Client(credentials=creds, project=project)
            inv["buckets"] = len(list(storage_client.list_buckets()))
            return inv
        except ImportError:
            return {"error": "google-cloud-compute ou google-cloud-storage não instalados"}
        except Exception as e:
            return {"error": str(e)[:200]}

    def collect_metrics(self) -> dict[str, Any]:
        """Cloud Monitoring: placeholder."""
        return {"avg_cpu_utilization": None, "note": "Cloud Monitoring requer configuração adicional"}

    def _provider_name(self) -> str:
        return "gcp"
