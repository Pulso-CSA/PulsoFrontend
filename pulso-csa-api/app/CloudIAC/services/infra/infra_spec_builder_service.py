#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Infra Spec Builder – LLM + cache❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import hashlib
import json
import os
import re
import threading
import time
from typing import Any, Optional

from app.core.openai.openai_client import get_openai_client
from app.CloudIAC.models.infra.core import (
    Blueprint,
    InfraSpec,
    ProviderTarget,
    SecurityConstraints,
    CostConstraints,
)
from app.prompts.loader import load_prompt
from app.CloudIAC.services.infra.golden_module_selector_service import select_golden_modules
from app.CloudIAC.services.infra.repo_scanner_service import scan_repo

# Cache InfraSpec por hash
_INFRA_SPEC_CACHE: dict[str, tuple[float, InfraSpec]] = {}
_INFRA_SPEC_CACHE_LOCK = threading.Lock()
INFRA_SPEC_CACHE_TTL_SEC = int(os.getenv("INFRA_SPEC_CACHE_TTL_SEC", "600"))
INFRA_SPEC_CACHE_MAX = 200
PROMPT_VERSION = "1.0"


def _infra_spec_cache_key(
    input_data: str,
    repo_fingerprint: str,
    prompt_version: str,
) -> str:
    return hashlib.sha256(
        f"{input_data[:500]}|{repo_fingerprint}|{prompt_version}".encode("utf-8")
    ).hexdigest()


def _parse_infra_spec_json(raw: str) -> Optional[dict]:
    """Extrai JSON da resposta do LLM."""
    raw = (raw or "").strip()
    if "```" in raw:
        m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw)
        if m:
            raw = m.group(1)
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def build_infra_spec(
    tenant_id: str,
    id_requisicao: str,
    root_path: str,
    user_request: Optional[str] = None,
    backend_context: Optional[dict] = None,
    structure_context: Optional[dict] = None,
    providers: Optional[list[str]] = None,
    envs: Optional[list[str]] = None,
    use_cache: bool = True,
) -> InfraSpec:
    """
    Constrói InfraSpec a partir do contexto do repo e user_request.
    Usa cache por hash(input + prompt_version + repo_fingerprint).
    LLM só quando necessário (cache miss).
    """
    repo_ctx = scan_repo(root_path, use_cache=use_cache)
    fingerprint = repo_ctx.get("fingerprint", "")
    input_data = json.dumps({
        "user_request": user_request or "",
        "backend": backend_context or {},
        "structure": structure_context or {},
        "providers": providers or ["aws"],
        "envs": envs or ["dev"],
    }, sort_keys=True)

    cache_key = _infra_spec_cache_key(input_data, fingerprint, PROMPT_VERSION)
    if use_cache:
        with _INFRA_SPEC_CACHE_LOCK:
            if cache_key in _INFRA_SPEC_CACHE:
                ts, cached = _INFRA_SPEC_CACHE[cache_key]
                if time.time() - ts <= INFRA_SPEC_CACHE_TTL_SEC:
                    return cached.model_copy(update={"tenant_id": tenant_id, "id_requisicao": id_requisicao})
                del _INFRA_SPEC_CACHE[cache_key]

    # Chamada LLM
    prompt_content = load_prompt("infra/infra_spec")
    prompt_content = prompt_content.replace("{repo_context}", json.dumps(repo_ctx, indent=2)[:3000])
    prompt_content = prompt_content.replace("{user_request}", user_request or "Analise o repositório e sugira infraestrutura.")
    prompt_content = prompt_content.replace("{backend_context}", json.dumps(backend_context or {}, indent=2)[:1500])
    prompt_content = prompt_content.replace("{structure_context}", json.dumps(structure_context or {}, indent=2)[:1500])

    client = get_openai_client()
    raw = client.generate_text(prompt_content, use_fast_model=True)

    parsed = _parse_infra_spec_json(raw)
    if not parsed:
        parsed = _default_infra_spec(providers or ["aws"])

    providers_list = parsed.get("providers") or [{"provider": "aws", "region": "us-east-1", "env": "dev"}]
    provider_targets = [
        ProviderTarget(
            provider=p.get("provider", "aws"),
            region=p.get("region"),
            env=p.get("env"),
        )
        for p in providers_list
        if isinstance(p, dict)
    ]
    if not provider_targets:
        provider_targets = [ProviderTarget(provider="aws", region="us-east-1", env="dev")]

    blueprint_data = parsed.get("blueprint")
    blueprint = None
    if isinstance(blueprint_data, dict):
        blueprint = Blueprint(
            blueprint_id=blueprint_data.get("blueprint_id", "default"),
            name=blueprint_data.get("name", "Default"),
            description=blueprint_data.get("description"),
            stack_pattern=blueprint_data.get("stack_pattern") or [],
        )

    security_data = parsed.get("security") or {}
    security = SecurityConstraints(
        no_public_ip_default=security_data.get("no_public_ip_default", True),
        no_0_0_0_0_ports=security_data.get("no_0_0_0_0_ports", True),
        encryption_at_rest=security_data.get("encryption_at_rest", True),
        network_segmentation=security_data.get("network_segmentation", True),
        required_tags=security_data.get("required_tags") or ["Environment", "Project", "ManagedBy"],
    )

    cost_data = parsed.get("cost") or {}
    cost = CostConstraints(
        budget_max=cost_data.get("budget_max"),
        prefer_right_sizing=cost_data.get("prefer_right_sizing", True),
        prefer_spot_preemptible=cost_data.get("prefer_spot_preemptible", False),
        regions_suggested=cost_data.get("regions_suggested") or [],
    )

    spec = InfraSpec(
        tenant_id=tenant_id,
        id_requisicao=id_requisicao,
        providers=provider_targets,
        envs=parsed.get("envs") or ["dev"],
        resources=parsed.get("resources") or ["networking", "compute", "storage", "iam", "observability"],
        blueprint=blueprint,
        golden_modules=[],  # preenchido pelo select_golden_modules
        security=security,
        cost=cost,
        user_request=user_request,
        backend_context=backend_context,
        structure_context=structure_context,
    )

    spec.golden_modules = select_golden_modules(spec)

    with _INFRA_SPEC_CACHE_LOCK:
        if len(_INFRA_SPEC_CACHE) >= INFRA_SPEC_CACHE_MAX:
            by_ts = sorted(_INFRA_SPEC_CACHE.items(), key=lambda x: x[1][0])
            for k, _ in by_ts[: INFRA_SPEC_CACHE_MAX // 2]:
                del _INFRA_SPEC_CACHE[k]
        _INFRA_SPEC_CACHE[cache_key] = (time.time(), spec)

    return spec


def _default_infra_spec(providers: list[str]) -> dict:
    return {
        "providers": [{"provider": p, "region": "us-east-1" if p == "aws" else "eastus" if p == "azure" else "us-central1", "env": "dev"} for p in providers],
        "envs": ["dev"],
        "resources": ["networking", "compute", "storage", "iam", "observability"],
        "blueprint": {"blueprint_id": "default", "name": "Default", "description": "Padrão", "stack_pattern": []},
        "golden_modules": [],
        "security": {"no_public_ip_default": True, "no_0_0_0_0_ports": True, "encryption_at_rest": True, "required_tags": ["Environment", "Project", "ManagedBy"]},
        "cost": {"budget_max": None, "prefer_right_sizing": True, "regions_suggested": []},
    }
