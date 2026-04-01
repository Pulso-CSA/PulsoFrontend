#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Router – Tela Teste (itens 9 e 10)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import asyncio
from fastapi import APIRouter, Depends, HTTPException

from core.auth import auth_and_rate_limit
from utils.log_manager import add_log
from utils.path_validation import sanitize_root_path, is_production

from models.tela_teste_models.tela_teste_models import (
    AnaliseTelaTesteRequest,
    AnaliseTelaTesteResponse,
    TelaTesteSpec,
    CriarTelaTesteRequest,
    CriarTelaTesteResponse,
)
from services.tela_teste_services.analise_tela_teste_service import run_analise_tela_teste
from services.tela_teste_services.criar_tela_teste_service import run_criar_tela_teste

router = APIRouter(tags=["Camada 3 – Tela Teste (FrontendEX)"])
SOURCE = "tela_teste"


#━━━━━━━━━❮9 – Análise de Tela Teste❯━━━━━━━━━

@router.post("/analise-tela-teste", response_model=AnaliseTelaTesteResponse)
async def analise_tela_teste(payload: AnaliseTelaTesteRequest, user: dict = Depends(auth_and_rate_limit)):
    """
    Analisa como deve ser a tela de testes para QA funcional.
    Input: id_requisicao + (root_path ou retornos de criar-estrutura e criar-codigo).
    Saída: layout, funcionalidades, testes_cruciais, dados_ficticios.
    A tela será implementada em FrontendEX (Streamlit, localhost:3000).
    """
    root_path = sanitize_root_path(payload.root_path) if payload.root_path else None
    if payload.root_path and not root_path:
        raise HTTPException(status_code=400, detail={"code": "ROOT_PATH_INVALID", "message": "root_path inválido ou fora do permitido."})
    root_path = root_path or payload.root_path
    add_log("info", f"analise-tela-teste iniciada | id_requisicao={payload.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: run_analise_tela_teste(
                id_requisicao=payload.id_requisicao,
                root_path=root_path,
                estrutura_criada=payload.estrutura_criada,
                codigo_implementado=payload.codigo_implementado,
            ),
        )
        add_log("info", f"analise-tela-teste concluída | id_requisicao={payload.id_requisicao}", SOURCE)
        return AnaliseTelaTesteResponse(
            id_requisicao=result["id_requisicao"],
            tela_teste=TelaTesteSpec(**result["tela_teste"]),
        )
    except FileNotFoundError:
        add_log("warning", f"analise-tela-teste arquivo não encontrado | id_requisicao={payload.id_requisicao}", SOURCE)
        raise HTTPException(status_code=404, detail={"code": "FILE_NOT_FOUND", "message": "Arquivo não encontrado."})
    except Exception as e:
        add_log("error", f"analise-tela-teste falhou: {type(e).__name__}", SOURCE)
        msg = "Erro na análise de tela teste." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "ANALISE_TELA_TESTE_FAILED", "message": msg})


#━━━━━━━━━❮10 – Criação da Tela Teste (FrontendEX)❯━━━━━━━━━

@router.post("/criar-tela-teste", response_model=CriarTelaTesteResponse)
async def criar_tela_teste(payload: CriarTelaTesteRequest, user: dict = Depends(auth_and_rate_limit)):
    """
    Cria a pasta FrontendEX na raiz do usuário com app Streamlit modularizado,
    consumindo os endpoints do backend e subindo em localhost:3000.
    Input: id_requisicao, root_path, tela_teste (saída de /analise-tela-teste).
    """
    root_path = sanitize_root_path(payload.root_path) if payload.root_path else None
    if payload.root_path and not root_path:
        raise HTTPException(status_code=400, detail={"code": "ROOT_PATH_INVALID", "message": "root_path inválido ou fora do permitido."})
    root_path = root_path or payload.root_path
    add_log("info", f"criar-tela-teste iniciada | id_requisicao={payload.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: run_criar_tela_teste(
                id_requisicao=payload.id_requisicao,
                root_path=root_path,
                tela_teste=payload.tela_teste.model_dump(),
                backend_base_url=payload.backend_base_url or "http://localhost:8000",
            ),
        )
        add_log("info", f"criar-tela-teste concluída | id_requisicao={payload.id_requisicao} pasta=FrontendEX", SOURCE)
        return CriarTelaTesteResponse(
            id_requisicao=result["id_requisicao"],
            tela_teste_criada=result["tela_teste_criada"],
            relatorio=result["relatorio"],
        )
    except FileNotFoundError:
        add_log("warning", f"criar-tela-teste root_path não encontrado | id_requisicao={payload.id_requisicao}", SOURCE)
        raise HTTPException(status_code=404, detail={"code": "FILE_NOT_FOUND", "message": "root_path não encontrado."})
    except Exception as e:
        add_log("error", f"criar-tela-teste falhou: {type(e).__name__}", SOURCE)
        msg = "Erro ao criar tela teste." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "CRIAR_TELA_TESTE_FAILED", "message": msg})
