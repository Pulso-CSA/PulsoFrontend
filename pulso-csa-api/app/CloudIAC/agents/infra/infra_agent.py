#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Infra Agent – pipeline Analyze→Generate→Validate→Deploy❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from typing import Any, Optional

from app.CloudIAC.models.infra.core import InfraSpec
from app.CloudIAC.models.infra.reports import (
    ApplySummary,
    CostReport,
    PolicyReport,
    ProviderDiffReport,
    ValidationReport,
)
from app.CloudIAC.services.infra.cost_guardrails_service import estimate_cost
from app.CloudIAC.services.infra.deploy_token_service import (
    CONFIRM_PHRASE,
    generate_deploy_token,
    validate_confirm_phrase,
    validate_deploy_token,
)
from app.CloudIAC.services.infra.infra_spec_builder_service import build_infra_spec
from app.CloudIAC.services.infra.policy_runner_service import run_policy_check
from app.CloudIAC.services.infra.provider_diff_service import get_provider_diff_report
from app.CloudIAC.services.infra.repo_scanner_service import scan_repo
from app.CloudIAC.services.infra.terraform_runner_service import run_terraform
from app.CloudIAC.services.infra.terraform_stack_generator_service import (
    compute_terraform_tree_hash,
    ensure_terraform_structure,
    get_terraform_base_path,
)


def run_analyze(
    root_path: str,
    tenant_id: str,
    id_requisicao: str,
    user_request: Optional[str] = None,
    providers: Optional[list[str]] = None,
    envs: Optional[list[str]] = None,
    backend_context: Optional[dict] = None,
    structure_context: Optional[dict] = None,
) -> dict[str, Any]:
    """
    Pipeline: analyze.
    Saída: repo_context, infra_spec_draft, blueprint_suggestion, cost_estimate, risk_report, provider_diff_report, next_actions.
    """
    repo_context = scan_repo(root_path, use_cache=True)
    spec = build_infra_spec(
        tenant_id=tenant_id,
        id_requisicao=id_requisicao,
        root_path=root_path,
        user_request=user_request,
        backend_context=backend_context,
        structure_context=structure_context,
        providers=providers,
        envs=envs,
        use_cache=True,
    )
    providers_list = [p.provider for p in spec.providers]
    cost_est = estimate_cost(spec.resources, providers_list)
    provider_diff = get_provider_diff_report(providers_list)

    return {
        "repo_context": repo_context,
        "infra_spec_draft": spec.model_dump(),
        "blueprint_suggestion": spec.blueprint.model_dump() if spec.blueprint else None,
        "cost_estimate": cost_est.model_dump(),
        "risk_report": {"note": "Validação de risco em /infra/validate"},
        "provider_diff_report": [p.model_dump() for p in provider_diff],
        "next_actions": ["POST /infra/generate para gerar artefatos Terraform", "POST /infra/validate para validar e obter deploy_token"],
    }


def run_generate(
    root_path: str,
    tenant_id: str,
    id_requisicao: str,
    infra_spec: Optional[InfraSpec] = None,
    user_request: Optional[str] = None,
    backend_context: Optional[dict] = None,
    structure_context: Optional[dict] = None,
) -> dict[str, Any]:
    """
    Pipeline: generate.
    Saída: artifacts, terraform_tree, commands, policy_report.
    """
    if not infra_spec:
        infra_spec = build_infra_spec(
            tenant_id=tenant_id,
            id_requisicao=id_requisicao,
            root_path=root_path,
            user_request=user_request,
            backend_context=backend_context,
            structure_context=structure_context,
            use_cache=True,
        )

    result = ensure_terraform_structure(root_path, infra_spec)
    terraform_base = result["terraform_base"]
    policy_report = run_policy_check(terraform_base)

    return {
        "artifacts": result.get("created", []),
        "terraform_tree": {"base": terraform_base, "providers": result.get("providers", []), "envs": result.get("envs", [])},
        "commands": ["terraform fmt", "terraform validate", "terraform plan"],
        "policy_report": policy_report.model_dump(),
    }


def run_validate(
    root_path: str,
    tenant_id: str,
    id_requisicao: str,
    terraform_path: Optional[str] = None,
) -> dict[str, Any]:
    """
    Pipeline: validate.
    Executa fmt, validate, plan (dry-run) + policy-as-code.
    Saída: validation_report, plan_summary, policy_report, deploy_token, confirm_phrase.
    """
    base = terraform_path or get_terraform_base_path(root_path)
    repo_ctx = scan_repo(root_path, use_cache=True)
    fingerprint = repo_ctx.get("fingerprint", "")
    terraform_hash = compute_terraform_tree_hash(base)

    policy_report = run_policy_check(base)
    from pathlib import Path
    stack_dirs = list(Path(base).glob("stacks/*/*"))
    workdir = str(stack_dirs[0]) if stack_dirs else base
    init_rc, _, _ = run_terraform(workdir, "init")
    fmt_rc, fmt_out, fmt_err = run_terraform(workdir, "fmt")
    validate_rc, validate_out, validate_err = run_terraform(workdir, "validate")
    plan_rc, plan_out, plan_err = run_terraform(workdir, "plan")

    validation_report = ValidationReport(
        fmt_ok=fmt_rc == 0,
        validate_ok=validate_rc == 0,
        plan_ok=plan_rc == 0,
        errors=[e for e in [fmt_err, validate_err, plan_err] if e],
        warnings=[],
    )

    plan_summary = {"changes": 0, "output_preview": plan_out[:1000] if plan_out else ""}

    providers_list = ["aws"]
    deploy_token = ""
    try:
        deploy_token = generate_deploy_token(
            tenant_id=tenant_id,
            id_requisicao=id_requisicao,
            env="dev",
            providers=providers_list,
            repo_fingerprint=fingerprint,
            terraform_tree_hash=terraform_hash,
        )
    except ValueError:
        pass

    return {
        "validation_report": validation_report.model_dump(),
        "plan_summary": plan_summary,
        "policy_report": policy_report.model_dump(),
        "deploy_token": deploy_token,
        "confirm_phrase": CONFIRM_PHRASE,
        "instruction": f"Para fazer deploy, use POST /infra/deploy com confirm=true, deploy_token e confirm_phrase='{CONFIRM_PHRASE}'",
    }


def run_deploy(
    root_path: str,
    tenant_id: str,
    id_requisicao: str,
    confirm: bool,
    deploy_token: Optional[str],
    confirm_phrase: Optional[str],
    terraform_path: Optional[str] = None,
    allow_policy_override: bool = False,
    override_reason: Optional[str] = None,
    budget_max: Optional[float] = None,
    allow_budget_override: bool = False,
) -> dict[str, Any]:
    """
    Pipeline: deploy (apenas quando confirm=true, token válido, frase correta).
    """
    if not confirm:
        return {"error": "Deploy requer confirm=true", "instruction": "Envie confirm=true no body"}
    if not deploy_token:
        return {"error": "deploy_token ausente", "instruction": "Execute POST /infra/validate para obter deploy_token"}
    if not validate_confirm_phrase(confirm_phrase):
        return {
            "error": "confirm_phrase incorreta",
            "instruction": f"Envie confirm_phrase='{CONFIRM_PHRASE}' (exatamente)",
        }

    base = terraform_path or get_terraform_base_path(root_path)
    repo_ctx = scan_repo(root_path, use_cache=False)
    fingerprint = repo_ctx.get("fingerprint", "")
    terraform_hash = compute_terraform_tree_hash(base)

    valid, err = validate_deploy_token(deploy_token, tenant_id, id_requisicao, fingerprint, terraform_hash)
    if not valid:
        return {"error": f"deploy_token inválido: {err}", "instruction": "Execute POST /infra/validate novamente"}

    policy_report = run_policy_check(base, allow_policy_override, override_reason)
    if not policy_report.passed and not allow_policy_override:
        return {"error": "Policy falhou", "policy_report": policy_report.model_dump()}

    from pathlib import Path
    stack_dirs = list(Path(base).glob("stacks/*/*"))
    workdir = str(stack_dirs[0]) if stack_dirs else base

    rc, out, err = run_terraform(workdir, "apply", auto_approve=True)
    success = rc == 0

    return {
        "apply_summary": ApplySummary(
            success=success,
            outputs_sanitized={},
            post_deploy_steps=["Verificar recursos na consola cloud", "Configurar alertas de custo"],
            errors=[err] if err else [],
        ).model_dump(),
    }
