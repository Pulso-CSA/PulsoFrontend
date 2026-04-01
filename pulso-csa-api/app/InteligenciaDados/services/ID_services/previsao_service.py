# Serviço de Previsão em Tempo Real – aplica modelo salvo a dados ou dataset
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from app.InteligenciaDados.models.ID_models.previsao_models import PrevisaoInput, PrevisaoOutput
from app.InteligenciaDados.storage.id_artifacts.id_artifacts_io import load_dataframe, load_model_metadata, save_dataframe

logger = logging.getLogger(__name__)


def _validar_schema(colunas_dados: List[str], metadata: Optional[Dict[str, Any]]) -> Optional[str]:
    """Retorna mensagem de erro se colunas não batem com features do modelo."""
    if not metadata or "features" not in metadata:
        return None
    feats = set(metadata["features"])
    cols = set(colunas_dados)
    faltando = feats - cols
    if faltando:
        return f"Colunas esperadas pelo modelo e ausentes nos dados: {', '.join(sorted(faltando))}."
    return None


def _carregar_modelo(path: str) -> Tuple[Any, str]:
    """Carrega modelo PyCaret; retorna (pipeline, tipo) com tipo em ('classificacao','regressao')."""
    path_clean = path.replace(".pkl", "")
    try:
        from pycaret.classification import load_model
        model = load_model(path_clean)
        return model, "classificacao"
    except Exception:
        try:
            from pycaret.regression import load_model
            model = load_model(path_clean)
            return model, "regressao"
        except Exception as e:
            logger.warning("Falha ao carregar modelo: %s", e)
            raise ValueError(f"Modelo não encontrado ou formato inválido: {path}") from e


def _extrair_coluna_previsao(pred_df: pd.DataFrame, df_original: pd.DataFrame) -> str:
    """Identifica coluna de previsão no DataFrame retornado por predict_model."""
    for c in ("prediction_label", "Label", "prediction"):
        if c in pred_df.columns:
            return c
    extra = [c for c in pred_df.columns if c not in df_original.columns]
    return extra[-1] if extra else pred_df.columns[-1]


class PrevisaoService:
    """
    Carrega modelo salvo (model_ref) e aplica previsões em:
    - dataset_ref: arquivo Parquet (lote); salva dataset com coluna de previsão.
    - dados: lista de dicts (tempo real, ex. chat); retorna lista de previsões.
    """

    def run(self, payload: PrevisaoInput) -> PrevisaoOutput:
        model_ref = payload.model_ref
        dataset_ref = payload.dataset_ref
        dados = payload.dados
        usuario = payload.usuario or "default"

        if not dataset_ref and not dados:
            return PrevisaoOutput(
                id_requisicao=payload.id_requisicao,
                previsoes=[],
                total_previsto=0,
            )

        metadata = load_model_metadata(model_ref)
        model, tipo = _carregar_modelo(model_ref)
        modelo_nome = getattr(model, "__class__", type(model)).__name__ if model else None

        if tipo == "classificacao":
            from pycaret.classification import predict_model
        else:
            from pycaret.regression import predict_model

        previsoes: List[Any] = []
        dataset_com_previsao_ref: Optional[str] = None
        metricas_negocio: Optional[Dict[str, Any]] = None
        intervalos_confianca: Optional[List[Dict[str, Any]]] = None
        erro_validacao: Optional[str] = None

        if dataset_ref:
            try:
                df = load_dataframe(dataset_ref)
                err = _validar_schema(list(df.columns), metadata)
                if err:
                    return PrevisaoOutput(
                        id_requisicao=payload.id_requisicao,
                        previsoes=[],
                        total_previsto=0,
                        modelo_usado=modelo_nome,
                        erro_validacao=err,
                    )
                pred_df = predict_model(model, df)
                col_pred = _extrair_coluna_previsao(pred_df, df)
                previsoes = pred_df[col_pred].astype(str).tolist()
                metricas_negocio = self._metricas_negocio_pred(pred_df, col_pred, tipo)
                intervalos_confianca = self._extrair_intervalos_regressao(pred_df, df)
                pred_df.rename(columns={col_pred: "previsao"}, inplace=True)
                out_path = save_dataframe(
                    pred_df, usuario, payload.id_requisicao, "dataset_com_previsao", subdir="datasets"
                )
                dataset_com_previsao_ref = out_path
            except Exception as e:
                logger.warning("Falha ao prever em dataset: %s", e)
                return PrevisaoOutput(
                    id_requisicao=payload.id_requisicao,
                    previsoes=[],
                    total_previsto=0,
                    modelo_usado=modelo_nome,
                )
        else:
            try:
                df = pd.DataFrame(dados)
                err = _validar_schema(list(df.columns), metadata)
                if err:
                    return PrevisaoOutput(
                        id_requisicao=payload.id_requisicao,
                        previsoes=[],
                        total_previsto=0,
                        modelo_usado=modelo_nome,
                        erro_validacao=err,
                    )
                pred_df = predict_model(model, df)
                col_pred = _extrair_coluna_previsao(pred_df, df)
                previsoes = pred_df[col_pred].tolist()
                metricas_negocio = self._metricas_negocio_pred(pred_df, col_pred, tipo)
                intervalos_confianca = self._extrair_intervalos_regressao(pred_df, df)
            except Exception as e:
                logger.warning("Falha ao prever em dados: %s", e)
                return PrevisaoOutput(
                    id_requisicao=payload.id_requisicao,
                    previsoes=[],
                    total_previsto=0,
                    modelo_usado=modelo_nome,
                )

        return PrevisaoOutput(
            id_requisicao=payload.id_requisicao,
            previsoes=previsoes,
            dataset_com_previsao_ref=dataset_com_previsao_ref,
            total_previsto=len(previsoes),
            modelo_usado=modelo_nome,
            metricas_negocio=metricas_negocio,
            intervalos_confianca=intervalos_confianca,
            erro_validacao=erro_validacao,
        )

    def _metricas_negocio_pred(self, pred_df: pd.DataFrame, col_pred: str, tipo: str) -> Dict[str, Any]:
        """Quantidade por classe (classificação) ou resumo (regressão)."""
        out: Dict[str, Any] = {}
        if tipo == "classificacao":
            out["quantidade_por_classe"] = pred_df[col_pred].astype(str).value_counts().astype(int).to_dict()
        else:
            out["media_prevista"] = float(pred_df[col_pred].mean())
            out["min_previsto"] = float(pred_df[col_pred].min())
            out["max_previsto"] = float(pred_df[col_pred].max())
        return out

    def _extrair_intervalos_regressao(self, pred_df: pd.DataFrame, df_original: pd.DataFrame) -> Optional[List[Dict[str, Any]]]:
        """Se PyCaret retornou prediction_lower/upper, monta lista de intervalos."""
        for low in ("prediction_lower", "Lower"):
            for up in ("prediction_upper", "Upper"):
                if low in pred_df.columns and up in pred_df.columns:
                    return [
                        {"lower": float(pred_df[low].iloc[i]), "upper": float(pred_df[up].iloc[i])}
                        for i in range(len(pred_df))
                    ]
        return None
