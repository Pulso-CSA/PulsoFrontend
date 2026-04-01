#━━━━━━━━━❮Inteligência de Dados – Chat❯━━━━━━━━━
# POST /chat: orquestrador em linguagem natural; previsões no próprio retorno.
import asyncio
import os
from fastapi import APIRouter, Depends, Request, status

from app.core.auth import auth_and_rate_limit
from app.core.entitlement.deps import require_valid_access
from app.InteligenciaDados.models.ID_models.id_chat_models import IDChatInput, IDChatOutput
from app.InteligenciaDados.services.ID_services.id_chat_service import IDChatService
from services.chat_history_service import persist_chat
from app.utils.log_manager import add_log

router = APIRouter(
    prefix="/inteligencia-dados",
    tags=["Inteligência de Dados – Chat"],
)

_service = IDChatService()


def _is_production() -> bool:
    return (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENV", "").lower()) == "production"


@router.post(
    "/chat",
    response_model=IDChatOutput,
    status_code=status.HTTP_200_OK,
)
async def chat_id(
    payload: IDChatInput,
    request: Request,
    user: dict = Depends(require_valid_access),
) -> IDChatOutput:
    """
    Chat de alto nível: envie uma mensagem em linguagem natural e o sistema executa
    as etapas necessárias (análise estatística, treino de modelo, previsão) e devolve
    a resposta com previsões no próprio retorno quando aplicável.
    Requer autenticação (Bearer token).
    """
    request_id = getattr(request.state, "request_id", None) or "unknown"
    try:
        if not payload.usuario:
            payload.usuario = user.get("email") or user.get("_id")
        # run_in_executor: evita bloquear event loop (IDChatService.run é síncrono)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _service.run, payload)
        tenant_id = user.get("_id") or user.get("email") or ""
        asyncio.create_task(
            persist_chat(
                tenant_id=tenant_id,
                usuario_id=payload.usuario or tenant_id,
                service_id="id",
                session_id=payload.id_requisicao,
                mensagem_user=payload.mensagem,
                mensagem_assistant=result.resposta_texto,
                dataset_ref=result.dataset_ref,
                model_ref=result.model_ref,
            )
        )
        return result
    except Exception as e:
        add_log("error", f"Erro no chat ID request_id={request_id}: {type(e).__name__}: {e}", "id_chat")
        # Retorna 200 com mensagem de erro em resposta_texto para o frontend exibir (evita "Algo deu errado")
        msg = "Erro no chat. Tente novamente ou contate o suporte." if _is_production() else str(e)
        return IDChatOutput(
            id_requisicao=payload.id_requisicao,
            resposta_texto=f"**Ocorreu um erro.** {msg}",
            etapas_executadas=[],
            sugestao_proximo_passo="Tente novamente ou conecte-se à base (botão Conexão) antes de usar os botões de sugestão.",
        )
