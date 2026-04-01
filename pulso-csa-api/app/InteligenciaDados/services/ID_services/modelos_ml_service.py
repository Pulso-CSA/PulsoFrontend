#━━━━━━━━━❮Serviço – Modelos ML (ID)❯━━━━━━━━━
# PyCaret compare_models, limiar 70%, persistência, importância de variáveis, motivo_precisao_baixa.
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from app.core.openai.openai_client import get_openai_client
from app.InteligenciaDados.models.ID_models.modelos_ml_models import ModelosMLInput, ModelosMLOutput
from app.prompts.loader import load_prompt
from app.InteligenciaDados.storage.id_artifacts.id_artifacts_io import (
    get_model_path,
    get_next_model_version,
    list_model_refs,
    load_dataframe,
    save_model_metadata,
)

logger = logging.getLogger(__name__)

# Limiar configurável via env (padrão 70%)
ACURACIA_MINIMA = float(os.getenv("ML_ACURACIA_MINIMA", "0.70"))


def _extrair_importancia_variaveis(model: Any, df: pd.DataFrame, target: str) -> List[Dict[str, Any]]:
    """Extrai importância de variáveis do pipeline (feature_importances_ ou coef_)."""
    try:
        pipe = model
        est = pipe[-1] if hasattr(pipe, "__getitem__") else model
        feats = [c for c in df.columns if c != target]
        if hasattr(pipe, "get_feature_names_out"):
            try:
                feats = list(pipe[:-1].get_feature_names_out())
            except Exception:
                pass
        if hasattr(est, "feature_importances_") and len(est.feature_importances_) == len(feats):
            imp = est.feature_importances_
            total = max(imp.sum(), 1e-9)
            return [{"variavel": str(f), "importancia": round(float(i) / total, 4)} for f, i in zip(feats, imp)]
        if hasattr(est, "coef_") and est.coef_ is not None:
            coef = est.coef_.ravel() if hasattr(est.coef_, "ravel") else est.coef_
            if len(coef) == len(feats):
                imp = abs(coef)
                total = max(imp.sum(), 1e-9)
                return [{"variavel": str(f), "importancia": round(float(i) / total, 4)} for f, i in zip(feats, imp)]
    except Exception as e:
        logger.debug("Importância de variáveis não disponível: %s", e)
    return []


def _treinar_com_pycaret(
    df: pd.DataFrame, target: str, tipo: str, acuracia_minima: float = ACURACIA_MINIMA, aplicar_balanceamento: bool = False
) -> Optional[Tuple[str, float, float, float, float, Any, str, Optional[List], Optional[List], Optional[float]]]:
    """Retorna (melhor_modelo_nome, accuracy, precision, recall, f1, modelo, tipo, matriz_confusao, modelos_comparados, auc) ou None."""
    try:
        if tipo == "regressao":
            from pycaret.regression import compare_models, setup
            setup(df, target=target, session_id=42, verbose=False)
            best = compare_models()
            from pycaret.regression import predict_model
            pred_df = predict_model(best, df)
            pred_col = None
            for c in ("prediction_label", "Label", "prediction"):
                if c in pred_df.columns:
                    pred_col = c
                    break
            if pred_col is None:
                extra = [c for c in pred_df.columns if c not in df.columns]
                pred_col = extra[-1] if extra else pred_df.columns[-1]
            y_true = df[target]
            y_pred = pred_df[pred_col]
            from sklearn.metrics import r2_score
            r2 = r2_score(y_true, y_pred)
            acc = max(0.0, min(1.0, (r2 + 1) / 2))
            return (str(best.__class__.__name__), acc, acc, acc, float(r2), best, "regressao", None, None, None)
        else:
            from pycaret.classification import compare_models, pull, setup
            from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score

            # Configurar balanceamento se solicitado
            setup_kwargs = {"session_id": 42, "verbose": False}
            if aplicar_balanceamento:
                # PyCaret suporta fix_imbalance=True para aplicar SMOTE automaticamente
                try:
                    setup_kwargs["fix_imbalance"] = True
                    logger.info("ModelosML: aplicando balanceamento de classes (SMOTE) no setup do PyCaret")
                except Exception as e:
                    logger.warning("ModelosML: fix_imbalance não disponível, tentando alternativa: %s", e)
                    # Alternativa: usar sampling_method
                    try:
                        setup_kwargs["sampling_method"] = "smote"
                    except Exception:
                        logger.warning("ModelosML: sampling_method também não disponível, continuando sem balanceamento")
            
            setup(df, target=target, **setup_kwargs)
            best = compare_models()
            try:
                leaderboard = pull()
                modelos_comparados = []
                if leaderboard is not None and not leaderboard.empty:
                    cols = [c for c in ("Model", "Accuracy", "AUC", "Recall", "Prec.", "F1", "Kappa", "MCC") if c in leaderboard.columns]
                    for idx, row in leaderboard.head(15).iterrows():
                        model_name = str(row.get("Model", idx)) if "Model" in leaderboard.columns else str(idx)
                        d: Dict[str, Any] = {"Model": model_name}
                        for c in cols:
                            if c != "Model":
                                v = row.get(c)
                                d[c] = round(float(v), 4) if pd.notna(v) and isinstance(v, (int, float)) else v
                        modelos_comparados.append(d)
            except Exception as lb_err:
                logger.debug("Leaderboard PyCaret não disponível: %s", lb_err)
                modelos_comparados = []

            from pycaret.classification import predict_model
            pred_df = predict_model(best, df)
            pred_col = "prediction_label" if "prediction_label" in pred_df.columns else [c for c in pred_df.columns if c not in df.columns][-1]
            y_true = df[target]
            y_pred = pred_df[pred_col]
            acc = accuracy_score(y_true, y_pred)
            if acc < acuracia_minima:
                return None
            prec = precision_score(y_true, y_pred, average="weighted", zero_division=0)
            rec = recall_score(y_true, y_pred, average="weighted", zero_division=0)
            f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
            cm = confusion_matrix(y_true, y_pred)
            matriz_confusao = cm.tolist()
            auc_val = 0.5
            try:
                from sklearn.metrics import roc_auc_score
                # PyCaret retorna "Score" ou "prediction_score"; verificar várias colunas
                score_col = next(
                    (c for c in ("Score", "prediction_score", "score") if c in pred_df.columns),
                    None,
                )
                if score_col is not None:
                    y_prob = pred_df[score_col]
                    if y_prob.nunique() > 1 and len(y_prob) == len(y_true):
                        n_classes = len(y_true.unique())
                        if n_classes == 2:
                            auc_val = float(roc_auc_score(y_true, y_prob))
                        else:
                            auc_val = float(roc_auc_score(y_true, y_prob, multi_class="ovr", average="weighted"))
                        if 0 < auc_val < 0.5:
                            auc_val = 1.0 - auc_val  # rótulos invertidos
            except Exception:
                pass
            return (str(best.__class__.__name__), acc, prec, rec, f1, best, "classificacao", matriz_confusao, modelos_comparados, auc_val)
    except Exception as e:
        logger.warning("PyCaret falhou: %s", e)
        return None


class ModelosMLService:
    """
    Carrega dataset tratado, identifica alvo, roda PyCaret compare_models.
    Só aceita modelo com acurácia >= 70%. LLM gera motivo e melhorias.
    """

    def __init__(self) -> None:
        self._llm = get_openai_client()

    def run(self, payload: ModelosMLInput) -> ModelosMLOutput:
        # Limiar configurável por request ou env
        acuracia_minima = payload.acuracia_minima if payload.acuracia_minima is not None else ACURACIA_MINIMA
        analise = payload.retorno_analise_estatistica or {}
        analise_interno = analise.get("analise_estatistica") or analise
        dataset_ref: Optional[str] = payload.dataset_ref or analise.get("dataset_ref")
        modelos_sugeridos = analise_interno.get("modelos_sugeridos", ["Random Forest", "XGBoost"])[:5]
        variavel_alvo = payload.variavel_alvo or (analise_interno.get("variaveis_alvo") or [None])[0]
        tipo = (payload.tipo_problema or "classificacao").lower()
        if tipo not in ("classificacao", "regressao"):
            tipo = "classificacao"

        modelo_escolhido: Optional[str] = None
        precisao, recall, f1, acuracia = 0.0, 0.0, 0.0, 0.0
        treinou_com_sucesso = False
        model_ref: Optional[str] = None
        usuario = payload.usuario or "default"
        importancia_variaveis: List[Dict[str, Any]] = []
        metricas_negocio: Dict[str, Any] = {}
        constatacoes_erro: Optional[str] = None
        matriz_confusao: Optional[List] = None
        modelos_comparados: Optional[List] = None
        auc: Optional[float] = None

        logger.info("ModelosML: run iniciado - dataset_ref=%s, variavel_alvo=%s, tipo=%s", "presente" if dataset_ref else "AUSENTE", variavel_alvo, tipo)
        if not dataset_ref:
            logger.warning("ModelosML: dataset_ref ausente - treino não será executado")
        if not variavel_alvo:
            logger.warning("ModelosML: variavel_alvo ausente - treino não será executado")

        if dataset_ref and variavel_alvo:
            try:
                logger.info("ModelosML: carregando dataset_ref (path_len=%d)", len(dataset_ref))
                df = load_dataframe(dataset_ref)
                logger.info("ModelosML: dataset carregado - shape=%s, colunas=%s", df.shape, list(df.columns)[:10])
                if variavel_alvo not in df.columns:
                    logger.warning("ModelosML: variavel_alvo '%s' não encontrada nas colunas; usando fallback", variavel_alvo)
                    variavel_alvo = df.select_dtypes(include=["number"]).columns[0] if not df.select_dtypes(include=["number"]).empty else df.columns[0]
                if df[variavel_alvo].nunique() < 2 and tipo == "classificacao":
                    tipo = "regressao"
                aplicar_balanceamento = payload.aplicar_balanceamento or False
                logger.info("ModelosML: iniciando PyCaret (target=%s, tipo=%s, acuracia_min=%s, balanceamento=%s)", variavel_alvo, tipo, acuracia_minima, aplicar_balanceamento)
                res = _treinar_com_pycaret(df, variavel_alvo, tipo, acuracia_minima, aplicar_balanceamento)
                if res:
                    treinou_com_sucesso = True
                    modelo_escolhido, acuracia, precisao, recall, f1, trained_model, tipo_salvo = res[0], res[1], res[2], res[3], res[4], res[5], res[6]
                    if len(res) >= 9:
                        matriz_confusao = res[7]
                        modelos_comparados = res[8]
                    if len(res) >= 10 and res[9] is not None:
                        auc = res[9]
                    features = [c for c in df.columns if c != variavel_alvo]
                    importancia_variaveis = _extrair_importancia_variaveis(trained_model, df, variavel_alvo)
                    metricas_negocio = {
                        "total_amostra": len(df),
                        "distribuicao_classe": df[variavel_alvo].value_counts().astype(int).to_dict() if tipo_salvo == "classificacao" else None,
                    }
                    nome_modelo = payload.versao or get_next_model_version(usuario, payload.id_requisicao)
                    try:
                        model_path = get_model_path(usuario, payload.id_requisicao, nome_modelo)
                        path_sem_ext = model_path.replace(".pkl", "")
                        if tipo_salvo == "regressao":
                            from pycaret.regression import save_model
                            save_model(trained_model, path_sem_ext)
                        else:
                            from pycaret.classification import save_model
                            save_model(trained_model, path_sem_ext)
                        model_ref = path_sem_ext
                        meta = {"features": features, "variavel_alvo": variavel_alvo, "tipo": tipo_salvo}
                        if treinou_com_sucesso and modelo_escolhido:
                            meta["modelo_escolhido"] = modelo_escolhido
                            meta["resultados"] = {"precisao": round(precisao, 4), "recall": round(recall, 4), "f1": round(f1, 4), "acuracia": round(acuracia, 4)}
                            if auc is not None:
                                meta["resultados"]["auc"] = round(auc, 4)
                        save_model_metadata(model_ref, meta)
                    except Exception as save_err:
                        logger.exception("ModelosML: falha ao salvar modelo - %s", save_err)
                else:
                    logger.warning("ModelosML: PyCaret retornou None (acuracia < %.0f%% ou erro interno)", acuracia_minima * 100)
            except ImportError as e:
                if "pycaret" in str(e).lower():
                    constatacoes_erro = "PyCaret não está instalado. Execute: pip install pycaret"
                    logger.warning("ModelosML: PyCaret não instalado - %s", e)
                else:
                    raise
            except Exception as e:
                logger.exception("ModelosML: falha ao treinar modelo - %s", e)

        if treinou_com_sucesso:
            constatacoes = f"Modelo atende ao limiar mínimo de {acuracia_minima:.0%} de acurácia." if acuracia >= acuracia_minima else f"Nenhum modelo atingiu {acuracia_minima:.0%} de acurácia. Recomenda-se mais dados ou feature engineering."
        elif constatacoes_erro:
            constatacoes = constatacoes_erro
        else:
            constatacoes = "Treino não executado (falta de dados, variável alvo ou acurácia insuficiente)."

        motivo_precisao_baixa: Optional[str] = None
        if treinou_com_sucesso and acuracia < acuracia_minima and dataset_ref and variavel_alvo:
            try:
                df_ctx = load_dataframe(dataset_ref)
                n_amostras = len(df_ctx)
                dist = df_ctx[variavel_alvo].value_counts().to_dict() if variavel_alvo in df_ctx.columns else {}
                n_feats = len([c for c in df_ctx.columns if c != variavel_alvo])
                prompt_motivo = load_prompt("ID_prompts/modelos_ml_motivo_precisao").format(
                    acuracia=f"{acuracia:.2%}",
                    n_amostras=n_amostras,
                    n_feats=n_feats,
                    distribuicao=dist
                )
                motivo_precisao_baixa = self._llm.generate_text(prompt_motivo, use_fast_model=True).strip()
            except Exception as e:
                logger.warning("LLM motivo precisão baixa falhou: %s", e)
                motivo_precisao_baixa = "Possíveis causas: poucos dados para treino, desbalanceamento de classes ou variáveis com pouca capacidade preditiva. Aumente a amostra ou faça balanceamento/engenharia de features."

        motivo = ""
        melhorias: List[str] = []
        if treinou_com_sucesso and modelo_escolhido:
            prompt = load_prompt("ID_prompts/modelos_ml_justificativa").format(
                modelo_escolhido=modelo_escolhido,
                precisao=f"{precisao:.2f}",
                recall=f"{recall:.2f}",
                f1=f"{f1:.2f}"
            )
            try:
                explicacao = self._llm.generate_text(prompt, use_fast_model=True).strip()
            except Exception as e:
                logger.warning("LLM modelos_ml falhou: %s", e)
                explicacao = f"Modelo {modelo_escolhido} com melhor métrica agregada. Aumentar amostragem de classes raras."
            partes = explicacao.split(". ")
            motivo = partes[0] + "." if partes else explicacao
            melhorias = [partes[1].strip()] if len(partes) > 1 else ["Aumentar amostragem ou balanceamento."]

        modelo_ml_dict: Dict[str, Any] = {
            "modelo_escolhido": modelo_escolhido or "N/A",
            "motivo": motivo,
            "constatacoes": constatacoes,
            "melhorias_recomendadas": melhorias,
        }
        if treinou_com_sucesso:
            resultados_dict: Dict[str, Any] = {"precisao": round(precisao, 4), "recall": round(recall, 4), "f1": round(f1, 4), "acuracia": round(acuracia, 4)}
            if auc is not None:
                resultados_dict["auc"] = round(auc, 4)
            modelo_ml_dict["resultados"] = resultados_dict
        if motivo_precisao_baixa:
            modelo_ml_dict["motivo_precisao_baixa"] = motivo_precisao_baixa
        if importancia_variaveis:
            modelo_ml_dict["importancia_variaveis"] = importancia_variaveis
        if metricas_negocio:
            modelo_ml_dict["metricas_negocio"] = metricas_negocio
        if matriz_confusao:
            modelo_ml_dict["matriz_confusao"] = matriz_confusao
        if modelos_comparados is not None:
            modelo_ml_dict["modelos_comparados"] = modelos_comparados
            # Aviso quando Recall/Prec/F1 são 0 para todos (comum em dados desbalanceados)
            def _eh_zero(v: Any) -> bool:
                return v is None or v == 0 or v == 0.0
            todos_zero = all(
                _eh_zero(row.get("Recall")) and _eh_zero(row.get("Prec.")) and _eh_zero(row.get("F1"))
                for row in modelos_comparados if isinstance(row, dict)
            )
            if todos_zero and len(modelos_comparados) > 0:
                modelo_ml_dict["aviso_metricas"] = (
                    "Recall, Precisão e F1 em 0% podem indicar predição apenas da classe majoritária. "
                    "Considere balanceamento (SMOTE/undersampling) ou revisar variáveis."
                )

        lista_refs: Optional[List[str]] = None
        try:
            lista_refs = list_model_refs(usuario, payload.id_requisicao)
        except Exception:
            pass

        return ModelosMLOutput(
            id_requisicao=payload.id_requisicao,
            modelo_ml=modelo_ml_dict,
            model_ref=model_ref,
            lista_model_refs=lista_refs,
        )
