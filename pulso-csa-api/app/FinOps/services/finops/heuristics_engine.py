#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Heurísticas FinOps/CloudOps/SecOps❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
Motor de heurísticas determinísticas (policies versionáveis).
Produz candidatos e evidências para o LLM transformar em narrativa.
"""
from typing import Any, Optional


def run_heuristics(
    billing: dict[str, Any],
    inventory: dict[str, Any],
    metrics: dict[str, Any],
    provider: str,
    quick_win_mode: str,
    guardrails_mode: bool,
) -> list[dict[str, Any]]:
    """Executa heurísticas e retorna lista de candidatos."""
    candidates: list[dict[str, Any]] = []

    # FinOps: rightsizing, commitments, storage
    total = billing.get("total_cost_usd") or billing.get("total_cost")
    if total is not None and total > 0:
        candidates.append({
            "eixo": "FinOps",
            "categoria": "custo",
            "acao": "Revisar custo total",
            "evidencia": f"Custo total: ${total:.2f} USD no período",
            "confianca": "alta",
            "economia_estimada_pct": None,
        })

    # Inventário: EC2/VMs ociosas
    ec2 = inventory.get("ec2", []) or inventory.get("vms", [])
    stopped = [r for r in ec2 if isinstance(r, dict) and r.get("state", "").lower() in ("stopped", "deallocated")]
    running = [r for r in ec2 if isinstance(r, dict) and r.get("state", "").lower() in ("running", "")]
    if stopped:
        candidates.append({
            "eixo": "FinOps",
            "categoria": "compute",
            "acao": "Revisar instâncias paradas",
            "evidencia": f"{len(stopped)} instância(s) parada(s): possível remoção ou desligamento",
            "confianca": "alta",
            "economia_estimada_pct": "5-15",
        })
    if running:
        types = [r.get("type") or r.get("size") or r.get("machine_type") for r in running if isinstance(r, dict)]
        if any("t2" in str(t) or "t3" in str(t) for t in types if t):
            candidates.append({
                "eixo": "FinOps",
                "categoria": "rightsizing",
                "acao": "Avaliar troca t2/t3 para graviton ou burstable",
                "evidencia": "Instâncias t2/t3 detectadas; avaliar família ARM ou burstable",
                "confianca": "média",
                "economia_estimada_pct": "10-20",
            })

    # Storage: S3, buckets
    s3_buckets = inventory.get("s3_buckets", 0) or inventory.get("buckets", 0)
    if s3_buckets and s3_buckets > 5:
        candidates.append({
            "eixo": "FinOps",
            "categoria": "storage",
            "acao": "Revisar lifecycle e storage class dos buckets",
            "evidencia": f"{s3_buckets} bucket(s): avaliar Standard/IA/Glacier e lifecycle",
            "confianca": "média",
            "economia_estimada_pct": "15-30",
        })

    # CloudOps: métricas CPU
    avg_cpu = metrics.get("avg_cpu_utilization") if isinstance(metrics.get("avg_cpu_utilization"), (int, float)) else None
    if avg_cpu is not None:
        if avg_cpu < 15:
            candidates.append({
                "eixo": "CloudOps",
                "categoria": "performance",
                "acao": "CPU baixo: avaliar downsizing",
                "evidencia": f"CPU médio: {avg_cpu}%",
                "confianca": "alta",
                "economia_estimada_pct": "20-40",
            })
        elif avg_cpu > 80:
            candidates.append({
                "eixo": "CloudOps",
                "categoria": "performance",
                "acao": "CPU alto: possível bottleneck",
                "evidencia": f"CPU médio: {avg_cpu}%",
                "confianca": "alta",
                "economia_estimada_pct": None,
            })

    # SecOps: recomendações genéricas
    candidates.append({
        "eixo": "SecOps",
        "categoria": "hardening",
        "acao": "Revisar IAM least privilege",
        "evidencia": "Auditoria de permissões recomendada",
        "confianca": "média",
        "economia_estimada_pct": None,
    })

    # Quick wins
    if quick_win_mode == "quick_wins":
        candidates.append({
            "eixo": "QuickWin",
            "categoria": "quick_wins",
            "acao": "Snapshots órfãos, storage class, egress óbvio, idle LB",
            "evidencia": "Verificar candidatos de quick wins na coleta",
            "confianca": "alta",
            "economia_estimada_pct": "5-15",
        })
    if quick_win_mode == "compare_regions":
        candidates.append({
            "eixo": "QuickWin",
            "categoria": "compare_regions",
            "acao": "Comparar custo por região",
            "evidencia": "Comparar regiões e sugerir realocação",
            "confianca": "média",
            "economia_estimada_pct": "10-25",
        })
    if quick_win_mode == "auto_shutdown_policies":
        candidates.append({
            "eixo": "QuickWin",
            "categoria": "auto_shutdown",
            "acao": "Políticas de desligamento para dev/test",
            "evidencia": "Sugerir policies para desligar fora de horário",
            "confianca": "alta",
            "economia_estimada_pct": "20-40",
        })

    # Guardrails
    if guardrails_mode:
        candidates.append({
            "eixo": "Guardrails",
            "categoria": "budget",
            "acao": "Sugerir budgets por escopo",
            "evidencia": "Definir thresholds e alertas",
            "confianca": "alta",
            "economia_estimada_pct": None,
        })

    return candidates


def build_guardrails_recommendations(
    billing: dict[str, Any],
    anomaly_threshold_pct: Optional[float] = None,
    anomaly_window_days: Optional[int] = None,
) -> list[dict[str, Any]]:
    """Gera recomendações de guardrails (budgets, anomalias, alertas)."""
    recs: list[dict[str, Any]] = []
    threshold = anomaly_threshold_pct or 30
    window = anomaly_window_days or 7
    recs.append({
        "tipo": "budget",
        "descricao": "Definir budget por conta/subscription/projeto",
        "detalhe": "Alertar ao atingir 80% e 100% do budget",
    })
    recs.append({
        "tipo": "anomalia",
        "descricao": f"Desvio de {threshold}% vs média {window} dias",
        "detalhe": "Alertar ao detectar spike por serviço",
    })
    recs.append({
        "tipo": "playbook",
        "descricao": "Runbook para resposta a anomalias",
        "detalhe": "Quem recebe, severidade, playbook",
    })
    return recs
