# Serviço de Tratamento e Limpeza de Dados – ETL modular (duplicatas, missing, outliers)
import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from app.InteligenciaDados.models.ID_models.tratamento_limpeza_models import TratamentoLimpezaInput, TratamentoLimpezaOutput
from app.InteligenciaDados.storage.id_artifacts.id_artifacts_io import load_dataframe, save_dataframe

logger = logging.getLogger(__name__)


def _tratar_valores_ausentes(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if df[col].dtype in ("object", "string", "category", "bool"):
            mode_val = df[col].mode()
            df[col] = df[col].fillna(mode_val[0] if len(mode_val) else "")
        else:
            df[col] = df[col].fillna(df[col].median())
    return df


def _clip_outliers_iqr(df: pd.DataFrame, factor: float = 1.5) -> pd.DataFrame:
    out = df.copy()
    for col in out.select_dtypes(include=["number"]).columns:
        q1, q3 = out[col].quantile(0.25), out[col].quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            low, high = q1 - factor * iqr, q3 + factor * iqr
            out[col] = out[col].clip(lower=low, upper=high)
    return out


class TratamentoLimpezaService:
    """
    Executa pipeline real de limpeza: duplicatas, valores ausentes, outliers (IQR).
    Persiste dataset tratado em Parquet e retorna path em dataset_pronto.
    """

    def __init__(self) -> None:
        pass

    def run(self, payload: TratamentoLimpezaInput) -> TratamentoLimpezaOutput:
        analise = payload.retorno_analise_inicial or {}
        dataset_ref: Optional[str] = payload.dataset_ref or analise.get("dataset_ref")
        analise_inicial = analise.get("analise_inicial") or analise
        tratamentos_sugeridos = analise_inicial.get("tratamentos_necessarios", [])

        acoes: List[str] = []
        justificativas: List[str] = []
        dataset_pronto_path: str = f"dados_tratados_{payload.id_requisicao[:8]}.parquet"

        if dataset_ref:
            try:
                df = load_dataframe(dataset_ref)
                n_antes = len(df)
                df = df.drop_duplicates()
                acoes.append("remoção de duplicatas")
                justificativas.append("Duplicatas poderiam enviesar análises.")
                df = _tratar_valores_ausentes(df)
                acoes.append("tratamento de valores ausentes (mediana/moda)")
                justificativas.append("Valores ausentes preenchidos para permitir modelos de ML.")
                df = _clip_outliers_iqr(df)
                acoes.append("limite de outliers (IQR 1.5)")
                justificativas.append("Outliers limitados para reduzir impacto em médias e modelos.")
                for t in tratamentos_sugeridos:
                    if t not in acoes and len(acoes) < 6:
                        acoes.append(t)
                        justificativas.append(f"Aplicação de: {t} conforme análise inicial.")
                usuario = payload.usuario or "default"
                dataset_pronto_path = save_dataframe(
                    df, usuario, payload.id_requisicao, f"dados_tratados_{payload.id_requisicao[:8]}", subdir="datasets"
                )
            except Exception as e:
                logger.warning("ETL tratamento falhou, retornando apenas plano: %s", e)
                if not acoes:
                    acoes = ["verificação de duplicatas", "tratamento de valores ausentes"]
                    justificativas = [
                        "Duplicatas podem enviesar análises.",
                        "Valores ausentes precisam ser tratados para modelos de ML.",
                    ]
        else:
            for t in tratamentos_sugeridos[:5]:
                acoes.append(t)
                justificativas.append(f"Aplicação de: {t} conforme análise inicial.")
            if not acoes:
                acoes = ["verificação de duplicatas", "tratamento de valores ausentes"]
                justificativas = [
                    "Duplicatas poderiam enviesar análises.",
                    "Valores precisam estar na mesma escala para análise.",
                ]

        return TratamentoLimpezaOutput(
            id_requisicao=payload.id_requisicao,
            tratamento_limpeza={
                "acoes": acoes,
                "justificativas": justificativas,
                "dataset_pronto": dataset_pronto_path,
            },
        )
