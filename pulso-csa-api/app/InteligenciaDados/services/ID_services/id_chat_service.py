# Serviço Chat ID – orquestrador: interpreta mensagem e executa captura → tratamento → análise → modelo → previsão
import hashlib
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

from app.core.openai.openai_client import get_openai_client
from app.InteligenciaDados.models.ID_models.analise_estatistica_models import AnaliseEstatisticaInput, AnaliseEstatisticaOutput
from app.prompts.loader import load_prompt
from app.InteligenciaDados.models.ID_models.captura_dados_models import CapturaDadosInput, CapturaDadosOutput
from app.InteligenciaDados.models.ID_models.id_chat_models import IDChatInput, IDChatOutput
from app.InteligenciaDados.models.ID_models.modelos_ml_models import ModelosMLInput, ModelosMLOutput
from app.InteligenciaDados.models.ID_models.previsao_models import PrevisaoInput, PrevisaoOutput
from app.InteligenciaDados.models.ID_models.tratamento_limpeza_models import TratamentoLimpezaInput, TratamentoLimpezaOutput
from app.InteligenciaDados.services.ID_services.analise_estatistica_service import AnaliseEstatisticaService
from app.InteligenciaDados.services.ID_services.captura_dados_service import CapturaDadosService
from app.InteligenciaDados.services.ID_services.modelos_ml_service import ModelosMLService
from app.InteligenciaDados.services.ID_services.previsao_service import PrevisaoService
from app.InteligenciaDados.services.ID_services.tratamento_limpeza_service import TratamentoLimpezaService
from app.InteligenciaDados.storage.id_artifacts.id_artifacts_io import get_latest_dataset_ref, get_latest_model_ref, load_dataframe, load_model_metadata
from app.utils.db_config_validation import validar_db_config

logger = logging.getLogger(__name__)

# Cache de interpretação (hash mensagem+contexto -> intent); máx 100 entradas; TTL 10 min
_INTENT_CACHE: Dict[str, tuple[float, Dict[str, Any]]] = {}  # key -> (timestamp, data)
_INTENT_CACHE_MAX = 100
_INTENT_CACHE_TTL_SEC = int(os.getenv("ID_INTENT_CACHE_TTL_SEC", "600"))


class IDChatService:
    """
    Cientista de dados em alto nível: interpreta mensagem em linguagem natural,
    executa as etapas necessárias (estatística, treino, previsão) e devolve
    resposta unificada com previsões no próprio chat quando aplicável.
    """

    def __init__(self) -> None:
        self._llm = get_openai_client()
        self._captura = CapturaDadosService()
        self._analise_estatistica = AnaliseEstatisticaService()
        self._tratamento = TratamentoLimpezaService()
        self._modelos_ml = ModelosMLService()
        self._previsao = PrevisaoService()

    def run(self, payload: IDChatInput) -> IDChatOutput:
        mensagem = payload.mensagem.strip()
        id_req = payload.id_requisicao
        usuario = payload.usuario or "default"
        dataset_ref = payload.dataset_ref
        model_ref = payload.model_ref
        dados_para_prever = payload.dados_para_prever
        db_config = payload.db_config

        etapas: List[str] = []
        captura_falha_politica: Optional[str] = None  # validação allowlist (mensagem segura para o utilizador)
        analise_estatistica: Optional[Dict[str, Any]] = None
        modelo_ml: Optional[Dict[str, Any]] = None
        previsoes: Optional[List[Any]] = None
        sugestao: Optional[str] = None

        m_lower = mensagem.lower()
        # Retorno antecipado: pedidos de estrutura/correlações sem conexão (evita chamada LLM e erro genérico)
        _pede_estrutura_ou_correlacao = any(x in m_lower for x in [
            "estrutura", "tabelas", "volumes",
            "correlações", "correlacoes", "correlação", "correlacao",
            "ver estrutura", "calcular correlações", "calcular correlacoes",
            "correlações principais", "correlacoes principais", "principais correla",
        ])
        if not db_config and not dataset_ref and _pede_estrutura_ou_correlacao:
            msg_conexao = (
                "**Conecte-se primeiro à base de dados.**\n\n"
                "Para ver estrutura, tabelas, volumes ou calcular correlações:\n"
                "1. Clique no botão **Conexão** (canto superior)\n"
                "2. Preencha Host, Base, Usuário e Senha do seu banco\n"
                "3. Clique em **Aplicar**\n"
                "4. Depois envie novamente sua pergunta ou clique em \"Ver estrutura da base\" ou \"Calcular correlações principais\""
            )
            return IDChatOutput(
                id_requisicao=id_req,
                resposta_texto=msg_conexao,
                etapas_executadas=etapas,
                dataset_ref=dataset_ref,
                model_ref=model_ref,
                sugestao_proximo_passo="Conecte-se à base (botão Conexão) e envie novamente.",
            )

        # Interpretar intenção com LLM (com cache isolado por usuario + TTL)
        intent = self._interpretar_mensagem(mensagem, dataset_ref, model_ref, db_config, usuario)

        # Fallback: mensagens como "analise a base de dados" devem acionar fazer_estatistica mesmo se LLM errar
        if not intent.get("fazer_estatistica") and any(x in m_lower for x in ["analise", "analisar", "analise a base", "analise geral", "analise dos dados"]):
            if db_config or dataset_ref:
                intent["fazer_estatistica"] = True
        # "analise geral dos dados do banco" = captura + estatística
        if any(x in m_lower for x in ["analise geral", "analise dos dados do banco", "analise do banco"]) and db_config:
            intent["fazer_captura"] = True
            intent["fazer_estatistica"] = True
        # "Ver estrutura da base", "tabelas e volumes", "correlações" = sempre tentar captura quando houver db_config
        # (mesmo com dataset_ref antigo, para garantir estrutura atual e evitar "Não foi possível obter a estrutura")
        _pede_dados_ou_estrutura = _pede_estrutura_ou_correlacao or any(
            x in m_lower
            for x in [
                "resumo estatístico",
                "resumo estatistico",
                "resumo das variáveis",
                "resumo das variaveis",
                "variáveis numéricas",
                "variaveis numericas",
                "resumo das variaveis numericas",
                "resumo das variáveis numéricas",
            ]
        ) or ("resumo" in m_lower and ("variável" in m_lower or "variavel" in m_lower or "numericas" in m_lower or "numéricas" in m_lower))
        if _pede_dados_ou_estrutura and db_config:
            intent["fazer_captura"] = True
            intent["fazer_estatistica"] = True
            if not intent.get("pergunta_estatistica"):
                intent["pergunta_estatistica"] = mensagem
        # "traga os graficos", "mostre os graficos" = estatística (já tem dataset, só reexecutar para garantir gráficos)
        if any(x in m_lower for x in ["traga os graficos", "traga os gráficos", "mostre os graficos", "mostre os gráficos", "exiba os graficos"]):
            intent["fazer_estatistica"] = True
        # Correlações (plural/acentos) — heurística Ollama pode falhar com só "correlação" singular
        if any(x in m_lower for x in ("correlações", "correlacoes", "correlação", "correlacao")):
            intent["fazer_estatistica"] = True
            if not intent.get("pergunta_estatistica"):
                intent["pergunta_estatistica"] = mensagem
        # "grafico", "gráfico", "barras", "histograma", "dispersão", "x vs y" = estatística (ex.: "um grafico de barras horizontais tenure vs monthlycharges")
        if any(x in m_lower for x in ["grafico", "gráfico", "barras", "histograma", "dispersão", "dispersao", "scatter", "visualização", "visualizacao"]):
            intent["fazer_estatistica"] = True
            if not intent.get("pergunta_estatistica"):
                intent["pergunta_estatistica"] = mensagem
        # "X vs Y" (ex.: "tenure vs monthlycharges") = estatística
        if " vs " in m_lower and any(x in m_lower for x in ["grafico", "gráfico", "barras", "compar", "relação", "relacao"]):
            intent["fazer_estatistica"] = True
            if not intent.get("pergunta_estatistica"):
                intent["pergunta_estatistica"] = mensagem
        # "mostre X registros", "primeiras X linhas" = estatística (exige dataset)
        if any(x in m_lower for x in ["mostre", "mostrar", "exiba", "traga"]) and any(x in m_lower for x in ["registros", "linhas", "amostra"]):
            intent["fazer_estatistica"] = True
            if not intent.get("pergunta_estatistica"):
                intent["pergunta_estatistica"] = mensagem
        # "Quantos registros tem o dataset?" = estatística (resposta direta com contagem)
        if any(x in m_lower for x in ["quantos registros", "quantas linhas", "quantos registros tem", "quantas linhas tem", "número de registros", "numero de registros", "total de registros"]):
            intent["fazer_estatistica"] = True
            if not intent.get("pergunta_estatistica"):
                intent["pergunta_estatistica"] = mensagem
        # "Existe coluna de churn?" = estatística (resposta sobre schema)
        if any(x in m_lower for x in ["existe coluna", "existe uma coluna", "há coluna", "ha coluna", "tem coluna", "possui coluna", "coluna de churn"]):
            intent["fazer_estatistica"] = True
            if not intent.get("pergunta_estatistica"):
                intent["pergunta_estatistica"] = mensagem
        # "Mostre a distribuição/contagem da variável", "variância", "descreva o dataset", "gere visualizações", "data leakage", "outliers" = estatística
        if any(x in m_lower for x in [
            "distribuição da variável", "distribuicao da variavel", "mostre a distribuição", "mostre a distribuicao",
            "contagem por", "mostre a contagem",
            "variância", "variancia", "maior variância", "maior variancia",
            "descreva o dataset", "descreva o conjunto de dados",
            "gere visualizações", "gere visualizacoes", "visualizações para", "visualizacoes para", "5 variáveis mais importantes", "5 variaveis mais importantes",
            "balanceamento de classes", "balanceamento", "reamostragem",
            "vazamento", "data leakage", "vazamentos de dados",
            "outlier", "outliers", "valores extremos", "extremos",
        ]):
            intent["fazer_estatistica"] = True
            if not intent.get("pergunta_estatistica"):
                intent["pergunta_estatistica"] = mensagem
        # "valores únicos" de uma coluna específica (ex.: Contract) = estatística
        _valores_unicos = "valores únicos" in m_lower or "valores unicos" in m_lower
        if _valores_unicos:
            intent["fazer_estatistica"] = True
            if not intent.get("pergunta_estatistica"):
                intent["pergunta_estatistica"] = mensagem
        # "quais colunas são numéricas/categóricas" = estatística de schema
        _tipos_colunas = any(
            x in m_lower
            for x in [
                "colunas são numéricas",
                "colunas sao numericas",
                "numéricas e quais são categóricas",
                "numericas e quais sao categoricas",
                "colunas numericas e categoricas",
            ]
        )
        if _tipos_colunas:
            intent["fazer_estatistica"] = True
            if not intent.get("pergunta_estatistica"):
                intent["pergunta_estatistica"] = mensagem
        # "crie um modelo", "treine um modelo", "aplique ponderação/reamostragem" = treino
        if any(x in m_lower for x in [
            "crie um modelo", "criar modelo", "treine um modelo", "treinar modelo",
            "treine novamente", "treinar novamente", "treine com balanceamento", "treinar com balanceamento",
            "aplique a ponderação", "aplique ponderação", "aplicar ponderação",
            "aplique reamostragem", "aplicar reamostragem", "ponderação de classes",
            "crie um modelo de classificação", "criar modelo de classificação",
            "treine um modelo de ml", "treinar modelo de ml",
        ]):
            intent["fazer_treino"] = True
            if "churn" in m_lower and not intent.get("variavel_alvo"):
                intent["variavel_alvo"] = "Churn"
        # "gere previsões", "gerar previsões", "quantos previstos como churn" = previsão
        if any(x in m_lower for x in [
            "gere previsões", "gere previsoes", "gerar previsões", "gerar previsoes",
            "previsões de churn", "previsoes de churn",
            "quantos clientes previstos", "quantos foram previstos", "quantos previstos como churn"
        ]):
            intent["fazer_previsao"] = True

        # Fallback: perguntas conceituais sobre ML (recall, precisão, métricas) acionam fazer_estatistica
        if any(x in m_lower for x in ["priorizar", "recall", "precisão", "precisao", "qual métrica", "qual metrica", "modelo deve"]) and any(x in m_lower for x in ["churn", "modelo", "métrica", "metrica"]):
            intent["fazer_estatistica"] = True
        # Fallback: perguntas sobre modelos/previsão acionam fazer_estatistica (retorna modelos_sugeridos)
        _modelo_previsao = any(x in m_lower for x in [
            "quais modelos", "que modelos", "modelos seriam", "modelos para previsão", "modelos para previsao",
            "modelos bem aplicados", "modelo de previsão", "modelo de previsao", "qual tipo de modelo",
            "tipo de modelo", "bem aplicado", "modelos aplicados", "modelo aplicado",
            "sugerir modelo", "sugira um modelo", "sugestão de modelo", "recomendar modelo"
        ])
        # "Sugerir" / "recomendar" = apenas sugestão, NÃO treinar (evita inventar modelo treinado)
        _apenas_sugestao = any(x in m_lower for x in ["sugerir", "sugestão", "sugestao", "recomendar", "recomendação", "recomendacao"])
        if _apenas_sugestao:
            intent["fazer_treino"] = False  # usuário quer sugestão, não treino
        # "Relação entre X e Y" = análise estatística (tabela cruzada), NÃO treino
        _relacao_entre = any(x in m_lower for x in ["relação entre", "relacao entre", "análise da relação", "analise da relacao"])
        if _relacao_entre:
            intent["fazer_treino"] = False
            intent["fazer_estatistica"] = True
        # "Dataset está pronto?" = diagnóstico (estatística), NÃO treino
        _dataset_pronto = any(x in m_lower for x in ["dataset está pronto", "dataset esta pronto", "o que falta", "está pronto para treinar"])
        if _dataset_pronto:
            intent["fazer_treino"] = False
            intent["fazer_estatistica"] = True
        # "Poder preditivo para churn" = análise estatística (correlação com Churn), NÃO treino
        _poder_preditivo = any(
            x in m_lower
            for x in [
                "poder preditivo",
                "maior poder preditivo",
                "variáveis têm maior poder preditivo",
                "variaveis tem maior poder preditivo",
            ]
        )
        if _poder_preditivo:
            intent["fazer_treino"] = False
            intent["fazer_estatistica"] = True
            if not intent.get("pergunta_estatistica"):
                intent["pergunta_estatistica"] = mensagem
        if _modelo_previsao and not intent.get("fazer_treino") and not intent.get("fazer_estatistica"):
            intent["fazer_estatistica"] = True  # analise_estatistica retorna modelos_sugeridos

        # Recuperar dataset_ref do storage quando ausente (ex.: frontend não enviou na 2ª mensagem)
        if not dataset_ref and (intent.get("fazer_estatistica") or intent.get("fazer_treino") or intent.get("fazer_previsao")):
            logger.info("Chat: dataset_ref ausente no payload; tentando recuperar do storage (usuario=%s, id_req=%s)", usuario, id_req)
            recovered = get_latest_dataset_ref(usuario, id_req)
            if recovered:
                dataset_ref = recovered
                logger.info("Chat: dataset_ref recuperado do storage com sucesso (len=%d)", len(dataset_ref))
            else:
                logger.warning("Chat: dataset_ref NÃO encontrado no storage para usuario=%s, id_req=%s", usuario, id_req)
        # "Qual foi o melhor modelo?" = recuperar model_ref e responder com metadados (não treinar)
        _pergunta_melhor_modelo = any(x in m_lower for x in ["qual foi o melhor modelo", "melhor modelo entre", "melhor modelo dos testados", "qual o melhor modelo"])
        if _pergunta_melhor_modelo:
            intent["fazer_treino"] = False
            intent["fazer_estatistica"] = False
        # Recuperar model_ref quando ausente (para previsão ou pergunta sobre melhor modelo)
        if not model_ref and (intent.get("fazer_previsao") or _pergunta_melhor_modelo):
            logger.info("Chat: model_ref ausente no payload; tentando recuperar do storage (usuario=%s, id_req=%s)", usuario, id_req)
            recovered_model = get_latest_model_ref(usuario, id_req)
            if recovered_model:
                model_ref = recovered_model
                logger.info("Chat: model_ref recuperado do storage com sucesso")
            else:
                logger.warning("Chat: model_ref NÃO encontrado no storage para usuario=%s, id_req=%s", usuario, id_req)

        # 0) Captura (conectar ao banco e extrair amostra)
        # Também faz captura quando intent precisa de dados (estatística, treino ou previsão)
        # mas não tem dataset_ref e tem db_config
        precisa_captura = (
            (intent.get("fazer_captura") and db_config)
            or (
                (intent.get("fazer_estatistica") or intent.get("fazer_treino") or intent.get("fazer_previsao"))
                and db_config
                and not dataset_ref
            )
        )
        if precisa_captura and db_config:
            # Validação de db_config contra allowlist
            is_valid, error_msg = validar_db_config(db_config)
            if not is_valid:
                logger.warning("Chat: db_config inválido: %s", error_msg)
                captura_falha_politica = error_msg
                etapas.append("captura_dados_falhou")
            else:
                try:
                    out_captura = self._captura.run(
                        CapturaDadosInput(
                            id_requisicao=id_req,
                            usuario=usuario,
                            db_config=db_config,
                            incluir_amostra=True,
                            max_rows_amostra=500,
                        )
                    )
                    captura_dict = out_captura.captura_dados
                    if captura_dict.get("dataset_ref"):
                        dataset_ref = captura_dict["dataset_ref"]
                    etapas.append("captura_dados")
                except Exception as e:
                    logger.exception("Chat: captura falhou (exceção ao conectar ou ler a base)")
                    etapas.append("captura_dados_falhou")

        # 0.5) Tratamento (limpeza ETL)
        if intent.get("fazer_tratamento") and dataset_ref:
            try:
                out_trat = self._tratamento.run(
                    TratamentoLimpezaInput(id_requisicao=id_req, usuario=usuario, dataset_ref=dataset_ref)
                )
                trat_dict = out_trat.tratamento_limpeza
                if trat_dict.get("dataset_pronto"):
                    dataset_ref = trat_dict["dataset_pronto"]
                etapas.append("tratamento_limpeza")
            except Exception as e:
                logger.warning("Chat: tratamento falhou: %s", e)

        # 1) Análise estatística (correlação, média, etc.)
        # Para "sugestão de modelo", roda mesmo sem dataset_ref (resposta não depende dos dados)
        _sugestao_modelo_sem_dados = (
            intent.get("fazer_estatistica")
            and not dataset_ref
            and any(x in m_lower for x in ["sugerir", "sugestão", "sugestao", "recomendar"])
            and any(x in m_lower for x in ["modelo", "modelos", "ml", "machine learning"])
        )
        # Perguntas conceituais sobre ML (recall, precisão, métricas, estratégia) não precisam de dataset
        _pergunta_conceitual_ml = (
            not dataset_ref
            and any(x in m_lower for x in [
                "priorizar", "recall", "precisão", "precisao", "qual métrica", "qual metrica",
                "estratégia", "estrategia", "acurácia", "acuracia", "auc", "f1", "kappa", "mcc",
                "modelo deve", "deve priorizar", "recomendação de métrica", "recomendacao de metrica"
            ])
            and any(x in m_lower for x in ["modelo", "churn", "classificação", "classificacao", "ml", "métrica", "metrica"])
        )
        # Sem dataset_ref não entra em AnaliseEstatistica (condição abaixo) — evita UI presa e LLM sem contexto
        _pergunta_exige_amostra = any(
            p in m_lower
            for p in (
                "correla", "estrutura", "tabelas", "volumes", "primeiras", "linhas",
                "grafico", "gráfico", "dispersão", "dispersao", "histograma", "amostra",
                "média", "media", "mediana", "desvio", "quartil", "distribuição", "distribuicao",
                "outlier", "balanceamento", "visualizações", "visualizacoes", "contagem por",
            )
        )
        if (
            intent.get("fazer_estatistica")
            and not dataset_ref
            and not _sugestao_modelo_sem_dados
            and not _pergunta_conceitual_ml
            and _pergunta_exige_amostra
        ):
            etapas = list(etapas or [])
            if "captura_dados_falhou" not in etapas and "captura_dados" not in etapas:
                etapas.append("amostra_ausente")
            msg_amostra = (
                "**Não há amostra de dados nesta sessão** (ficheiro do dataset não encontrado no servidor).\n\n"
                "Em ambientes como a Railway o disco é **reiniciado** a cada deploy; é preciso voltar a gerar a amostra.\n\n"
                "1. Abra **Conexão**, confira URI/base/credenciais e clique em **Aplicar**.\n"
                "2. Envie **Ver estrutura da base** (ou a mesma pergunta de correlações) para disparar a captura.\n\n"
                "_O cliente deve enviar o `db_config` em cada mensagem até existir `dataset_ref` na resposta._"
            )
            return IDChatOutput(
                id_requisicao=id_req,
                resposta_texto=msg_amostra,
                etapas_executadas=etapas,
                previsoes=None,
                analise_estatistica=None,
                modelo_ml=None,
                dataset_ref=None,
                model_ref=model_ref,
                sugestao_proximo_passo="Reaplique a conexão (Aplicar) e repita o pedido.",
            )
        if (intent.get("fazer_estatistica") and (dataset_ref or _sugestao_modelo_sem_dados)) or _pergunta_conceitual_ml:
            try:
                out_stat = self._analise_estatistica.run(
                    AnaliseEstatisticaInput(
                        id_requisicao=id_req,
                        dataset_ref=dataset_ref,
                        pergunta=intent.get("pergunta_estatistica") or mensagem,
                    )
                )
                analise_estatistica = out_stat.analise_estatistica
                etapas.append("analise_estatistica")
            except Exception as e:
                logger.warning("Chat: análise estatística falhou: %s", e)

        # 1.5) Tratar pedido de aplicar balanceamento sem modelo treinado
        aplicar_balanceamento_intent = intent.get("aplicar_balanceamento", False)
        analisar_balanceamento_intent = intent.get("analisar_balanceamento", False)
        if aplicar_balanceamento_intent and not model_ref and not intent.get("fazer_treino"):
            # Usuário pediu aplicar balanceamento mas não há modelo treinado
            # Deve explicar que precisa treinar primeiro
            try:
                prompt_explicacao = load_prompt("ID_prompts/modelos_ml_explicacao_balanceamento").format(
                    situacao="Usuário pediu aplicar balanceamento mas não há modelo treinado. Precisa treinar um modelo primeiro mencionando balanceamento."
                )
                explicacao = self._llm.generate_text(prompt_explicacao, use_fast_model=True).strip()
                # Se houver análise estatística com balanceamento, incluir na resposta
                if analise_estatistica and analise_estatistica.get("balanceamento_classe"):
                    bal = analise_estatistica["balanceamento_classe"]
                    partes_bal = [f"**Balanceamento da variável alvo:**"]
                    for k, v in bal.items():
                        if k not in ("razao", "recomendacao"):
                            partes_bal.append(f"• {k}: {v}")
                    if bal.get("recomendacao"):
                        partes_bal.append(f"\n{bal['recomendacao']}")
                    explicacao = "\n".join(partes_bal) + "\n\n" + explicacao
                resposta_texto = explicacao
                sugestao = "Pode treinar um modelo com /criar-modelo-ml usando este dataset_ref e uma variável_alvo."
                return IDChatOutput(
                    id_requisicao=id_req,
                    resposta_texto=resposta_texto,
                    etapas_executadas=["analise_balanceamento"],
                    previsoes=None,
                    analise_estatistica=analise_estatistica,
                    modelo_ml=None,
                    dataset_ref=dataset_ref,
                    model_ref=None,
                    sugestao_proximo_passo=sugestao,
                )
            except Exception as e:
                logger.warning("Chat: falha ao gerar explicação de balanceamento: %s", e)
                # Fallback simples
                resposta_texto = (
                    "Balanceamento de classes é aplicado durante o treinamento do modelo, não após análise estatística. "
                    "Para aplicar balanceamento, treine um novo modelo mencionando essa necessidade, por exemplo: "
                    "'Treine novamente com balanceamento de classes' ou 'Aplique SMOTE e treine o modelo'."
                )
                if analise_estatistica and analise_estatistica.get("balanceamento_classe"):
                    bal = analise_estatistica["balanceamento_classe"]
                    partes_bal = [f"**Balanceamento da variável alvo:**"]
                    for k, v in bal.items():
                        if k not in ("razao", "recomendacao"):
                            partes_bal.append(f"• {k}: {v}")
                    if bal.get("recomendacao"):
                        partes_bal.append(f"\n{bal['recomendacao']}")
                    resposta_texto = "\n".join(partes_bal) + "\n\n" + resposta_texto
                return IDChatOutput(
                    id_requisicao=id_req,
                    resposta_texto=resposta_texto,
                    etapas_executadas=["analise_balanceamento"],
                    previsoes=None,
                    analise_estatistica=analise_estatistica,
                    modelo_ml=None,
                    dataset_ref=dataset_ref,
                    model_ref=None,
                    sugestao_proximo_passo="Pode treinar um modelo com /criar-modelo-ml usando este dataset_ref e uma variável_alvo.",
                )

        # 2) Treinar modelo (se pedido e temos dataset); o model_ref retornado será usado em 3) para prever com o próprio modelo criado
        if intent.get("fazer_treino"):
            logger.info("Chat: intent fazer_treino=True; dataset_ref=%s", "presente" if dataset_ref else "AUSENTE")
        if intent.get("fazer_treino") and dataset_ref:
            variavel_alvo = intent.get("variavel_alvo")
            if not variavel_alvo and analise_estatistica:
                variavel_alvo = (analise_estatistica.get("variaveis_alvo") or [None])[0]
            if not variavel_alvo:
                variavel_alvo = self._inferir_variavel_alvo(mensagem, dataset_ref)
            logger.info("Chat: treino - variavel_alvo=%s, tipo_problema=%s", variavel_alvo, intent.get("tipo_problema") or "classificacao")
            if not variavel_alvo:
                logger.warning("Chat: treino ignorado - variavel_alvo não identificada (mensagem=%s)", mensagem[:80])
            if variavel_alvo:
                try:
                    aplicar_balanceamento = intent.get("aplicar_balanceamento", False)
                    out_ml = self._modelos_ml.run(
                        ModelosMLInput(
                            id_requisicao=id_req,
                            usuario=usuario,
                            dataset_ref=dataset_ref,
                            variavel_alvo=variavel_alvo,
                            tipo_problema=intent.get("tipo_problema") or "classificacao",
                            aplicar_balanceamento=aplicar_balanceamento,
                        )
                    )
                    modelo_ml = out_ml.modelo_ml
                    if getattr(out_ml, "model_ref", None):
                        model_ref = out_ml.model_ref
                    etapas.append("criar_modelo_ml")
                    logger.info("Chat: treino concluído com sucesso; model_ref=%s", model_ref[:80] + "..." if model_ref and len(model_ref) > 80 else model_ref)
                except Exception as e:
                    logger.exception("Chat: treino falhou - %s", e)

        out_previsao = None
        # 3) Previsão (com model_ref e dados ou dataset)
        if intent.get("fazer_previsao") and model_ref and (dados_para_prever or dataset_ref):
            try:
                out_previsao = self._previsao.run(
                    PrevisaoInput(
                        id_requisicao=id_req,
                        model_ref=model_ref,
                        dataset_ref=dataset_ref if not dados_para_prever else None,
                        dados=dados_para_prever,
                        usuario=usuario,
                    )
                )
                previsoes = out_previsao.previsoes
                etapas.append("prever")
            except Exception as e:
                logger.warning("Chat: previsão falhou: %s", e)

        # Se só pediu previsão e já tem model_ref + dados
        if not previsoes and intent.get("fazer_previsao") and model_ref and dados_para_prever:
            try:
                out_previsao = self._previsao.run(
                    PrevisaoInput(
                        id_requisicao=id_req,
                        model_ref=model_ref,
                        dados=dados_para_prever,
                        usuario=usuario,
                    )
                )
                previsoes = out_previsao.previsoes
                etapas.append("prever")
            except Exception as e:
                logger.warning("Chat: previsão (dados) falhou: %s", e)

        # "Qual foi o melhor modelo?" – carregar metadados e montar resposta
        resposta_melhor_modelo: Optional[str] = None
        if _pergunta_melhor_modelo and not model_ref:
            resposta_melhor_modelo = (
                "Nenhum modelo treinado nesta sessão. Treine um modelo primeiro (ex.: 'Treine um modelo para prever churn') "
                "e depois pergunte novamente. O frontend deve manter e reenviar o model_ref da resposta anterior."
            )
        elif _pergunta_melhor_modelo and model_ref:
            try:
                meta = load_model_metadata(model_ref)
                if meta and meta.get("resultados"):
                    res = meta["resultados"]
                    nome = meta.get("modelo_escolhido") or "Modelo treinado"
                    partes_res = [f"**Melhor modelo:** {nome}."]
                    for k, v in res.items():
                        if isinstance(v, (int, float)):
                            val = v * 100 if v <= 1 else v
                            partes_res.append(f"{k}: {val:.1f}%")
                    resposta_melhor_modelo = " ".join(partes_res)
                    modelo_ml = {"modelo_escolhido": nome, "resultados": res, "constatacoes": ""}
            except Exception as e:
                logger.warning("Chat: falha ao carregar metadados do modelo para 'melhor modelo': %s", e)

        # Montar resposta em linguagem natural
        resposta_texto = self._montar_resposta(
            mensagem=mensagem,
            intent=intent,
            analise_estatistica=analise_estatistica,
            modelo_ml=modelo_ml,
            previsoes=previsoes,
            model_ref=model_ref,
            db_config=db_config,
            etapas=etapas,
            dataset_ref=dataset_ref,
            resposta_melhor_modelo=resposta_melhor_modelo,
            captura_falha_politica=captura_falha_politica,
        )
        if not sugestao:
            sugestao = self._sugestao_proximo(etapas, intent, model_ref, dataset_ref)

        distribuicao_previsoes: Optional[Dict[str, int]] = None
        metricas_modelo_previsao: Optional[Dict[str, Any]] = None
        exemplos_previsao: Optional[List[Dict[str, Any]]] = None
        if previsoes and len(previsoes) > 0:
            if out_previsao and getattr(out_previsao, "metricas_negocio", None):
                qpc = out_previsao.metricas_negocio.get("quantidade_por_classe")
                if isinstance(qpc, dict):
                    distribuicao_previsoes = {str(k): int(v) for k, v in qpc.items()}
            if not distribuicao_previsoes:
                from collections import Counter
                distribuicao_previsoes = {str(k): int(v) for k, v in Counter(str(p) for p in previsoes).items()}
            exemplos_previsao = [{"indice": i, "previsao": str(p)} for i, p in enumerate(previsoes[:20])]
            if model_ref and not metricas_modelo_previsao:
                try:
                    meta = load_model_metadata(model_ref)
                    if meta and meta.get("resultados"):
                        metricas_modelo_previsao = meta["resultados"]
                except Exception:
                    pass
            if modelo_ml and modelo_ml.get("resultados") and not metricas_modelo_previsao:
                metricas_modelo_previsao = modelo_ml["resultados"]

        return IDChatOutput(
            id_requisicao=id_req,
            resposta_texto=resposta_texto,
            etapas_executadas=etapas,
            previsoes=previsoes,
            distribuicao_previsoes=distribuicao_previsoes,
            metricas_modelo_previsao=metricas_modelo_previsao,
            exemplos_previsao=exemplos_previsao,
            analise_estatistica=analise_estatistica,
            modelo_ml=modelo_ml,
            dataset_ref=dataset_ref,
            model_ref=model_ref,
            sugestao_proximo_passo=sugestao,
        )

    def _interpretar_mensagem(
        self,
        mensagem: str,
        dataset_ref: Optional[str],
        model_ref: Optional[str],
        db_config: Optional[Dict[str, Any]] = None,
        usuario: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Usa LLM para extrair intenções; resultado em cache por hash(mensagem+contexto+usuario) com TTL."""
        m = mensagem.lower()
        cache_key = hashlib.sha256(
            (mensagem + "|" + str(dataset_ref) + "|" + str(model_ref) + "|" + str(db_config is not None) + "|" + str(usuario or "")).encode()
        ).hexdigest()
        cache_key_user = f"{usuario or 'default'}:{cache_key}"
        now = time.time()
        if cache_key_user in _INTENT_CACHE:
            ts, data = _INTENT_CACHE[cache_key_user]
            if now - ts <= _INTENT_CACHE_TTL_SEC:
                return data
            del _INTENT_CACHE[cache_key_user]

        # Em ambientes com USE_OLLAMA ativo, evita chamada LLM lenta
        # e usa diretamente heurísticas locais (mais rápidas e estáveis).
        if os.getenv("USE_OLLAMA", "").strip().lower() in ("1", "true", "yes"):
            out = {
                "fazer_captura": any(x in m for x in ["conectar", "banco", "capturar", "tabela", "base de dados"]),
                "fazer_tratamento": any(x in m for x in ["limpar", "tratar", "normalizar", "duplicatas", "outliers"]),
                "fazer_estatistica": any(
                    x in m
                    for x in [
                        "correlação",
                        "correlações",
                        "correlacao",
                        "correlacoes",
                        "calcular",
                        "calcule",
                        "principais",
                        "média",
                        "media",
                        "estatística",
                        "estatistica",
                        "estatístico",
                        "estatistico",
                        "resumo estatístico",
                        "resumo estatistico",
                        "primeiras",
                        "linhas",
                        "registros",
                        "amostra",
                        "analise",
                        "analisar",
                        "analise a base",
                        "grafico",
                        "gráfico",
                        "barras",
                        "histograma",
                        "dispersão",
                        "dispersao",
                        "colunas",
                        "coluna",
                        "liste",
                        "listar",
                        "tipos de dados",
                        "tipos",
                        "tabelas",
                        "volumes",
                        "estrutura",
                        "distribuição",
                        "distribuicao",
                        "compare",
                        "comparar",
                        "recomende",
                        "recomendar",
                        "feature engineering",
                        "técnicas",
                        "tecnicas",
                    ]
                ),
                # Treino: verbos explícitos ou aplicação de ponderação/reamostragem
                "fazer_treino": any(x in m for x in [
                    "treinar", "treino", "treine",
                    "aplique a ponderação", "aplique ponderação", "aplicar ponderação",
                    "aplique a reamostragem", "aplique reamostragem", "aplicar reamostragem",
                    "ponderação de classes", "treine novamente", "treinar novamente",
                ]),
                "fazer_previsao": any(x in m for x in ["previsão", "previsao", "quem vai", "quais clientes"]),
                "variavel_alvo": None,
                "pergunta_estatistica": mensagem,
                "tipo_problema": "regressao" if "regressão" in m or "valor" in m else "classificacao",
                "analisar_balanceamento": any(x in m for x in ["analise o balanceamento", "analisar balanceamento", "verifique o balanceamento", "mostre o balanceamento", "balanceamento da variável"]),
                "aplicar_balanceamento": any(x in m for x in ["aplique ponderação", "aplique reamostragem", "aplique balanceamento", "treine com balanceamento", "use smote", "aplicar smote"]),
            }
            if len(_INTENT_CACHE) >= _INTENT_CACHE_MAX:
                _INTENT_CACHE.pop(next(iter(_INTENT_CACHE)))
            _INTENT_CACHE[cache_key_user] = (time.time(), out)
            return out

        prompt = load_prompt("ID_prompts/id_chat_interpretacao").format(
            mensagem=mensagem,
            dataset_ref="sim" if dataset_ref else "não",
            model_ref="sim" if model_ref else "não",
            db_config="sim" if db_config else "não"
        )
        try:
            # Timeout maior para interpretação (Ollama pode demorar em máquinas lentas)
            raw = self._llm.generate_text(
                prompt, use_fast_model=True, timeout_override=360
            ).strip()
            raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            out = json.loads(raw)
            if len(_INTENT_CACHE) >= _INTENT_CACHE_MAX:
                _INTENT_CACHE.pop(next(iter(_INTENT_CACHE)))
            _INTENT_CACHE[cache_key_user] = (time.time(), out)
            return out
        except Exception as e:
            logger.warning("Chat: interpretação LLM falhou: %s", e)
            out = {
                "fazer_captura": any(x in m for x in ["conectar", "banco", "capturar", "tabela", "base de dados"]),
                "fazer_tratamento": any(x in m for x in ["limpar", "tratar", "normalizar", "duplicatas", "outliers"]),
                "fazer_estatistica": any(x in m for x in ["correlação", "correlações", "correlacao", "correlacoes", "calcular", "calcule", "principais", "média", "media", "estatística", "estatistica", "primeiras", "linhas", "registros", "amostra", "analise", "analisar", "analise a base", "grafico", "gráfico", "barras", "histograma", "dispersão", "dispersao", "colunas", "coluna", "liste", "listar", "tipos", "tabelas", "volumes", "estrutura", "distribuição", "distribuicao", "compare", "recomende", "feature engineering", "técnicas", "tecnicas"]),
                "fazer_treino": any(x in m for x in ["treinar", "treino", "treine", "aplique a ponderação", "aplique ponderação", "aplique reamostragem", "ponderação de classes", "treine novamente"]),
                "fazer_previsao": any(x in m for x in ["previsão", "previsao", "quem vai", "quais clientes"]),
                "variavel_alvo": None,
                "pergunta_estatistica": mensagem,
                "tipo_problema": "regressao" if "regressão" in m or "valor" in m else "classificacao",
            }
            if len(_INTENT_CACHE) >= _INTENT_CACHE_MAX:
                _INTENT_CACHE.pop(next(iter(_INTENT_CACHE)))
            _INTENT_CACHE[cache_key_user] = (time.time(), out)
            return out

    def _inferir_variavel_alvo(self, mensagem: str, dataset_ref: str) -> Optional[str]:
        """Quando a mensagem não traz coluna explícita, usa LLM + colunas do dataset para inferir a variável alvo."""
        try:
            df = load_dataframe(dataset_ref)
            colunas = list(df.columns)[:50]
            if not colunas:
                return None
            prompt = load_prompt("ID_prompts/id_chat_inferir_variavel_alvo").format(
                mensagem=mensagem,
                colunas=', '.join(colunas)
            )
            raw = self._llm.generate_text(
                prompt, use_fast_model=True, timeout_override=360
            ).strip().strip('"\'')
            if raw in colunas:
                return raw
            # Match case-insensitive ou parcial
            raw_lower = raw.lower()
            for c in colunas:
                if c.lower() == raw_lower or raw_lower in c.lower():
                    return c
            return None
        except Exception as e:
            logger.warning("Inferência de variável alvo falhou: %s", e)
            return None

    def _montar_resposta(
        self,
        mensagem: str,
        intent: Dict[str, Any],
        analise_estatistica: Optional[Dict[str, Any]],
        modelo_ml: Optional[Dict[str, Any]],
        previsoes: Optional[List[Any]],
        model_ref: Optional[str] = None,
        db_config: Optional[Dict[str, Any]] = None,
        etapas: Optional[List[str]] = None,
        dataset_ref: Optional[str] = None,
        resposta_melhor_modelo: Optional[str] = None,
        captura_falha_politica: Optional[str] = None,
    ) -> str:
        partes: List[str] = []
        if resposta_melhor_modelo:
            partes.append(resposta_melhor_modelo)
        if analise_estatistica:
            resp = analise_estatistica.get("resposta_pergunta") or analise_estatistica.get("insights", [])
            if isinstance(resp, list):
                resp = " ".join(resp[:2]) if resp else "Análise estatística concluída."
            texto = str(resp).strip()
            # Remover tokens corrompidos do LLM (<unk>, <s>, | repetidos, etc.)
            texto = re.sub(r"<unk>|</s>|<s>|<s\s*\||\|\s*s>", "", texto, flags=re.IGNORECASE)
            texto = re.sub(r"\|\s*\|+", " ", texto)
            texto = re.sub(r"[$#]+\s*\|+!", "", texto).strip()
            # Remover vazamentos de prompt/instruções na resposta (Ollama às vezes retorna o prompt)
            _prefixos_instrucao = (
                "o usuário perguntou", "o usuário pergunta", "pergunta:", "métricas relevantes", "resposta:",
                "a resposta deve", "a medida que", "use apenas", "não use ", "não invente", "regra crítica",
                "responda sempre", "responda apenas", "dê uma resposta", "seja objetivo", "seja direto"
            )
            linhas = texto.split("\n")
            linhas_limpas = [
                L for L in linhas
                if not any(L.strip().lower().startswith(p) for p in _prefixos_instrucao)
            ]
            texto = "\n".join(linhas_limpas).strip() or texto
            partes.append(texto)
            # Perfil de churn quando disponível (resposta mais pontual)
            perfil_churn = analise_estatistica.get("perfil_churn")
            if perfil_churn:
                partes.append(f"\n\n{perfil_churn}")
            # Indicar gráficos quando há dados reais; listar títulos para facilitar interpretação no frontend
            graficos_dados = analise_estatistica.get("graficos_dados") or []
            graficos_metadados = analise_estatistica.get("graficos_metadados") or []
            tem_dados = any(g.get("values") or g.get("x") for g in graficos_dados if isinstance(g, dict))
            if tem_dados and graficos_metadados:
                titulos = [g.get("titulo", "") for g in graficos_metadados[:5] if g.get("titulo")]
                if titulos:
                    partes.append("\n\n📊 **Gráficos:** " + " | ".join(titulos[:4]) + ("..." if len(titulos) > 4 else ""))
                else:
                    partes.append("\n\n📊 Distribuições, contagens e dispersões.")
            elif tem_dados:
                partes.append("\n\n📊 Distribuições, contagens e dispersões.")
        # Mostrar resultado do treino (sucesso ou falha com constatacoes)
        if modelo_ml and intent.get("fazer_treino"):
            if model_ref and modelo_ml.get("modelo_escolhido") != "N/A":
                res = modelo_ml.get("resultados") or {}
                auc_val = res.get("auc")
                auc_str = f" (AUC {auc_val * 100:.1f}%)" if auc_val is not None else ""
                partes.append(
                    f"\n\n**Melhor modelo:** {modelo_ml.get('modelo_escolhido')}{auc_str}. "
                    f"{modelo_ml.get('constatacoes', '')}"
                )
                # Perfil de churn a partir da importância de variáveis (resposta mais pontual)
                imp = modelo_ml.get("importancia_variaveis") or []
                if imp and any(x in (mensagem or "").lower() for x in ["churn", "perfil", "treine", "modelo"]):
                    top_vars = [f"{x['variavel']}" for x in imp[:4] if x.get("importancia", 0) > 0.05]
                    if top_vars:
                        partes.append(f"\n\n**Perfil de churn:** Variáveis mais importantes: {', '.join(top_vars)}.")
            elif modelo_ml.get("constatacoes"):
                partes.append(f"\n\n**Treino:** {modelo_ml.get('constatacoes')}")
        if previsoes is not None and len(previsoes) > 0:
            from collections import Counter
            contagem = Counter(str(p).lower() for p in previsoes)
            n_churn = sum(contagem.get(k, 0) for k in ("yes", "sim", "1", "churn"))
            n_total = len(previsoes)
            m_lower = mensagem.lower()
            # "Quantos clientes previstos como churn?" -> resposta direta e pontual
            if any(x in m_lower for x in ["quantos", "quantas"]) and any(x in m_lower for x in ["previstos", "previsões", "previsoes", "churn"]):
                partes.append(f"\n\n**{n_churn}** clientes previstos como churn (de {n_total} no total).")
            elif len(previsoes) <= 10:
                partes.append("\n\n**Previsões:** " + ", ".join(str(p) for p in previsoes) + ".")
            else:
                partes.append(f"\n\n**Previsões:** {len(previsoes)} geradas. Churn: {n_churn} | Sem churn: {n_total - n_churn}. Amostra: " + ", ".join(str(p) for p in previsoes[:5]) + "...")
        if not partes:
            logger.warning("Chat: nenhuma etapa executada; etapas=%s, intent_treino=%s, dataset_ref=%s, db_config=%s", etapas or [], intent.get("fazer_treino"), "presente" if dataset_ref else "ausente", "presente" if db_config else "ausente")
            m_lower = mensagem.lower()
            # Perguntas conceituais sobre estratégia de validação – resposta direta, sem depender de etapas
            if any(
                x in m_lower
                for x in [
                    "estratégia de validação",
                    "estrategia de validacao",
                    "validação cruzada",
                    "validacao cruzada",
                    "cross validation",
                    "k-fold",
                    "kfold",
                ]
            ):
                return load_prompt("ID_prompts/id_chat_estrategia_validacao")
            # Usar prompt de orientação quando contexto está ausente
            if intent.get("fazer_treino") or intent.get("fazer_previsao"):
                try:
                    prompt_orientacao = load_prompt("ID_prompts/id_chat_orientacao_contexto").format(
                        tem_dataset_ref="sim" if dataset_ref else "não",
                        tem_model_ref="sim" if model_ref else "não",
                        tem_db_config="sim" if db_config else "não",
                        mensagem=mensagem
                    )
                    resposta_orientacao = self._llm.generate_text(prompt_orientacao, use_fast_model=True).strip()
                    return resposta_orientacao
                except Exception as e:
                    logger.warning("Chat: falha ao gerar orientação com LLM: %s", e)
                    # Fallback
                    if intent.get("fazer_treino"):
                        return (
                            "Não foi possível treinar o modelo. **Para treinar:**\n"
                            "1. Conecte-se ao banco (botão Conexão) e envie uma mensagem como \"Analise os dados do banco\" ou \"Faça uma análise estatística dos dados\".\n"
                            "2. Após a análise, peça novamente para treinar o modelo.\n"
                            "O frontend deve manter e reenviar o `dataset_ref` (ou `db_config`) da conversa anterior em cada nova mensagem."
                        )
                    elif intent.get("fazer_previsao"):
                        return (
                            "Não foi possível fazer previsões. **Para fazer previsões:**\n"
                            "1. Primeiro treine um modelo (ex.: 'Treine um modelo para prever churn')\n"
                            "2. Depois use o comando '/prever' com model_ref e dados_para_prever\n"
                            "Ou pergunte 'Quantos clientes foram previstos como churn?' após treinar um modelo."
                        )
            _pediu_estrutura = any(
                x in m_lower for x in ["estrutura", "tabelas", "volumes", "correlações", "correlacoes", "ver estrutura"]
            )
            if "captura_dados_falhou" in (etapas or []):
                base = (
                    "**Não foi possível conectar à base de dados ou concluir a captura.**\n\n"
                    "Verifique no botão **Conexão**: host/URI, nome do banco, usuário e senha. "
                    "Confirme que o banco está acessível a partir do servidor (rede/firewall) e que o utilizador tem permissão de leitura."
                )
                if captura_falha_politica:
                    base += (
                        f"\n\n**Política de segurança (servidor):** {captura_falha_politica}\n\n"
                        "_Se a mensagem falar em allowlist ou variáveis de ambiente, o administrador deve ajustar "
                        "`ALLOWED_DB_HOSTS` / `ALLOWED_DB_DATABASES` na Railway (Variables), não só o formulário de conexão._"
                    )
                else:
                    base += (
                        "\n\n_Se a conexão estiver correta, consulte os logs do serviço (ex.: Railway → Deploy Logs) "
                        "para o detalhe do erro._"
                    )
                base += (
                    "\n\nDepois tente novamente **Ver estrutura da base** ou **Calcular correlações principais**."
                )
                return base
            if db_config and _pediu_estrutura and "captura_dados" not in (etapas or []):
                return (
                    "**Não foi possível obter a estrutura da base.**\n\n"
                    "Verifique no botão **Conexão** se host, porta, base, usuário e senha estão corretos e se o banco está acessível. "
                    "Confirme que o frontend envia o **db_config** (configuração de conexão) no payload desta requisição. "
                    "Em seguida, tente novamente."
                )
            if db_config:
                # Tentar usar prompt de orientação
                try:
                    prompt_orientacao = load_prompt("ID_prompts/id_chat_orientacao_contexto").format(
                        tem_dataset_ref="não",
                        tem_model_ref="não",
                        tem_db_config="sim",
                        mensagem=mensagem
                    )
                    resposta_orientacao = self._llm.generate_text(prompt_orientacao, use_fast_model=True).strip()
                    return resposta_orientacao
                except Exception as e:
                    logger.warning("Chat: falha ao gerar orientação com LLM: %s", e)
                    # Fallback
                    msg_gen = (
                        "Não foi possível executar nenhuma etapa. "
                        "Possíveis causas: conexão com o banco, ausência de dataset_ref (reenvie o contexto da análise anterior) ou timeout. Tente novamente."
                    )
                    if _pediu_estrutura:
                        msg_gen = (
                            "**Não foi possível obter dados da base.**\n\n"
                            "Verifique no botão **Conexão** se host, porta, base, usuário e senha estão corretos e se o **db_config** é enviado no payload. "
                            "Depois tente novamente \"Ver estrutura da base\" ou \"Quais são as tabelas e volumes?\"."
                        )
                    return msg_gen
            if any(x in m_lower for x in ["estrutura", "tabelas", "volumes", "correlações", "correlacoes", "analise", "análise"]):
                return (
                    "**Conecte-se primeiro à base de dados.**\n\n"
                    "Para ver estrutura, tabelas, volumes ou calcular correlações:\n"
                    "1. Clique no botão **Conexão** (canto superior)\n"
                    "2. Preencha Host, Base, Usuário e Senha do seu banco\n"
                    "3. Clique em **Aplicar**\n"
                    "4. Depois envie novamente sua pergunta ou clique em \"Ver estrutura da base\" ou \"Calcular correlações principais\""
                )
            return (
                "**Conecte-se à base de dados** para analisar dados.\n\n"
                "Use o botão **Conexão** no canto superior, configure seu banco e clique em **Aplicar**. "
                "Em seguida, faça sua pergunta ou use os botões de sugestão."
            )
        return "".join(partes).strip()

    def _sugestao_proximo(
        self,
        etapas: List[str],
        intent: Dict[str, Any],
        model_ref: Optional[str],
        dataset_ref: Optional[str],
    ) -> str:
        if "captura_dados_falhou" in (etapas or []):
            return "Verifique host, usuário e senha no botão Conexão e tente novamente."
        # Pediu estrutura/dados mas nenhuma etapa rodou (ex.: captura não tentada ou falhou sem marcar etapas)
        if not dataset_ref and (intent.get("fazer_captura") or intent.get("fazer_estatistica")) and "captura_dados" not in (etapas or []):
            return "Verifique a conexão no botão Conexão e tente novamente."
        if "prever" in etapas and model_ref:
            return "Use o mesmo model_ref com novos dados em 'dados_para_prever' para mais previsões."
        if "criar_modelo_ml" in etapas and model_ref:
            return "Chame /prever com model_ref e dados_para_prever para previsões em tempo real."
        if "analise_estatistica" in etapas and dataset_ref:
            return "Pode treinar um modelo com /criar-modelo-ml usando este dataset_ref e uma variável_alvo."
        if dataset_ref and (intent.get("fazer_estatistica") or intent.get("fazer_treino")):
            return "Continue sua análise ou treine um modelo com /criar-modelo-ml e variavel_alvo."
        if model_ref:
            return "Use model_ref com dados_para_prever para previsões em tempo real."
        return "Envie um dataset_ref para análise estatística ou treino de modelo."
