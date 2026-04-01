#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮11 – Teste Automatizado Local❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from utils.log_manager import add_log
from services.test_runner_service.test_runner_service import run_automated_test
from models.pipeline_models.pipeline_models import (
    TesteAutomatizadoRequest,
    TesteAutomatizadoResponse,
    RelatorioTestes,
)


def run_teste_automatizado(req: TesteAutomatizadoRequest) -> TesteAutomatizadoResponse:
    """
    Executa testes no backend/ambiente (venv ou docker).
    Cruza id_requisicao + retornos de criar-estrutura/codigo/tela; não interrompe em falha;
    registra logs e retorna relatório (status, erros, vulnerabilidades, logs).
    """
    add_log("info", f"[teste-automatizado] Iniciando para id_requisicao={req.id_requisicao}", "pipeline")
    logs: list[str] = []
    erros: list[str] = []
    vulnerabilidades: list[str] = []

    # Run automático (venv/docker) – reutiliza test_runner
    test_resp = run_automated_test(
        root_path=req.root_path,
        log_type="info",
        prefer_docker=req.prefer_docker,
    )
    logs.extend(test_resp.logs or [])
    logs.append(f"Teste run: {'OK' if test_resp.success else 'FALHA'} – {test_resp.message}")

    if not test_resp.success:
        erros.append(test_resp.message)
        if test_resp.details:
            erros.append(test_resp.details[:500])

    # Status do relatório (não para execução; apenas classificação)
    if not erros and not vulnerabilidades:
        status = "aprovado"
    elif erros and not vulnerabilidades:
        status = "parcialmente aprovado"
    else:
        status = "parcialmente aprovado" if erros else "aprovado"
    if erros and not test_resp.success:
        status = "parcialmente aprovado"

    relatorio = RelatorioTestes(
        status=status,
        erros=erros,
        vulnerabilidades=vulnerabilidades,
        logs=logs,
    )
    return TesteAutomatizadoResponse(
        id_requisicao=req.id_requisicao,
        relatorio_testes=relatorio,
    )
