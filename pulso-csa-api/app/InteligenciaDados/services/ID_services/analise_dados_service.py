# Serviço de Análise Inicial dos Dados – objetivos, variáveis alvo, tratamentos sugeridos
import json
import logging
from typing import Any, Dict, List, Optional

from app.core.openai.openai_client import get_openai_client
from app.InteligenciaDados.models.ID_models.analise_dados_models import AnaliseDadosInicialInput, AnaliseDadosInicialOutput
from app.prompts.loader import load_prompt
from app.InteligenciaDados.storage.id_artifacts.id_artifacts_io import load_dataframe

logger = logging.getLogger(__name__)


def _resumo_amostra(path: str) -> str:
    """Carrega amostra e retorna resumo (colunas, tipos, primeiras linhas) para o prompt."""
    try:
        df = load_dataframe(path)
        colunas = list(df.columns)
        dtypes = {c: str(df.dtypes[c]) for c in colunas[:30]}
        head = df.head(3).to_string(max_cols=10)
        return f"Colunas: {colunas}\nTipos: {dtypes}\nAmostra (3 linhas):\n{head}"
    except Exception as e:
        logger.warning("Falha ao carregar amostra para análise inicial: %s", e)
        return ""


class AnaliseDadosService:
    """
    Interpreta o retorno de /captura-dados, propõe objetivo de análise,
    identifica variáveis relevantes e tratamentos necessários. Usa LLM.
    Se houver dataset_ref (amostra), inclui resumo no prompt para refinar variáveis alvo.
    """

    def __init__(self) -> None:
        self._llm = get_openai_client()

    def run(self, payload: AnaliseDadosInicialInput) -> AnaliseDadosInicialOutput:
        captura = payload.retorno_captura or {}
        objetivo = payload.objetivo_analise or "análise exploratória"
        tabelas = captura.get("tabelas", [])[:15]
        tipo_base = captura.get("tipo_base", "SQL")
        dataset_ref: Optional[str] = payload.dataset_ref or captura.get("dataset_ref")

        contexto_amostra = ""
        if dataset_ref:
            contexto_amostra = "\n\nResumo da amostra de dados (use para refinar variaveis_alvo e tratamentos):\n" + _resumo_amostra(dataset_ref)

        prompt = load_prompt("ID_prompts/analise_dados_inicial").format(
            tipo_base=tipo_base,
            tabelas=', '.join(tabelas),
            objetivo=objetivo,
            contexto_amostra=contexto_amostra
        )
        try:
            raw = self._llm.generate_text(prompt, use_fast_model=True).strip()
            raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            data = json.loads(raw)
        except Exception as e:
            logger.warning("LLM análise inicial falhou: %s", e)
            data = {
                "objetivo_analise": objetivo,
                "analises_recomendadas": ["distribuição de variáveis", "correlações"],
                "tratamentos_necessarios": ["verificar duplicatas", "tratar valores ausentes"],
                "variaveis_alvo": tabelas[0:3] if tabelas else [],
            }

        return AnaliseDadosInicialOutput(
            id_requisicao=payload.id_requisicao,
            analise_inicial=data,
            dataset_ref=dataset_ref,
        )
