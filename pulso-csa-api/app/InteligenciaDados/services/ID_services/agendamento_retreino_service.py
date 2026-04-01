# Serviço de agendamento e execução de retreino (ID)
import logging
import time
import uuid
from copy import deepcopy
from typing import Any, Dict, List, Optional

from app.InteligenciaDados.models.ID_models.agendamento_retreino_models import (
    AgendamentoRetreinoInput,
    AgendamentoRetreinoOutput,
    ExecutarRetreinoOutput,
)
from app.InteligenciaDados.models.ID_models.modelos_ml_models import ModelosMLInput, ModelosMLOutput
from app.InteligenciaDados.services.ID_services.modelos_ml_service import ModelosMLService
from app.InteligenciaDados.storage.id_artifacts.id_artifacts_io import (
    load_agendamentos,
    pop_agendamento_por_id,
    save_agendamento,
)
from app.storage.database.ID_database.database_agendamentos import (
    salvar_agendamento as salvar_agendamento_bd,
    buscar_agendamento_por_id as buscar_agendamento_bd,
    remover_agendamento_por_id as remover_agendamento_bd,
    listar_agendamentos_pendentes as listar_agendamentos_bd,
)
from app.utils.retreino_lock import obter_lock_retreino, liberar_lock_retreino
import asyncio

logger = logging.getLogger(__name__)


class AgendamentoRetreinoService:
    """
    Registra agendamentos de retreino (estrutura mínima).
    A execução real deve ser disparada por cron/external caller em POST /executar-retreino-agendado.
    """

    def __init__(self) -> None:
        self._modelos_ml = ModelosMLService()

    def agendar(self, payload: AgendamentoRetreinoInput) -> AgendamentoRetreinoOutput:
        agendamento_id = str(uuid.uuid4())[:8]
        ag = {
            "agendamento_id": agendamento_id,
            "id_requisicao": payload.id_requisicao,
            "usuario": payload.usuario or "default",
            "dataset_ref": payload.dataset_ref,
            "variavel_alvo": payload.variavel_alvo,
            "tipo_problema": payload.tipo_problema or "classificacao",
            "cron_expr": payload.cron_expr,
            "proxima_execucao_em_minutos": payload.proxima_execucao_em_minutos,
            "created_at": time.time(),
        }
        # Salvar em BD (estrutura mínima) e fallback para arquivo
        try:
            asyncio.run(salvar_agendamento_bd(deepcopy(ag)))
        except Exception as e:
            logger.warning("Falha ao salvar agendamento em BD, usando arquivo: %s", e)
            save_agendamento(ag)
        return AgendamentoRetreinoOutput(
            id_requisicao=payload.id_requisicao,
            agendamento_id=agendamento_id,
            mensagem="Agendamento registrado. Chame POST /inteligencia-dados/executar-retreino-agendado com body {'agendamento_id': '" + agendamento_id + "'} para executar o retreino (ou use um cron externo).",
        )

    def executar_um(self, agendamento_id: str) -> ExecutarRetreinoOutput:
        """Remove o agendamento da fila e executa o retreino (com lock para evitar duplicação)."""
        # Lock para evitar execução duplicada/concorrente
        if not obter_lock_retreino(agendamento_id):
            return ExecutarRetreinoOutput(agendamento_id=agendamento_id, executado=False, erro="Retreino já está em execução (lock ativo).")
        ag = None
        try:
            # Tentar buscar do BD primeiro, fallback para arquivo
            try:
                ag = asyncio.run(buscar_agendamento_bd(agendamento_id))
                if ag:
                    ag = asyncio.run(remover_agendamento_bd(agendamento_id))
            except Exception as e:
                logger.debug("Falha ao buscar do BD, usando arquivo: %s", e)
                ag = pop_agendamento_por_id(agendamento_id)
            if not ag:
                liberar_lock_retreino(agendamento_id)
                return ExecutarRetreinoOutput(agendamento_id=agendamento_id, executado=False, erro="Agendamento não encontrado ou já executado.")
            out: ModelosMLOutput = self._modelos_ml.run(
                ModelosMLInput(
                    id_requisicao=ag["id_requisicao"],
                    usuario=ag.get("usuario"),
                    dataset_ref=ag["dataset_ref"],
                    variavel_alvo=ag["variavel_alvo"],
                    tipo_problema=ag.get("tipo_problema", "classificacao"),
                )
            )
            resultado = ExecutarRetreinoOutput(
                agendamento_id=agendamento_id,
                executado=True,
                model_ref_novo=out.model_ref,
                modelo_ml=out.modelo_ml,
            )
            liberar_lock_retreino(agendamento_id)
            return resultado
        except Exception as e:
            logger.warning("Retreino agendado falhou: %s", e)
            if ag:  # Coloca de volta na fila se havia agendamento
                save_agendamento(ag)
            liberar_lock_retreino(agendamento_id)
            from app.utils.path_validation import is_production
            err_msg = "Erro ao executar retreino." if is_production() else str(e)
            return ExecutarRetreinoOutput(agendamento_id=agendamento_id, executado=False, erro=err_msg)

    def listar_pendentes(self) -> List[Dict[str, Any]]:
        """Lista agendamentos ainda não executados (BD primeiro, fallback arquivo)."""
        try:
            return asyncio.run(listar_agendamentos_bd())
        except Exception as e:
            logger.debug("Falha ao listar do BD, usando arquivo: %s", e)
            return load_agendamentos()
