#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Base Connector – Interface❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ConnectorResult:
    """Resultado normalizado de coleta (billing, inventário, métricas)."""
    billing: dict[str, Any]
    inventory: dict[str, Any]
    metrics: dict[str, Any]
    provider: str
    errors: list[str]
    data_quality: str  # "high" | "medium" | "low" | "none"


class BaseCloudConnector(ABC):
    """Interface base para conectores AWS/Azure/GCP."""

    CONNECTOR_TIMEOUT = 60
    REQUEST_TIMEOUT = 30

    @abstractmethod
    def preflight(self) -> tuple[bool, str]:
        """Valida credenciais e permissões mínimas. Retorna (ok, mensagem)."""
        pass

    @abstractmethod
    def collect_billing(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Coleta dados de billing na janela informada."""
        pass

    @abstractmethod
    def collect_inventory(self) -> dict[str, Any]:
        """Coleta inventário de recursos (compute, storage, network, etc.)."""
        pass

    @abstractmethod
    def collect_metrics(self) -> dict[str, Any]:
        """Coleta métricas (CPU, I/O, rede) quando disponíveis."""
        pass

    def collect_all(
        self, start_date: str, end_date: str
    ) -> ConnectorResult:
        """Pipeline completo: billing + inventário + métricas."""
        errors: list[str] = []
        billing: dict[str, Any] = {}
        inventory: dict[str, Any] = {}
        metrics: dict[str, Any] = {}

        try:
            billing = self.collect_billing(start_date, end_date)
        except Exception as e:
            errors.append(f"Billing: {type(e).__name__}: {str(e)[:150]}")
            billing = {"error": errors[-1], "total_cost": None}

        try:
            inventory = self.collect_inventory()
        except Exception as e:
            errors.append(f"Inventory: {type(e).__name__}: {str(e)[:150]}")
            inventory = {"error": errors[-1]}

        try:
            metrics = self.collect_metrics()
        except Exception as e:
            errors.append(f"Metrics: {type(e).__name__}: {str(e)[:150]}")
            metrics = {"error": errors[-1]}

        if not errors:
            data_quality = "high"
        elif len(errors) < 2:
            data_quality = "medium"
        else:
            data_quality = "low"

        return ConnectorResult(
            billing=billing,
            inventory=inventory,
            metrics=metrics,
            provider=self._provider_name(),
            errors=errors,
            data_quality=data_quality,
        )

    @abstractmethod
    def _provider_name(self) -> str:
        """Nome do provider (aws, azure, gcp)."""
        pass
