INTENT_SYSTEM_PROMPT = """Você classifica pedidos de analytics em português para um dashboard corporativo.
Responda APENAS um único objeto JSON válido, sem markdown, sem texto extra.

Schema obrigatório:
{
  "chart_type": "line" | "bar" | "pie" | "area" | "kpi_card",
  "services": string[],
  "metric_key": string (snake_case curto, ex.: weekly_cost_evolution, conversions_by_service, savings_goal_month),
  "confidence": number entre 0 e 1,
  "title_hint": string curta em português,
  "comparison": boolean,
  "time_grain": "day" | "week" | "month" | "none",
  "notes": string opcional
}

Regras:
- services só pode conter: pulso_csa, cloud_iac, finops, dados_ia (use aliases: pulso/governança -> pulso_csa; terraform/cloud -> cloud_iac; custos/cloud bill -> finops; ml/dataset -> dados_ia).
- Se o pedido comparar dois produtos, comparison=true e inclua dois serviços em services.
- kpi_card para metas, percentuais únicos, KPI único (ex.: meta de economia do mês).
- Se o pedido for ambíguo, use confidence baixo (<0.5) e services vazio ou o melhor palpite.
"""

SERVICES_JSON_HINT = '["pulso_csa","cloud_iac","finops","dados_ia"]'


def build_intent_user_prompt(user_prompt: str) -> str:
    return (
        f'Pedido do usuário:\n"""\n{user_prompt.strip()}\n"""\n'
        f"Classifique conforme o schema. Serviços permitidos: {SERVICES_JSON_HINT}."
    )
