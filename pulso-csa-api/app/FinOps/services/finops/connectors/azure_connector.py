#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Azure Connector – Cost Management❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from datetime import datetime, timedelta
from typing import Any, Optional

from services.finops.connectors.base import BaseCloudConnector


class AzureConnector(BaseCloudConnector):
    """Conector Azure: Cost Management Query, inventário básico."""

    def __init__(
        self,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        subscription_id: Optional[str] = None,
    ) -> None:
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._subscription_id = subscription_id

    def preflight(self) -> tuple[bool, str]:
        """Valida credenciais e access ao subscription."""
        try:
            from azure.identity import ClientSecretCredential
            from azure.mgmt.resource import ResourceManagementClient
            cred = ClientSecretCredential(
                tenant_id=self._tenant_id or "",
                client_id=self._client_id or "",
                client_secret=self._client_secret or "",
            )
            client = ResourceManagementClient(cred, self._subscription_id or "")
            list(client.resource_groups.list())
            return True, "Credenciais válidas"
        except ImportError:
            return False, "azure-identity ou azure-mgmt-resource não instalados. pip install azure-identity azure-mgmt-resource"
        except Exception as e:
            return False, f"Azure preflight falhou: {type(e).__name__}: {str(e)[:200]}"

    def collect_billing(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Cost Management Query API."""
        try:
            from azure.identity import ClientSecretCredential
            from azure.mgmt.costmanagement import CostManagementClient
            from azure.mgmt.costmanagement.models import QueryDefinition, QueryTimePeriod, QueryDataset
            cred = ClientSecretCredential(
                tenant_id=self._tenant_id or "",
                client_id=self._client_id or "",
                client_secret=self._client_secret or "",
            )
            client = CostManagementClient(cred)
            scope = f"/subscriptions/{self._subscription_id}"
            start = start_date or (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
            end = end_date or (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
            query = QueryDefinition(
                type="ActualCost",
                timeframe="Custom",
                time_period=QueryTimePeriod(from_property=start, to=end),
                dataset=QueryDataset(
                    granularity="Monthly",
                    aggregation={"totalCost": {"name": "Cost", "function": "Sum"}},
                ),
            )
            result = client.query.usage(scope, query)
            rows = list(result.rows) if result.rows else []
            total = sum(float(r[0]) for r in rows) if rows else 0
            return {"total_cost_usd": round(total, 2), "period": {"start": start, "end": end}, "rows_count": len(rows)}
        except ImportError:
            return {"error": "azure-mgmt-costmanagement não instalado", "total_cost_usd": None}
        except Exception as e:
            return {"error": str(e)[:200], "total_cost_usd": None}

    def collect_inventory(self) -> dict[str, Any]:
        """Inventário resumido: VMs, Disks, Storage."""
        try:
            from azure.identity import ClientSecretCredential
            from azure.mgmt.compute import ComputeManagementClient
            from azure.mgmt.storage import StorageManagementClient
            cred = ClientSecretCredential(
                tenant_id=self._tenant_id or "",
                client_id=self._client_id or "",
                client_secret=self._client_secret or "",
            )
            sub = self._subscription_id or ""
            inv: dict[str, Any] = {"vms": [], "disks": [], "storage_accounts": 0}
            compute = ComputeManagementClient(cred, sub)
            for vm in compute.virtual_machines.list_all():
                inv["vms"].append({"id": vm.id, "name": vm.name, "size": getattr(vm.hardware_profile, "vm_size", None)})
            inv["vms"] = inv["vms"][:50]
            storage = StorageManagementClient(cred, sub)
            inv["storage_accounts"] = len(list(storage.storage_accounts.list()))
            return inv
        except ImportError:
            return {"error": "azure-mgmt-compute ou azure-mgmt-storage não instalados"}
        except Exception as e:
            return {"error": str(e)[:200]}

    def collect_metrics(self) -> dict[str, Any]:
        """Azure Monitor: placeholder (requer setup adicional)."""
        return {"avg_cpu_utilization": None, "note": "Azure Monitor requer configuração adicional"}

    def _provider_name(self) -> str:
        return "azure"
