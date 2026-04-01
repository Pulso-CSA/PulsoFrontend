#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Serviço – Análise de Tela Teste (item 9)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
import json
from typing import Dict, List, Any, Optional

# openai está em api/app/core/openai/ (compartilhado)
try:
    from core.openai.openai_client import get_openai_client
except ImportError:
    from app.core.openai.openai_client import get_openai_client
from app.prompts.loader import load_prompt
from utils.log_manager import add_log


def _build_context(
    id_requisicao: str,
    root_path: Optional[str],
    estrutura_criada: Optional[Dict[str, Any]],
    codigo_implementado: Optional[Dict[str, Any]],
) -> str:
    """Monta o contexto para o LLM a partir dos payloads ou dos relatórios em disco."""
    parts = []

    if estrutura_criada:
        parts.append("Estrutura criada (criar-estrutura):")
        parts.append(json.dumps(estrutura_criada, ensure_ascii=False, indent=2))
    if codigo_implementado:
        parts.append("Código implementado (criar-codigo):")
        parts.append(json.dumps(codigo_implementado, ensure_ascii=False, indent=2))

    if root_path and (not estrutura_criada or not codigo_implementado):
        reports_dir = os.path.join(root_path, "reports", id_requisicao)
        base_dir = os.path.join(root_path, id_requisicao, "generated_code")
        manifest_path = os.path.join(base_dir, "structure_manifest.json")
        backend_path = os.path.join(reports_dir, "02_backend_report.json")
        for label, path in [
            ("Manifesto da estrutura", manifest_path),
            ("Relatório de backend", backend_path),
        ]:
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    parts.append(f"{label}:")
                    parts.append(json.dumps(data, ensure_ascii=False, indent=2))
                except Exception as e:
                    add_log("warning", f"analise_tela_teste: falha ao ler {path}: {e}", "tela_teste")

    return "\n\n".join(parts) if parts else "Nenhum contexto de estrutura ou backend disponível."


def run_analise_tela_teste(
    id_requisicao: str,
    root_path: Optional[str] = None,
    estrutura_criada: Optional[Dict[str, Any]] = None,
    codigo_implementado: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Gera a especificação da tela de teste (layout, funcionalidades, testes cruciais, dados fictícios).
    A tela será Streamlit, modularizada em FrontendEX, porta 3000, consumindo endpoints do usuário.
    """
    contexto = _build_context(id_requisicao, root_path, estrutura_criada, codigo_implementado)

    template = load_prompt("tela_teste/analise_tela_teste")
    prompt = template.replace("{contexto}", contexto)

    client = get_openai_client()
    raw = client.generate_text(prompt, system_prompt=None, use_fast_model=True)

    # Limpa possíveis blocos markdown
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    default_spec = {
        "layout": "dashboard simples em 3 colunas",
        "funcionalidades": ["login", "consulta de dados"],
        "testes_cruciais": ["login com credenciais inválidas", "consulta sem autenticação"],
        "dados_ficticios": {"usuarios": ["teste@email.com"], "senhas_teste": ["senha123"]},
    }

    try:
        spec = json.loads(text)
        if isinstance(spec, dict):
            default_spec.update({k: v for k, v in spec.items() if k in default_spec})
    except Exception as e:
        add_log("warning", f"analise_tela_teste: JSON inválido, usando default: {e}", "tela_teste")

    return {
        "id_requisicao": id_requisicao,
        "tela_teste": default_spec,
    }
