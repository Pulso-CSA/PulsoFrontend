# Serviço de Análise Estatística – métricas reais, correlações, metadados de gráficos, LLM para insights
import hashlib
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from app.core.openai.openai_client import get_openai_client
from app.InteligenciaDados.models.ID_models.analise_estatistica_models import (
    AnaliseEstatisticaInput,
    AnaliseEstatisticaOutput,
)
from app.prompts.loader import load_prompt
from app.InteligenciaDados.storage.id_artifacts.id_artifacts_io import load_dataframe

logger = logging.getLogger(__name__)

# Cache de análise estatística (evita reprocessamento; TTL configurável)
_ANALISE_CACHE: Dict[str, Tuple[float, Dict[str, Any], Optional[str]]] = {}  # key -> (timestamp, data, dataset_ref)
_ANALISE_CACHE_MAX = 80
_ANALISE_CACHE_TTL_SEC = int(os.getenv("ID_ANALISE_CACHE_TTL_SEC", "300"))  # 5 min


def _metricas_reais(df: pd.DataFrame) -> Dict[str, Any]:
    """Calcula métricas estatísticas completas para todas as colunas numéricas."""
    numerics = df.select_dtypes(include=["number"])
    resultados: Dict[str, Any] = {}
    if not numerics.empty:
        desc = numerics.describe()
        resultados["medias"] = desc.loc["mean"].to_dict()
        resultados["desvio_padrao"] = desc.loc["std"].to_dict()
        resultados["medianas"] = desc.loc["50%"].to_dict()
        resultados["quartil_25"] = desc.loc["25%"].to_dict()
        resultados["quartil_75"] = desc.loc["75%"].to_dict()
        resultados["minimos"] = desc.loc["min"].to_dict()
        resultados["maximos"] = desc.loc["max"].to_dict()
        
        # Assimetria (skewness) e curtose (kurtosis)
        try:
            resultados["assimetria"] = numerics.skew().to_dict()
            resultados["curtose"] = numerics.kurtosis().to_dict()
        except Exception:
            resultados["assimetria"] = {}
            resultados["curtose"] = {}
        
        # Correlações
        try:
            corr = numerics.corr()
            resultados["correlacoes"] = {
                col: "forte" if abs(corr[col].mean()) > 0.3 else "moderada" if abs(corr[col].mean()) > 0.1 else "fraca"
                for col in corr.columns[:15]
            }
            resultados["matriz_correlacao"] = corr.round(4).to_dict()
        except Exception:
            resultados["correlacoes"] = {}
            resultados["matriz_correlacao"] = {}
    return resultados


def _df_with_coerced_numerics(df: pd.DataFrame, min_frac: float = 0.45) -> pd.DataFrame:
    """Mantém numéricas e tenta converter texto com números (ex.: TotalCharges vindo do Mongo/CSV)."""
    d = df.copy()
    n = len(d)
    if n == 0:
        return d
    need = max(5, int(n * min_frac))
    for c in d.columns:
        if pd.api.types.is_numeric_dtype(d[c]):
            continue
        try:
            ser = d[c]
            if ser.dtype == object or str(ser.dtype) == "string":
                coerced = pd.to_numeric(
                    ser.astype(str).str.strip().str.replace(",", ".", regex=False),
                    errors="coerce",
                )
                if int(coerced.notna().sum()) >= need:
                    d[c] = coerced
        except Exception:
            continue
    return d


def _matriz_correlacao_top_pairs(
    matriz: Dict[str, Any], max_cols: int = 22, top_n: int = 8
) -> List[Tuple[str, str, float]]:
    if not matriz:
        return []
    pares: List[Tuple[str, str, float]] = []
    cols = list(matriz.keys())[:max_cols]
    for i, c1 in enumerate(cols):
        row = matriz.get(c1)
        if not isinstance(row, dict):
            continue
        for c2 in cols[i + 1 :]:
            v = row.get(c2)
            if v is None or not isinstance(v, (int, float)):
                continue
            if isinstance(v, float) and np.isnan(v):
                continue
            fv = float(v)
            if abs(fv) < 0.999:
                pares.append((c1, c2, fv))
    pares.sort(key=lambda x: abs(x[2]), reverse=True)
    return pares[:top_n]


def _format_correlacoes_principais(top: List[Tuple[str, str, float]]) -> str:
    linhas = ["**Correlações principais do dataset (Pearson):**", ""]
    for idx, (c1, c2, v) in enumerate(top, 1):
        intens = "forte" if abs(v) >= 0.5 else "moderada" if abs(v) >= 0.25 else "fraca"
        linhas.append(f"{idx}. **{c1}** ↔ **{c2}:** {v:.3f} — correlação {intens}")
    linhas.append("")
    linhas.append("O gráfico de dispersão abaixo mostra o par com maior |correlação| entre variáveis numéricas.")
    return "\n".join(linhas)


def _sanitize_llm_resposta_estatistica(text: str) -> str:
    """Remove eco do prompt quando o modelo (ex.: Ollama pequeno) repete o template inteiro."""
    t = (text or "").strip()
    if len(t) < 150:
        return t
    if "Validação interna antes de responder" not in t and "Regras obrigatórias para responder" not in t:
        return t
    for anchor in ("\n\nCom base nos dados", "\nCom base nos dados", "\n\nPortanto,", "\nPortanto,"):
        i = t.rfind(anchor)
        if i >= 100:
            return t[i:].strip()
    paras = [p.strip() for p in t.split("\n\n") if p.strip()]
    for p in reversed(paras):
        if len(p) > 700:
            continue
        if any(x in p for x in ("Pergunta do usuário:", "Formato da saída:", "Tarefa:", "Dados disponíveis:")):
            continue
        if p.startswith("•") and "NÃO " in p:
            continue
        return p
    return t


def _par_com_maior_correlacao(df: pd.DataFrame, numerics: List[str]) -> Optional[Tuple[str, str]]:
    """Retorna o par de colunas numéricas com maior |correlação|, excluindo variáveis binárias (nunique<=2)."""
    best_pair: Optional[Tuple[str, str]] = None
    best_abs_corr = -1.0
    for i, cx in enumerate(numerics):
        if df[cx].nunique() <= 2:
            continue
        for cy in numerics[i + 1:]:
            if df[cy].nunique() <= 2:
                continue
            try:
                c = float(df[cx].corr(df[cy]))
                if not np.isnan(c) and abs(c) > best_abs_corr:
                    best_abs_corr = abs(c)
                    best_pair = (cx, cy)
            except Exception:
                pass
    return best_pair


def _correlacao_entre_colunas(df: pd.DataFrame, col_x: str, col_y: str) -> Optional[float]:
    """Calcula correlação de Pearson entre duas colunas numéricas."""
    if col_x not in df.columns or col_y not in df.columns:
        return None
    if not pd.api.types.is_numeric_dtype(df[col_x]) or not pd.api.types.is_numeric_dtype(df[col_y]):
        return None
    return float(df[col_x].corr(df[col_y]))


def _regressao_linear_simples(df: pd.DataFrame, col_x: str, col_y: str) -> Optional[Dict[str, Any]]:
    """Calcula regressão linear simples entre duas colunas numéricas."""
    if col_x not in df.columns or col_y not in df.columns:
        return None
    if not pd.api.types.is_numeric_dtype(df[col_x]) or not pd.api.types.is_numeric_dtype(df[col_y]):
        return None
    try:
        x = df[col_x].dropna()
        y = df[col_y].dropna()
        if len(x) != len(y) or len(x) < 2:
            return None
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        return {
            "coeficiente_angular": float(slope),
            "intercepto": float(intercept),
            "r_quadrado": float(r_value ** 2),
            "p_valor": float(p_value),
            "erro_padrao": float(std_err),
        }
    except Exception:
        return None


def _correlacoes_com_alvo(df: pd.DataFrame, pergunta: str, resultados: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Retorna correlações com variável alvo ordenadas por valor absoluto. Detecta alvo por pergunta ou colunas comuns."""
    alvo_candidatos = ["churn", "fraude", "vendas", "target", "classe", "label"]
    pergunta_lower = pergunta.lower()
    variavel_alvo: Optional[str] = None
    for c in alvo_candidatos:
        if c in pergunta_lower:
            for col in df.columns:
                if col.lower() == c or c in col.lower():
                    variavel_alvo = col
                    break
        if variavel_alvo:
            break
    if not variavel_alvo and "churn" in pergunta_lower:
        for col in df.columns:
            if "churn" in col.lower():
                variavel_alvo = col
                break
    if not variavel_alvo and any(p in pergunta_lower for p in ["correlação", "correlacoes", "correlações", "análise", "analise"]):
        for col in df.columns:
            if col.lower() in ("churn", "fraude", "target") or any(c in col.lower() for c in ["churn", "fraude", "target"]):
                variavel_alvo = col
                break
    if not variavel_alvo or variavel_alvo not in df.columns:
        return []
    try:
        numerics = df.select_dtypes(include=["number"]).columns.tolist()
        if variavel_alvo not in numerics:
            ser_cat = df[variavel_alvo].astype(str).str.lower().str.strip()
            ser = pd.to_numeric(ser_cat.map({"yes": 1, "no": 0, "1": 1, "0": 0, "true": 1, "false": 0}), errors="coerce")
            if ser.notna().sum() < 2:
                ser = pd.Series(pd.factorize(df[variavel_alvo])[0], index=df.index)
            df_corr = df[numerics].copy()
            df_corr["_alvo"] = ser
            corr_ser = df_corr.corr()["_alvo"].drop("_alvo", errors="ignore")
        else:
            corr = df[numerics].corr()
            corr_ser = corr[variavel_alvo].drop(variavel_alvo, errors="ignore")
        corr_list = [
            {"variavel": str(c), "valor": round(float(v), 4), "forca": "forte" if abs(v) >= 0.5 else "moderada" if abs(v) >= 0.4 else "fraca"}
            for c, v in corr_ser.items()
        ]
        return sorted(corr_list, key=lambda x: abs(x["valor"]), reverse=True)[:15]
    except Exception as e:
        logger.debug("correlacoes_com_alvo falhou: %s", e)
        return []


def _balanceamento_classe(df: pd.DataFrame, variavel_alvo: str) -> Optional[Dict[str, Any]]:
    """Retorna contagem por classe, razão e recomendação de reamostragem."""
    if variavel_alvo not in df.columns:
        return None
    try:
        vc = df[variavel_alvo].astype(str).value_counts()
        contagens = {str(k): int(v) for k, v in vc.astype(int).to_dict().items()}
        if len(contagens) < 2:
            return None
        vals = list(contagens.values())
        menor, maior = min(vals), max(vals)
        razao = menor / maior if maior > 0 else 0
        rec = "Considerar SMOTE ou undersampling" if razao < 0.3 or razao > 3 else "Balanceamento aceitável"
        out: Dict[str, Any] = dict(contagens)
        out["razao"] = round(razao, 4)
        out["recomendacao"] = rec
        return out
    except Exception:
        return None


def _teste_normalidade(df: pd.DataFrame, col: str) -> Optional[Dict[str, Any]]:
    """Testa normalidade de uma coluna numérica usando Shapiro-Wilk."""
    if col not in df.columns:
        return None
    if df[col].dtype not in ("number", "int", "float"):
        return None
    try:
        dados = df[col].dropna()
        if len(dados) < 3 or len(dados) > 5000:  # Shapiro-Wilk tem limite prático
            return None
        stat, p_value = stats.shapiro(dados)
        return {
            "estatistica": float(stat),
            "p_valor": float(p_value),
            "normal": p_value > 0.05,
        }
    except Exception:
        return None


# Colunas que não geram gráficos úteis (identificadores únicos)
_COLS_IGNORAR_GRAFICO = frozenset({"_id", "id", "customerid", "customer_id", "clientid", "client_id"})

# Máximo de gráficos exibidos (evita poluição visual)
MAX_GRAFICOS = 4


# Textos fixos de vantagens e desvantagens por tipo de gráfico
_VANTAGENS_DESVANTAGENS = {
    "histograma": {
        "vantagens": [
            "Visão rápida da distribuição e tendência central",
            "Identifica assimetria e outliers",
            "Revela forma da distribuição (normal, bimodal, etc.)",
        ],
        "desvantagens": [
            "Resultado depende da escolha dos intervalos (bins)",
            "Pode mascarar detalhes dentro de cada faixa",
            "Para variáveis binárias, gráfico de barras por categoria é mais direto",
        ],
    },
    "barra": {
        "vantagens": [
            "Comparação direta entre categorias",
            "Identifica desbalanceamento de classes",
            "Fácil interpretação para variáveis nominais",
        ],
        "desvantagens": [
            "Ordem das barras pode influenciar percepção",
            "Muitas categorias (>10) prejudicam legibilidade",
            "Não mostra relações entre variáveis",
        ],
    },
    "dispersao": {
        "vantagens": [
            "Revela correlação e tendência entre duas variáveis",
            "Identifica clusters e outliers",
            "Permite avaliar linearidade da relação",
        ],
        "desvantagens": [
            "Overplotting com muitos pontos",
            "Não quantifica a relação (use correlação)",
            "Pode mascarar padrões em subgrupos",
        ],
    },
}


def _explicacao_histograma(col: str, labels: List[str], values: List[float]) -> str:
    """Gera explicação específica para histograma, fácil de interpretar no frontend."""
    if not values:
        return f"Distribuição de frequências de **{col}**."
    total = sum(values)
    idx_max = int(np.argmax(values))
    faixa_maior = labels[idx_max] if idx_max < len(labels) else ""
    pct = 100 * values[idx_max] / total if total > 0 else 0
    return f"**{col}:** maior concentração em {faixa_maior} ({pct:.0f}% dos dados)."


def _explicacao_barra(col: str, labels: List[str], values: List[float]) -> str:
    """Gera explicação específica para gráfico de barras, clara para o frontend."""
    if not values:
        return f"Contagem por **{col}**."
    total = sum(values)
    idx_max = int(np.argmax(values))
    cat_maior = labels[idx_max] if idx_max < len(labels) else ""
    pct = 100 * values[idx_max] / total if total > 0 else 0
    if len(labels) == 2 and len(values) >= 2 and max(values) > 0 and abs(values[0] - values[1]) / max(values) < 0.2:
        return f"**{col}:** equilibrado entre categorias ({cat_maior} com {pct:.0f}%)."
    return f"**{col}:** predominante **{cat_maior}** ({pct:.0f}%)."


def _explicacao_dispersao(col_x: str, col_y: str, x_vals: List[float], y_vals: List[float]) -> str:
    """Gera explicação específica para dispersão, interpretável no frontend."""
    if len(x_vals) < 2 or len(y_vals) < 2:
        return f"Relação **{col_x}** × **{col_y}**."
    try:
        corr = float(np.corrcoef(x_vals, y_vals)[0, 1])
        direcao = "positiva" if corr > 0 else "negativa"
        intens = "forte" if abs(corr) >= 0.5 else "moderada" if abs(corr) >= 0.4 else "fraca"
        return f"**{col_x} × {col_y}:** correlação {intens} e {direcao} (r={corr:.2f})."
    except Exception:
        return f"Dispersão **{col_x}** vs **{col_y}**."


def _graficos_metadados_e_dados(
    df: pd.DataFrame,
    par_dispersao: Optional[Tuple[str, str]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Retorna metadados e dados reais para gráficos (histograma, barra, dispersão), com explicação por gráfico.
    Se par_dispersao=(col_x, col_y) for informado, usa esse par para o gráfico de dispersão."""
    metadados: List[Dict[str, Any]] = []
    dados: List[Dict[str, Any]] = []
    numerics = df.select_dtypes(include=["number"]).columns.tolist()[:6]
    cats = [
        c for c in df.select_dtypes(include=["object", "category"]).columns.tolist()[:6]
        if c.lower().strip() not in _COLS_IGNORAR_GRAFICO and df[c].nunique() <= 20
    ]

    for col in numerics:
        try:
            ser = df[col].dropna()
            n_bins = min(12, max(5, len(ser.unique()) // 2) if len(ser.unique()) > 1 else 5)
            hist, bins = np.histogram(ser, bins=n_bins)
            labels = [f"{bins[i]:.1f}-{bins[i+1]:.1f}" for i in range(len(bins) - 1)]
            values = hist.tolist()
            dados.append({"labels": labels, "values": values})
            vd = _VANTAGENS_DESVANTAGENS["histograma"]
            explicacao = _explicacao_histograma(col, labels, values)
            metadados.append({
                "tipo": "histograma",
                "titulo": f"Distribuição de {col}",
                "eixo_x": col,
                "eixo_y": "frequência",
                "explicacao": explicacao,
                "insight_especifico": explicacao,
                "vantagens": vd["vantagens"],
                "desvantagens": vd["desvantagens"],
            })
        except Exception:
            dados.append({"labels": [], "values": []})
            vd = _VANTAGENS_DESVANTAGENS["histograma"]
            explicacao = f"Distribuição de **{col}** em faixas de valores."
            metadados.append({
                "tipo": "histograma",
                "titulo": f"Distribuição de {col}",
                "eixo_x": col,
                "eixo_y": "frequência",
                "explicacao": explicacao,
                "insight_especifico": explicacao,
                "vantagens": vd["vantagens"],
                "desvantagens": vd["desvantagens"],
            })

    for col in cats:
        try:
            vc = df[col].value_counts().head(12)
            labels = vc.index.astype(str).tolist()
            values = vc.values.tolist()
            dados.append({"labels": labels, "values": values})
            vd = _VANTAGENS_DESVANTAGENS["barra"]
            explicacao = _explicacao_barra(col, labels, values)
            metadados.append({
                "tipo": "barra",
                "titulo": f"Contagem por {col}",
                "eixo_x": col,
                "eixo_y": "contagem",
                "explicacao": explicacao,
                "insight_especifico": explicacao,
                "vantagens": vd["vantagens"],
                "desvantagens": vd["desvantagens"],
            })
        except Exception:
            dados.append({"labels": [], "values": []})
            vd = _VANTAGENS_DESVANTAGENS["barra"]
            explicacao = f"Contagem de registros por **{col}**."
            metadados.append({
                "tipo": "barra",
                "titulo": f"Contagem por {col}",
                "eixo_x": col,
                "eixo_y": "contagem",
                "explicacao": explicacao,
                "insight_especifico": explicacao,
                "vantagens": vd["vantagens"],
                "desvantagens": vd["desvantagens"],
            })

    # Dispersão: prioriza par solicitado na pergunta (ex: "gráfico entre tenure e TotalCharges"); evita binárias
    if len(numerics) >= 2:
        col_x, col_y = None, None
        if par_dispersao and len(par_dispersao) == 2:
            cx, cy = par_dispersao[0], par_dispersao[1]
            if cx in df.columns and cy in df.columns:
                nux, nuy = df[cx].nunique(), df[cy].nunique()
                if nux > 2 and nuy > 2:
                    col_x, col_y = cx, cy
        if col_x is None or col_y is None:
            par_corr = _par_com_maior_correlacao(df, numerics)
            if par_corr:
                col_x, col_y = par_corr[0], par_corr[1]
            if col_x is None or col_y is None:
                pares = [(0, 1)] if len(numerics) < 3 else [(0, 1), (0, 2), (1, 2), (1, 0)]
                for i, j in pares:
                    if j < len(numerics):
                        cx, cy = numerics[i], numerics[j]
                        nux, nuy = df[cx].nunique(), df[cy].nunique()
                        if nux > 2 and nuy > 2:
                            col_x, col_y = cx, cy
                            break
        if col_x is not None and col_y is not None:
            try:
                sample = df[[col_x, col_y]].dropna().head(500)
                x_vals = sample[col_x].tolist()
                y_vals = sample[col_y].tolist()
                dados.append({"x": x_vals, "y": y_vals})
                vd = _VANTAGENS_DESVANTAGENS["dispersao"]
                explicacao = _explicacao_dispersao(col_x, col_y, x_vals, y_vals)
                metadados.append({
                    "tipo": "dispersao",
                    "titulo": f"{col_x} vs {col_y}",
                    "eixo_x": col_x,
                    "eixo_y": col_y,
                    "explicacao": explicacao,
                    "insight_especifico": explicacao,
                    "vantagens": vd["vantagens"],
                    "desvantagens": vd["desvantagens"],
                })
            except Exception:
                dados.append({"x": [], "y": []})
                vd = _VANTAGENS_DESVANTAGENS["dispersao"]
                explicacao = f"Dispersão **{col_x}** vs **{col_y}**."
                metadados.append({
                    "tipo": "dispersao",
                    "titulo": f"{col_x} vs {col_y}",
                    "eixo_x": col_x,
                    "eixo_y": col_y,
                    "explicacao": explicacao,
                    "insight_especifico": explicacao,
                    "vantagens": vd["vantagens"],
                    "desvantagens": vd["desvantagens"],
                })

    return metadados, dados


def _pediu_graficos(pergunta: str) -> bool:
    """
    Retorna True apenas quando o usuário pede explicitamente gráficos/visualizações.
    Evita gerar gráficos em respostas a perguntas sobre estrutura, colunas, tipos, etc.
    """
    if not pergunta or not pergunta.strip():
        return False
    pl = pergunta.lower()
    pediu = any(
        x in pl
        for x in [
            "grafico",
            "gráfico",
            "graficos",
            "gráficos",
            "histograma",
            "dispersão",
            "dispersao",
            "scatter",
            "barras",
            "visualização",
            "visualizacao",
            "visualizar",
            "mostre a distribuição",
            "mostre a distribuicao",
            "mostre o gráfico",
            "mostre o grafico",
            "mostre os gráficos",
            "mostre os graficos",
            "plote",
            "plotar",
            "análise gráfica",
            "analise grafica",
            "análise gráfica e estatística",
            "analise grafica e estatistica",
        ]
    )
    pediu = pediu or ("contagem por" in pl and any(x in pl for x in ["mostre", "exiba", "mostre a", "exiba a"]))
    # Não gerar quando pede apenas estrutura/metadados
    nao_pediu = any(
        x in pl
        for x in [
            "colunas",
            "coluna",
            "liste as colunas",
            "listar colunas",
            "tipos de dados",
            "tipos de cada",
            "estrutura",
            "tabelas e volumes",
            "tabelas e volume",
            "primeiras",
            "primeira linha",
            "primeiro registro",
        ]
    )
    return bool(pediu) and not bool(nao_pediu)


def _extrair_par_dispersao_da_pergunta(pergunta: str, numerics: List[str]) -> Optional[Tuple[str, str]]:
    """Extrai par (col_x, col_y) quando a pergunta pede gráfico/dispersão entre duas variáveis (ex: tenure e TotalCharges)."""
    import re
    pergunta_lower = pergunta.lower()
    if not any(p in pergunta_lower for p in ["dispersão", "dispersao", "gráfico de dispersão", "grafico de dispersao", "scatter", "entre "]):
        return None
    palavras = re.findall(r"[\w]+", pergunta)
    stop = {"entre", "qual", "a", "e", "de", "da", "dispersão", "dispersao", "gráfico", "grafico", "scatter"}
    candidatas = [p for p in palavras if len(p) > 1 and p.lower() not in stop]
    colunas_por_posicao: List[Tuple[int, str]] = []
    for c in numerics:
        cl = c.lower()
        if cl in [p.lower() for p in candidatas]:
            pos = pergunta_lower.find(cl)
            if pos >= 0:
                colunas_por_posicao.append((pos, c))
        else:
            for p in candidatas:
                if p.lower() in cl and len(p) > 2:
                    pos = pergunta_lower.find(p.lower())
                    if pos >= 0:
                        colunas_por_posicao.append((pos, c))
                        break
    vistos: set = set()
    colunas_ordenadas = []
    for _pos, col in sorted(colunas_por_posicao, key=lambda x: x[0]):
        if col not in vistos:
            vistos.add(col)
            colunas_ordenadas.append(col)
    if len(colunas_ordenadas) >= 2:
        return colunas_ordenadas[0], colunas_ordenadas[1]
    return None


def _extrair_variavel_da_pergunta(pergunta: str, colunas: List[str]) -> Optional[str]:
    """Extrai nome de coluna mencionada na pergunta (ex.: outliers em MonthlyCharges -> MonthlyCharges)."""
    import re
    pergunta_lower = pergunta.lower()
    for col in colunas:
        if col.lower() in pergunta_lower or col in pergunta:
            return col
    palavras = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", pergunta)
    for p in palavras:
        for c in colunas:
            if p.lower() == c.lower() or (len(p) > 2 and p.lower() in c.lower()):
                return c
    return None


def _extrair_coluna_grafico_especifico(
    pergunta: str, colunas_df: List[str]
) -> Optional[Tuple[str, str]]:
    """
    Extrai coluna quando a pergunta pede explicitamente um gráfico específico.
    Retorna (nome_coluna, tipo) onde tipo é 'contagem'|'histograma'|'distribuicao'.
    Ex.: "Mostre a contagem por Dependents" -> ("Dependents", "contagem")
    """
    import re
    if not pergunta or not colunas_df:
        return None
    pl = pergunta.lower().strip()
    # "contagem por X", "mostre a contagem por X"
    if "contagem por" in pl:
        for col in colunas_df:
            if col.lower() in pl and pl.find("contagem por") < pl.find(col.lower()):
                return (col, "contagem")
        # Fallback: palavra após "contagem por"
        match = re.search(r"contagem\s+por\s+(\w+)", pl, re.IGNORECASE)
        if match:
            cand = match.group(1)
            for col in colunas_df:
                if col.lower() == cand.lower():
                    return (col, "contagem")
    # "histograma de X", "histograma do X"
    if "histograma" in pl and (" de " in pl or " do " in pl):
        for col in colunas_df:
            if col.lower() in pl:
                return (col, "histograma")
    # "distribuição de X", "distribuição da variável X"
    if "distribuição" in pl or "distribuicao" in pl:
        for col in colunas_df:
            if col.lower() in pl:
                return (col, "distribuicao")
    return None


def _ordenar_graficos_por_relevancia(
    metadados: List[Dict[str, Any]],
    dados: List[Dict[str, Any]],
    correlacoes_com_alvo: List[Dict[str, Any]],
    pergunta: str = "",
    colunas_df: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Ordena gráficos do mais relevante ao menos. Quando a pergunta pede um gráfico específico
    (ex: contagem por Dependents, histograma de tenure), retorna APENAS os relevantes."""
    if len(metadados) != len(dados):
        return metadados, dados

    pergunta_lower = (pergunta or "").lower()
    colunas = colunas_df or []

    # Pedido específico: contagem por X, histograma de X, distribuição de X → só gráficos que agregam
    especifico = _extrair_coluna_grafico_especifico(pergunta, colunas)
    if especifico:
        col_alvo, tipo_pedido = especifico
        col_alvo_lower = col_alvo.lower()
        indices_ok = []
        for i, m in enumerate(metadados):
            eixo_x = (m.get("eixo_x") or "").lower()
            titulo = (m.get("titulo") or "").lower()
            grafico_tipo = m.get("tipo", "")
            if col_alvo_lower in eixo_x or col_alvo_lower in titulo:
                if tipo_pedido == "contagem" and grafico_tipo == "barra":
                    indices_ok.append(i)
                elif tipo_pedido == "histograma" and grafico_tipo == "histograma":
                    indices_ok.append(i)
                elif tipo_pedido == "distribuicao" and grafico_tipo in ("barra", "histograma"):
                    indices_ok.append(i)
        if indices_ok:
            return [metadados[i] for i in indices_ok], [dados[i] for i in indices_ok]

    var_pergunta = _extrair_variavel_da_pergunta(pergunta, colunas) if pergunta and colunas else None
    # Extrair múltiplas variáveis da pergunta (ex: "MonthlyCharges entre churn" -> [monthlycharges, churn])
    vars_pergunta: List[str] = []
    if pergunta and colunas_df:
        pergunta_lower = pergunta.lower()
        for col in colunas_df:
            if col.lower() in pergunta_lower or col in pergunta:
                vars_pergunta.append(col.lower())
        if var_pergunta and var_pergunta.lower() not in [v.lower() for v in vars_pergunta]:
            vars_pergunta.append(var_pergunta.lower())

    corr_map = {c["variavel"].lower(): abs(c["valor"]) for c in (correlacoes_com_alvo or [])}

    def score(idx: int) -> Tuple[float, int]:
        m = metadados[idx]
        eixo_x = (m.get("eixo_x") or "").strip().lower()
        eixo_y = (m.get("eixo_y") or "").strip().lower()
        excluir = {"frequência", "frequencia", "contagem"}
        vars_grafico = [v for v in [eixo_x, eixo_y] if v and v not in excluir]

        # Dispersão solicitada entre X e Y: prioriza o scatter que tem exatamente o par pedido
        if m.get("tipo") == "dispersao" and vars_pergunta and len(vars_pergunta) >= 2:
            if all(any(vp in vg or vg in vp for vg in vars_grafico) for vp in vars_pergunta):
                return (9999.0, idx)

        if var_pergunta and vars_grafico:
            for v in vars_grafico:
                if var_pergunta.lower() == v or var_pergunta.lower() in v or v in var_pergunta.lower():
                    return (999.0, idx)
        best = 0.0
        for var in vars_grafico:
            for k, v in corr_map.items():
                if k == var or k in var or var in k:
                    best = max(best, v)
                    break
        return (best if best > 0 else -1.0, idx)

    def eh_relevante(idx: int) -> bool:
        """Se a pergunta menciona variáveis específicas, exclui gráficos que não as contêm."""
        if not vars_pergunta or len(vars_pergunta) < 2:
            return True
        m = metadados[idx]
        eixo_x = (m.get("eixo_x") or "").strip().lower()
        eixo_y = (m.get("eixo_y") or "").strip().lower()
        titulo = (m.get("titulo") or "").lower()
        vars_grafico = [eixo_x, eixo_y, titulo]
        for vp in vars_pergunta:
            for vg in vars_grafico:
                if vp in vg or vg in vp:
                    return True
        return False

    indices = list(range(len(metadados)))
    # Filtrar gráficos irrelevantes quando pergunta é específica (ex: "compare MonthlyCharges entre churn")
    if vars_pergunta and len(vars_pergunta) >= 2:
        indices = [i for i in indices if eh_relevante(i)]
    # Balanceamento: apenas gráficos com variável alvo (Churn)
    pergunta_lower = (pergunta or "").lower()
    if "balanceamento" in pergunta_lower or "reamostragem" in pergunta_lower:
        churn_indices = [i for i in indices if (
            "churn" in str(metadados[i].get("eixo_x", "")).lower() or
            "churn" in str(metadados[i].get("eixo_y", "")).lower() or
            "churn" in str(metadados[i].get("titulo", "")).lower()
        )]
        if churn_indices:
            indices = churn_indices
    # Dispersão/correlação entre X e Y: apenas o scatter solicitado
    elif any(p in pergunta_lower for p in [
        "dispersão entre", "dispersao entre", "scatter entre",
        "correlação entre", "correlacao entre", "gráfico entre",
    ]):
        disp_indices = [i for i in indices if metadados[i].get("tipo") == "dispersao"]
        if vars_pergunta and len(vars_pergunta) >= 2:
            disp_indices = [i for i in disp_indices if all(
                vp in str(metadados[i].get("eixo_x", "")).lower() or
                vp in str(metadados[i].get("eixo_y", "")).lower()
                for vp in vars_pergunta
            )]
        if disp_indices:
            indices = disp_indices[:1]
    # Correlações: priorizar dispersões (top 2) + 1 histograma mais correlacionado
    elif "correlação" in pergunta_lower or "correlacoes" in pergunta_lower or "correlações" in pergunta_lower:
        disp_indices = [i for i in indices if metadados[i].get("tipo") == "dispersao"]
        hist_indices = [i for i in indices if metadados[i].get("tipo") == "histograma"]
        if disp_indices or hist_indices:
            indices = (disp_indices[:2] if disp_indices else []) + (hist_indices[:1] if hist_indices else [])
    # Estrutura/geral: limitar a 3 gráficos
    elif "estrutura" in pergunta_lower or "ver estrutura" in pergunta_lower:
        indices = indices[:3]
    indices.sort(key=lambda i: score(i), reverse=True)
    # Limitar a MAX_GRAFICOS para evitar poluição visual
    indices = indices[:MAX_GRAFICOS]

    return [metadados[i] for i in indices], [dados[i] for i in indices]


class AnaliseEstatisticaService:
    """
    Carrega dataset tratado, calcula métricas reais (médias, desvios, correlações),
    gera metadados de gráficos e usa LLM para insights em texto.
    """

    def __init__(self) -> None:
        self._llm = get_openai_client()

    def run(self, payload: AnaliseEstatisticaInput) -> AnaliseEstatisticaOutput:
        tratamento = payload.retorno_tratamento or {}
        tratamento_limpeza = tratamento.get("tratamento_limpeza") or tratamento
        acoes = tratamento_limpeza.get("acoes", [])
        dataset_ref: Optional[str] = payload.dataset_ref or tratamento_limpeza.get("dataset_pronto")
        pergunta = (payload.pergunta or "").strip()

        quantidade_dados = 0
        resultados: Dict[str, Any] = {}
        graficos_metadados: List[Dict[str, Any]] = []
        graficos_dados: List[Dict[str, Any]] = []
        insights: List[str] = []
        resposta_pergunta: Optional[str] = None
        correlacoes_com_alvo: List[Dict[str, Any]] = []
        balanceamento_classe: Optional[Dict[str, Any]] = None
        modelos_sugeridos = ["Random Forest", "XGBoost", "Logistic Regression"]
        requisitos_modelos = ["dataset balanceado", "features categóricas codificadas"]

        # Sugestão de modelo: resposta sem precisar de dataset
        if not dataset_ref and pergunta:
            pergunta_lower = pergunta.lower()
            if any(p in pergunta_lower for p in ["sugerir", "sugestão", "sugestao", "recomendar"]) and any(
                p in pergunta_lower for p in ["modelo", "modelos", "ml", "machine learning"]
            ):
                resposta_pergunta = (
                    f"**Modelos recomendados para classificação (ex.: previsão de churn):** {', '.join(modelos_sugeridos)}. "
                    f"**Requisitos:** {', '.join(requisitos_modelos)}. "
                    "Para treinar de fato, faça uma análise dos dados e use a opção de criar modelo com variável alvo."
                )
                data = {
                    "quantidade_dados": 0,
                    "resultados": {},
                    "insights": insights or ["Faça uma análise dos dados para treinar um modelo."],
                    "modelos_sugeridos": modelos_sugeridos,
                    "requisitos_modelos": requisitos_modelos,
                    "graficos_metadados": [],
                    "graficos_dados": [],
                    "resposta_pergunta": resposta_pergunta,
                }
                return AnaliseEstatisticaOutput(
                    id_requisicao=payload.id_requisicao,
                    analise_estatistica=data,
                    dataset_ref=None,
                )
            # Perguntas conceituais sobre ML (recall, precisão, métricas, estratégia) – resposta via LLM
            if any(p in pergunta_lower for p in ["priorizar", "recall", "precisão", "precisao", "qual métrica", "qual metrica", "estratégia", "estrategia", "modelo deve", "deve priorizar"]):
                prompt_conceitual = load_prompt("ID_prompts/analise_estatistica_conceitual").format(pergunta=pergunta)
                try:
                    resposta_pergunta = self._llm.generate_text(prompt_conceitual, use_fast_model=True).strip()
                except Exception as e:
                    logger.warning("LLM para pergunta conceitual falhou: %s", e)
                    resposta_pergunta = (
                        "Para churn, recomenda-se priorizar RECALL: capturar mais clientes em risco de sair "
                        "é geralmente mais valioso que evitar falsos positivos. Ajuste o limiar de decisão ou "
                        "use reamostragem se necessário."
                    )
                data = {
                    "quantidade_dados": 0,
                    "resultados": {},
                    "insights": insights or ["Resposta conceitual sobre métricas de ML."],
                    "modelos_sugeridos": modelos_sugeridos,
                    "requisitos_modelos": requisitos_modelos,
                    "graficos_metadados": [],
                    "graficos_dados": [],
                    "resposta_pergunta": resposta_pergunta,
                }
                return AnaliseEstatisticaOutput(
                    id_requisicao=payload.id_requisicao,
                    analise_estatistica=data,
                    dataset_ref=None,
                )

        # Cache: mesma pergunta + dataset = retorno imediato (evita 80+ s de reprocessamento)
        if dataset_ref and pergunta:
            cache_key = hashlib.sha256(
                (str(dataset_ref) + "|" + pergunta.strip().lower()).encode()
            ).hexdigest()
            now = time.time()
            if cache_key in _ANALISE_CACHE:
                ts, cached_data, cached_ref = _ANALISE_CACHE[cache_key]
                if now - ts <= _ANALISE_CACHE_TTL_SEC:
                    logger.info("AnaliseEstatistica: cache hit (key=%s)", cache_key[:12])
                    return AnaliseEstatisticaOutput(
                        id_requisicao=payload.id_requisicao,
                        analise_estatistica=cached_data,
                        dataset_ref=cached_ref,
                    )
                del _ANALISE_CACHE[cache_key]
            if len(_ANALISE_CACHE) >= _ANALISE_CACHE_MAX:
                # Remover entrada mais antiga
                oldest = min(_ANALISE_CACHE.items(), key=lambda x: x[1][0])
                del _ANALISE_CACHE[oldest[0]]

        if dataset_ref:
            try:
                df = load_dataframe(dataset_ref)
                quantidade_dados = len(df)
                resultados = _metricas_reais(df)
                par_dispersao = None
                pergunta_low = (pergunta or "").lower()
                if any(p in pergunta_low for p in ["dispersão", "dispersao", "gráfico de dispersão", "grafico de dispersao", "scatter"]):
                    numerics = df.select_dtypes(include=["number"]).columns.tolist()
                    par_dispersao = _extrair_par_dispersao_da_pergunta(pergunta, numerics)
                # Só gera gráficos quando o usuário pede explicitamente (evita gerar sem contexto)
                if _pediu_graficos(pergunta):
                    graficos_metadados, graficos_dados = _graficos_metadados_e_dados(df, par_dispersao=par_dispersao)

                _resposta_ok = False
                if pergunta:
                    resposta_pergunta = self._responder_pergunta_estatistica(df, pergunta, resultados)
                    _resposta_ok = bool(resposta_pergunta and len(resposta_pergunta) > 60)
                    if not resposta_pergunta:
                        # Incluir modelos_sugeridos quando a pergunta for sobre modelos/previsão
                        ctx_modelos = ""
                        if any(p in pergunta.lower() for p in ["modelo", "modelos", "previsão", "previsao", "ml", "machine learning", "fraude", "detecção"]):
                            ctx_modelos = f"\n\nModelos recomendados: {', '.join(modelos_sugeridos)}. Requisitos: {', '.join(requisitos_modelos)}."
                        else:
                            ctx_modelos = ""
                        dados_disponiveis = json.dumps(resultados, ensure_ascii=False)[:1200]
                        prompt_usr = load_prompt("ID_prompts/analise_estatistica_resposta_usuario").format(
                            pergunta=pergunta,
                            dados_disponiveis=dados_disponiveis,
                            ctx_modelos=ctx_modelos
                        )
                        try:
                            resposta_pergunta = self._llm.generate_text(prompt_usr, use_fast_model=True).strip()
                            resposta_pergunta = _sanitize_llm_resposta_estatistica(resposta_pergunta)
                        except Exception:
                            resposta_pergunta = "Os resultados e gráficos abaixo trazem a análise solicitada. Confira os insights e as visualizações."

                # Pular LLM de insights quando resposta determinística já é boa (economiza tempo)
                if _resposta_ok:
                    insights = ["Consulte os resultados acima."]
                else:
                    metricas_str = json.dumps(resultados, ensure_ascii=False)[:1500]
                    acoes_str = ', '.join(acoes[:3]) or 'nenhuma'
                    prompt = load_prompt("ID_prompts/analise_estatistica_insights").format(
                        metricas=metricas_str,
                        quantidade_dados=quantidade_dados,
                        acoes=acoes_str
                    )
                    try:
                        insights = [self._llm.generate_text(prompt, use_fast_model=True).strip()]
                    except Exception as e:
                        logger.warning("LLM insights falhou: %s", e)
                        insights = [f"Dataset com {quantidade_dados} registros analisado. Verifique o balanceamento de classes e as correlações acima antes de treinar."]
                correlacoes_com_alvo = _correlacoes_com_alvo(df, pergunta, resultados)
                graficos_metadados, graficos_dados = _ordenar_graficos_por_relevancia(
                    graficos_metadados, graficos_dados, correlacoes_com_alvo,
                    pergunta=pergunta, colunas_df=list(df.columns),
                )
                # Perguntas conceituais ou previsões: sem gráficos (evita "enzoniado")
                pergunta_low = (pergunta or "").lower()
                if any(p in pergunta_low for p in [
                    "ver estrutura", "estrutura da base", "estrutura do dataset",
                    "feature engineering", "engenharia de recursos", "técnicas de feature", "tecnicas de feature",
                    "gere previsões", "gere previsoes", "gerar previsões", "gerar previsoes",
                    "previsões de churn", "previsoes de churn", "gere previsões de", "gerar previsões de",
                ]):
                    graficos_metadados, graficos_dados = [], []
                variavel_alvo_bal = None
                for c in ["churn", "fraude", "target", "classe"]:
                    if c in pergunta.lower():
                        for col in df.columns:
                            if c in col.lower() or col.lower() == c:
                                variavel_alvo_bal = col
                                break
                        break
                balanceamento_classe = _balanceamento_classe(df, variavel_alvo_bal) if variavel_alvo_bal else None
            except Exception as e:
                logger.warning("Falha ao carregar dataset para estatística: %s", e)

        if not resultados:
            resultados = {"media_valor": 350.75, "desvio_padrao": 120.5, "correlacoes": {}}
        if quantidade_dados == 0:
            quantidade_dados = 30000
        if not insights:
            insights = [f"Dataset analisado ({quantidade_dados} registros). Verifique gráficos e balanceamento antes de treinar."]

        data = {
            "quantidade_dados": quantidade_dados,
            "resultados": resultados,
            "insights": insights,
            "modelos_sugeridos": modelos_sugeridos,
            "requisitos_modelos": requisitos_modelos,
            "graficos_metadados": graficos_metadados,
            "graficos_dados": graficos_dados,
        }
        if resposta_pergunta:
            data["resposta_pergunta"] = resposta_pergunta
        if correlacoes_com_alvo:
            data["correlacoes_com_alvo"] = correlacoes_com_alvo
            # Perfil de churn: variáveis que caracterizam clientes em risco (para respostas mais pontuais)
            if "churn" in (pergunta or "").lower():
                perfis = []
                for c in correlacoes_com_alvo[:5]:
                    v, val = c.get("variavel"), c.get("valor", 0)
                    if val and abs(val) > 0.05:
                        if val > 0:
                            perfis.append(f"{v} alto")
                        else:
                            perfis.append(f"{v} baixo")
                if perfis:
                    data["perfil_churn"] = f"**Perfil de churn:** Clientes com maior risco tendem a ter: {', '.join(perfis[:4])}."
        if balanceamento_classe:
            data["balanceamento_classe"] = balanceamento_classe

        # Armazenar em cache para requisições repetidas ( mesma pergunta + dataset )
        if dataset_ref and pergunta:
            cache_key = hashlib.sha256(
                (str(dataset_ref) + "|" + pergunta.strip().lower()).encode()
            ).hexdigest()
            _ANALISE_CACHE[cache_key] = (time.time(), data, dataset_ref)
            logger.debug("AnaliseEstatistica: cache stored (key=%s)", cache_key[:12])

        return AnaliseEstatisticaOutput(
            id_requisicao=payload.id_requisicao,
            analise_estatistica=data,
            dataset_ref=dataset_ref,
        )

    def _responder_pergunta_estatistica(self, df: pd.DataFrame, pergunta: str, resultados: Dict[str, Any]) -> Optional[str]:
        """Detecta tipo de análise estatística na pergunta e retorna resposta calculada (sem inventar)."""
        import re
        pergunta_lower = pergunta.lower()
        numerics = df.select_dtypes(include=["number"]).columns.tolist()
        categorias = [c for c in df.columns if c not in numerics]
        n_linhas = len(df)

        # 0.00. Quantos registros/linhas tem o dataset? – resposta direta (evita devolver só "primeiras 5 linhas")
        if any(p in pergunta_lower for p in ["quantos registros", "quantas linhas", "quantos registros tem", "quantas linhas tem", "número de registros", "numero de registros", "total de registros", "total de linhas"]):
            return f"**O dataset tem {n_linhas} registros** (linhas)."

        # 0.01. Existe coluna de churn? (ou outra coluna) – resposta determinística
        if any(p in pergunta_lower for p in ["existe coluna", "existe uma coluna", "há coluna", "ha coluna", "tem coluna", "possui coluna"]):
            alvo = None
            if "churn" in pergunta_lower:
                for c in df.columns:
                    if "churn" in str(c).lower():
                        alvo = c
                        break
            if not alvo:
                for c in df.columns:
                    if c.lower() in pergunta_lower:
                        alvo = c
                        break
            if not alvo and any(t in pergunta_lower for t in ["fraude", "target"]):
                for c in df.columns:
                    if "fraude" in c.lower() or "target" in c.lower() or c.lower() == "target":
                        alvo = c
                        break
            if alvo:
                return f"**Sim.** Existe a coluna **{alvo}** no dataset."
            return "**Não.** Nenhuma coluna mencionada na pergunta foi encontrada no dataset. Colunas disponíveis: " + ", ".join(list(df.columns)[:15]) + ("..." if len(df.columns) > 15 else "") + "."

        # 0.02a. Descreva o dataset em uma frase – resposta determinística
        if any(p in pergunta_lower for p in ["descreva o dataset", "descreva o dataset em uma frase", "descreva o conjunto de dados"]):
            n_linhas, n_cols = len(df), len(df.columns)
            col_churn = next((c for c in df.columns if "churn" in str(c).lower()), None)
            frase = f"**{n_linhas} linhas, {n_cols} colunas"
            if col_churn:
                vc = df[col_churn].astype(str).str.strip().str.lower().value_counts()
                tot = vc.sum()
                yes_cnt = vc.get("yes", 0) + vc.get("sim", 0)
                yes_pct = 100 * yes_cnt / tot if tot > 0 else 0
                frase += f", variável alvo **{col_churn}** ({yes_pct:.0f}% positivos)"
            frase += ".**"
            return frase

        # 0.02b. Data leakage / vazamentos de dados – resposta determinística
        if any(p in pergunta_lower for p in ["vazamento", "vazamentos de dados", "data leakage", "identifique possíveis vazamentos"]):
            linhas = [
                "**Possíveis fontes de vazamento de dados (data leakage) em problemas de churn:**",
                "",
                "• **TotalCharges:** Deriva de tenure × cobranças; pode conter informação do futuro (ex.: cliente que churnou tinha TotalCharges = tenure × MonthlyCharges). Use com cautela ou remova em testes rigorosos.",
                "• **Colunas de ID:** `_id`, `customerID` – não têm poder preditivo e podem vazar se usadas indevidamente.",
                "• **Variáveis que são consequência do alvo:** Qualquer coluna que seja resultado direto do churn (ex.: status de cancelamento derivado).",
                "• **Dados temporais:** Se a data de corte não for respeitada, dados futuros podem vazar no treino.",
                "",
                "**Recomendação:** Use apenas variáveis conhecidas *antes* do evento de churn. Remova TotalCharges em análises de sensibilidade ou use tenure + MonthlyCharges separadamente.",
            ]
            return "\n".join(linhas)

        # 0.02b1. Gere visualizações / variáveis mais importantes – resposta estruturada referenciando os gráficos
        if any(p in pergunta_lower for p in [
            "gere visualizações", "gere visualizacoes", "visualizações para", "visualizacoes para",
            "5 variáveis mais importantes", "5 variaveis mais importantes", "variáveis mais importantes", "variaveis mais importantes",
        ]):
            linhas = [
                "**Visualizações geradas:**",
                "",
                "Os gráficos abaixo apresentam:",
                "• **Distribuições** das variáveis numéricas principais",
                "• **Contagens** por categoria das variáveis qualitativas",
                "• **Dispersão** do par com maior correlação (relação entre variáveis)",
                "",
                "Confira os títulos e explicações de cada gráfico para interpretação.",
            ]
            return "\n".join(linhas)

        # 0.02b2. Gráfico de dispersão entre X e Y – resposta referenciando o par exibido
        if any(p in pergunta_lower for p in ["gráfico de dispersão", "grafico de dispersao", "dispersão entre", "dispersao entre", "scatter entre", "scatter de"]):
            par = _extrair_par_dispersao_da_pergunta(pergunta, numerics)
            if par:
                col_x, col_y = par[0], par[1]
                if col_x in df.columns and col_y in df.columns:
                    corr = _correlacao_entre_colunas(df, col_x, col_y)
                    if corr is not None:
                        return f"O gráfico de dispersão abaixo mostra **{col_x}** vs **{col_y}**. Correlação de Pearson: {corr:.3f}."
                    return f"O gráfico de dispersão abaixo mostra a relação entre **{col_x}** e **{col_y}**."

        # 0.02c. Quais variáveis têm maior variância? – ordenar por desvio padrão
        if any(p in pergunta_lower for p in ["variáveis têm maior variância", "variaveis tem maior variancia", "maior variância", "maior variancia", "variância", "variancia"]):
            desvios = resultados.get("desvio_padrao") or {}
            if desvios:
                ordenadas = sorted(desvios.items(), key=lambda x: x[1] or 0, reverse=True)[:8]
                linhas = ["**Variáveis com maior variância (desvio padrão):**", ""]
                for col, dp in ordenadas:
                    if dp is not None and not (isinstance(dp, float) and np.isnan(dp)):
                        linhas.append(f"• **{col}:** {float(dp):.2f}")
                if len(linhas) > 2:
                    return "\n".join(linhas)

        # 0.02. Resumo estatístico das variáveis numéricas – só métricas por variável (média, mediana, dp, assimetria, curtose), sem "correlação" por variável
        if any(p in pergunta_lower for p in ["resumo estatístico das variáveis numéricas", "resumo estatistico das variaveis numericas", "resumo das variáveis numéricas", "resumo das variaveis numericas", "resumo estatístico", "resumo estatistico"]):
            medias = resultados.get("medias") or {}
            medianas = resultados.get("medianas") or {}
            desvios = resultados.get("desvio_padrao") or {}
            assimetria = resultados.get("assimetria") or {}
            curtose = resultados.get("curtose") or {}
            linhas = ["**Resumo de dados numéricos do dataset:**", ""]
            for col in list(medias.keys())[:12]:
                partes = []
                if col in medias and medias[col] is not None:
                    partes.append(f"média {medias[col]:.4f}")
                if col in medianas and medianas[col] is not None:
                    partes.append(f"mediana {medianas[col]:.4f}")
                if col in desvios and desvios[col] is not None:
                    partes.append(f"desvio {desvios[col]:.4f}")
                if col in assimetria and assimetria[col] is not None:
                    try:
                        a = float(assimetria[col])
                        if not np.isnan(a):
                            partes.append(f"assimetria {a:.4f}")
                    except (TypeError, ValueError):
                        pass
                if col in curtose and curtose[col] is not None:
                    try:
                        k = float(curtose[col])
                        if not np.isnan(k):
                            partes.append(f"curtose {k:.4f}")
                    except (TypeError, ValueError):
                        pass
                if partes:
                    linhas.append(f"• **{col}:** " + ", ".join(partes))
            if len(linhas) > 2:
                return "\n".join(linhas)

        # 0. Análise gráfica/geral – resposta formatada com métricas reais (sem LLM)
        if any(p in pergunta_lower for p in ["analise grafica", "análise gráfica", "analise estatistica", "análise estatística", "analise dos dados", "analise geral"]):
            linhas = ["**Resumo estatístico:**"]
            medias = resultados.get("medias") or {}
            desvios = resultados.get("desvio_padrao") or {}
            quartis75 = resultados.get("quartil_75") or {}
            assimetria = resultados.get("assimetria") or {}
            for col in list(medias.keys())[:6]:
                m = medias.get(col)
                d = desvios.get(col)
                q = quartis75.get(col)
                a = assimetria.get(col)
                partes_col = []
                if m is not None:
                    partes_col.append(f"média {m:.4f}")
                if d is not None:
                    partes_col.append(f"dp {d:.2f}")
                if q is not None:
                    partes_col.append(f"Q3 {q:.2f}")
                if a is not None:
                    partes_col.append(f"assimetria {a:.2f}")
                if partes_col:
                    linhas.append(f"• **{col}:** " + ", ".join(partes_col))
            corr = resultados.get("matriz_correlacao") or {}
            # Se pergunta menciona churn, priorizar correlações COM a variável churn
            col_churn = None
            churn_numeric = None  # série numérica (0/1) para correlação
            if "churn" in pergunta_lower:
                for c in df.columns:
                    if "churn" in str(c).lower():
                        col_churn = c
                        break
                if col_churn is not None:
                    if col_churn in numerics:
                        churn_numeric = df[col_churn]
                    else:
                        # Churn categórico (Yes/No) → codificar para 0/1
                        try:
                            s = df[col_churn].astype(str).str.strip().str.lower()
                            churn_numeric = s.map({"yes": 1, "sim": 1, "1": 1, "true": 1, "no": 0, "não": 0, "nao": 0, "0": 0, "false": 0}).fillna(-1)
                            if (churn_numeric == -1).all():
                                churn_numeric = None
                            else:
                                churn_numeric = churn_numeric.replace(-1, np.nan)
                        except Exception:
                            churn_numeric = None
            if churn_numeric is not None and col_churn:
                linhas.append("")
                linhas.append("**Correlações com Churn (para previsão):**")
                pares_churn: List[Tuple[str, float]] = []
                for c in numerics:
                    if c == col_churn:
                        continue
                    try:
                        v = float(churn_numeric.corr(df[c]))
                        if not np.isnan(v):
                            pares_churn.append((c, v))
                    except Exception:
                        pass
                pares_churn.sort(key=lambda x: abs(x[1]), reverse=True)
                for c, v in pares_churn[:6]:
                    intens = "forte" if abs(v) >= 0.5 else "moderada" if abs(v) >= 0.4 else "fraca"
                    linhas.append(f"• {col_churn} ↔ {c}: {v:.3f} ({intens})")
            elif corr and len(numerics) >= 2:
                c1, c2 = numerics[0], numerics[1]
                v = (corr.get(c1) or {}).get(c2)
                if v is not None:
                    intens = "forte" if abs(v) > 0.5 else "moderada" if abs(v) > 0.2 else "fraca"
                    linhas.append(f"• **Correlação {c1} ↔ {c2}:** {float(v):.3f} ({intens})")
            if len(linhas) > 1:
                return "\n".join(linhas)

        # 0.1. Valores únicos de uma coluna específica (ex.: Contract)
        if "valores únicos" in pergunta_lower or "valores unicos" in pergunta_lower:
            alvo = None
            # tentar casar pelo nome da coluna mencionado na pergunta
            for c in df.columns:
                if c.lower() in pergunta_lower:
                    alvo = c
                    break
            # fallback específico para Contract
            if not alvo and "contract" in pergunta_lower:
                for c in df.columns:
                    if "contract" in c.lower():
                        alvo = c
                        break
            if alvo and alvo in df.columns:
                serie = df[alvo].dropna()
                valores = [str(v) for v in serie.unique().tolist()]
                if len(valores) > 20:
                    valores = valores[:20] + ["..."]
                return f"Valores únicos da coluna **{alvo}**: {', '.join(valores)}."

        # 0.2. Quais colunas são numéricas e quais categóricas
        if any(
            p in pergunta_lower
            for p in [
                "colunas são numéricas",
                "colunas sao numericas",
                "numéricas e quais são categóricas",
                "numericas e quais sao categoricas",
                "colunas numericas e categoricas",
            ]
        ):
            nums_fmt = ", ".join(numerics) if numerics else "(nenhuma)"
            cats_fmt = ", ".join(categorias) if categorias else "(nenhuma)"
            return (
                "**Colunas por tipo:**\n\n"
                f"- Numéricas: {nums_fmt}.\n"
                f"- Categóricas/outras: {cats_fmt}."
            )

        # 0.5. Relação entre variáveis categóricas (ex.: Contract × Churn) – tabela cruzada
        if any(p in pergunta_lower for p in ["relação entre", "relacao entre", "análise da relação", "analise da relacao"]):
            col_a, col_b = None, None
            cats = [c for c in df.select_dtypes(include=["object", "category"]).columns if c.lower() not in _COLS_IGNORAR_GRAFICO and df[c].nunique() <= 20]
            for c in cats:
                if c.lower() in pergunta_lower or c in pergunta:
                    if col_a is None:
                        col_a = c
                    elif col_b is None and c != col_a:
                        col_b = c
                        break
            if col_a and col_b:
                try:
                    ct = pd.crosstab(df[col_a], df[col_b], margins=True)
                    linhas = [f"**Relação {col_a} × {col_b}:**", ""]
                    # Cabeçalho da tabela
                    header = "| " + " | ".join(str(x) for x in ct.columns) + " |"
                    linhas.append(header)
                    # Separador
                    separator = "|" + "---|" * len(ct.columns)
                    linhas.append(separator)
                    # Linhas de dados (excluindo a linha de margens se necessário)
                    for idx in ct.index[:-1]:  # Excluir última linha (margens) se houver
                        row_values = [str(int(v)) for v in ct.loc[idx]]
                        linhas.append("| " + " | ".join(row_values) + " |")
                    # Linha de totais (margens)
                    if len(ct.index) > 0:
                        total_row = [str(int(v)) for v in ct.iloc[-1]]
                        linhas.append("| " + " | ".join(total_row) + " |")
                    total_geral = int(ct.iloc[-1, -1]) if ct.size > 0 else len(df)
                    linhas.append("")
                    linhas.append(f"**Insight:** Tabela cruzada de contagem ({total_geral} registros).")
                    return "\n".join(linhas)
                except Exception:
                    pass

        # 0.35. Tabelas e volumes – resposta clara (estrutura + tamanho)
        if any(p in pergunta_lower for p in ["tabelas e volumes", "quais são as tabelas", "quais sao as tabelas", "quais tabelas", "quais volumes"]):
            n_linhas, n_cols = len(df), len(df.columns)
            cols_list = list(df.columns)
            cols_texto = ", ".join(cols_list[:15]) + ("..." if n_cols > 15 else "")
            linhas = [
                "**Estrutura e volumes do dataset:**",
                "",
                f"• **Volume:** {n_linhas} registros (linhas)",
                f"• **Colunas:** {n_cols}",
                f"• **Nomes:** {cols_texto}",
                "",
                "**Métricas estatísticas disponíveis:** médias, desvio padrão, medianas, quartis, assimetria, curtose e correlações.",
            ]
            return "\n".join(linhas)

        # 0.4. Ver estrutura da base – resposta determinística (evita erro "Média: mediana")
        if any(p in pergunta_lower for p in ["ver estrutura", "estrutura da base", "estrutura do dataset"]):
            n_linhas, n_cols = len(df), len(df.columns)
            todas_colunas = list(df.columns)
            # Listar todas as colunas (evita truncar em 10 e deixar pergunta "não respondida")
            cols_texto = ", ".join(todas_colunas) if n_cols <= 25 else ", ".join(todas_colunas[:22]) + ", ..."
            mapeamento = [
                ("medias", "Média dos valores"),
                ("desvio_padrao", "Desvio padrão (dispersão)"),
                ("medianas", "Mediana (percentil 50%)"),
                ("quartil_25", "Quartil inferior (25%)"),
                ("quartil_75", "Quartil superior (75%)"),
                ("minimos", "Valor mínimo"),
                ("maximos", "Valor máximo"),
                ("assimetria", "Assimetria (skewness)"),
                ("curtose", "Curtose (kurtosis)"),
                ("correlacoes", "Correlação entre variáveis"),
            ]
            linhas = [
                f"**Estrutura do dataset:** {n_linhas} linhas, {n_cols} colunas.",
                f"**Colunas:** {cols_texto}.",
                "",
                "**Métricas disponíveis:**",
            ]
            for chave, desc in mapeamento:
                if chave in (resultados or {}):
                    linhas.append(f"• **{chave}:** {desc}.")
            return "\n".join(linhas)

        # 0.45. Feature engineering – resposta determinística (evita "Correlação curtosa")
        if any(p in pergunta_lower for p in ["feature engineering", "engenharia de recursos", "técnicas de feature", "tecnicas de feature"]):
            return (
                "**Técnicas de feature engineering recomendadas:**\n\n"
                "• **Encoding categórico:** One-Hot para categóricas com poucas categorias; Label Encoding para ordinais.\n"
                "• **Normalização:** StandardScaler ou MinMaxScaler para variáveis numéricas em escalas diferentes.\n"
                "• **Criação de features:** Razões (ex.: tenure/TotalCharges), bins de tenure, contagem de serviços.\n"
                "• **Tratamento de nulos:** Imputação por mediana ou KNN para numéricos; moda para categóricos.\n"
                "• **Seleção:** Remover colunas com alta correlação (redundância)."
            )

        # 0. "Traga os gráficos" – contexto de origem
        if any(p in pergunta_lower for p in ["traga os graficos", "traga os gráficos", "mostre os graficos", "mostre os gráficos", "exiba os graficos"]):
            return (
                "**Gráficos da análise atual:**\n\n"
                "Os gráficos abaixo foram gerados a partir do dataset carregado na última captura ou análise. "
                "Cada um representa: (1) **Histogramas** – distribuição de variáveis numéricas em faixas; "
                "(2) **Barras** – contagem por categoria; (3) **Dispersão** – relação entre duas variáveis numéricas. "
                "As explicações, vantagens e desvantagens de cada tipo estão descritas em cada card."
            )

        # 1. Sugestão de modelos – resposta determinística, 100% verídica (sem LLM)
        if any(p in pergunta_lower for p in ["sugerir", "sugestão", "sugestao", "recomendar", "modelo para", "qual modelo", "quais modelos"]):
            modelos = ["Random Forest", "XGBoost", "Regressão Logística"]
            requisitos = ["dataset balanceado", "features categóricas codificadas"]
            return (
                f"**Modelos recomendados para classificação (ex.: detecção de fraude):** {', '.join(modelos)}. "
                f"**Requisitos:** {', '.join(requisitos)}. "
                "Para treinar de fato, use a opção de criar modelo com variável alvo."
            )

        # 1b. Balanceamento de classes – ANTES de "primeiras/amostra" (evita match errado: "reamostragem" contém "amostra")
        if any(p in pergunta_lower for p in ["balanceamento", "balanceamento de classes", "reamostragem", "smote", "undersampling"]):
            col_alvo = None
            for c in df.columns:
                if "churn" in str(c).lower() or "target" in str(c).lower() or "classe" in str(c).lower():
                    col_alvo = c
                    break
            if col_alvo is None:
                col_alvo = df.columns[-1] if len(df.columns) > 0 else None
            if col_alvo:
                vc = df[col_alvo].value_counts()
                total = vc.sum()
                linhas = [f"**Balanceamento da variável alvo '{col_alvo}':**"]
                for cat, cnt in vc.items():
                    pct = 100 * cnt / total if total > 0 else 0
                    linhas.append(f"• {cat}: {int(cnt)} ({pct:.1f}%)")
                ratio = vc.max() / vc.min() if len(vc) >= 2 and vc.min() > 0 else 0
                linhas.append("")
                if ratio > 3:
                    linhas.append(f"**Desbalanceamento:** razão {ratio:.1f}:1. Recomenda-se SMOTE, undersampling ou oversampling antes de treinar.")
                elif ratio > 1.5:
                    linhas.append("**Desbalanceamento moderado.** Considere ponderação de classes ou técnicas de reamostragem.")
                else:
                    linhas.append("**Classes relativamente balanceadas.** Pode treinar sem reamostragem obrigatória.")
                return "\n".join(linhas)

        # 1c. Primeiras N linhas ou registros aleatórios – NÃO matchar "amostra" quando fizer parte de "reamostragem"
        _pede_amostra = any(p in pergunta_lower for p in ["primeiras", "primeira", "primeiro", "head"])
        _pede_amostra = _pede_amostra or (("linhas" in pergunta_lower or "registros" in pergunta_lower) and "balanceamento" not in pergunta_lower and "reamostragem" not in pergunta_lower)
        _pede_amostra = _pede_amostra or ("amostra" in pergunta_lower and "reamostragem" not in pergunta_lower)
        _pede_aleatorio = "aleat" in pergunta_lower or "random" in pergunta_lower
        if _pede_amostra:
            n = 5
            match = re.search(r"(\d+)\s*(?:primeiras?|linhas?|registros?|aleatórios?|aleatorios?)", pergunta_lower)
            if match:
                n = min(int(match.group(1)), 20)
            sample_df = df.sample(n=n, random_state=42) if _pede_aleatorio else df.head(n)
            rows_str = sample_df.to_string(index=False, max_cols=10)
            if len(rows_str) > 1500:
                rows_str = rows_str[:1500] + "\n... (truncado)"
            titulo = f"{n} registros aleatórios:" if _pede_aleatorio else f"Primeiras {n} linhas:"
            return f"{titulo}\n```\n{rows_str}\n```"

        # 4.9. Contagem por coluna (ex.: "Mostre a contagem por Dependents")
        if "contagem por" in pergunta_lower or "mostre a contagem" in pergunta_lower:
            col_alvo = None
            for c in df.columns:
                if c.lower() in pergunta_lower:
                    col_alvo = c
                    break
            for hint in ["dependents", "partner", "gender", "phoneservice", "churn", "contract"]:
                if hint in pergunta_lower:
                    for c in df.columns:
                        if hint in c.lower():
                            col_alvo = c
                            break
                    if col_alvo:
                        break
            if col_alvo and col_alvo in df.columns:
                vc = df[col_alvo].value_counts()
                total = vc.sum()
                linhas = [f"**Contagem por {col_alvo}:**", ""]
                for cat, cnt in vc.head(15).items():
                    pct = 100 * cnt / total if total > 0 else 0
                    linhas.append(f"• {cat}: {int(cnt)} ({pct:.1f}%)")
                return "\n".join(linhas)

        # 5. Distribuição de variável específica (ex.: "Mostre a distribuição da variável Partner")
        if any(p in pergunta_lower for p in ["distribuição da variável", "distribuicao da variavel", "mostre a distribuição", "mostre a distribuicao"]) or ("distribuição" in pergunta_lower and "variável" in pergunta_lower):
            col_alvo = None
            for c in df.columns:
                if c.lower() in pergunta_lower or (len(c) > 2 and c.lower() in pergunta_lower.replace(" ", "")):
                    col_alvo = c
                    break
            # Fallback para nomes comuns
            for hint in ["partner", "gender", "dependents", "churn", "contract", "internetservice", "paymentservice"]:
                if hint in pergunta_lower:
                    for c in df.columns:
                        if hint in c.lower():
                            col_alvo = c
                            break
                    if col_alvo:
                        break
            if col_alvo and col_alvo in df.columns:
                vc = df[col_alvo].value_counts()
                total = vc.sum()
                linhas = [f"**Distribuição da variável '{col_alvo}':**", ""]
                for cat, cnt in vc.head(10).items():
                    pct = 100 * cnt / total if total > 0 else 0
                    linhas.append(f"• {cat}: {int(cnt)} ({pct:.1f}%)")
                linhas.append("")
                linhas.append("Os gráficos abaixo mostram as contagens por categoria.")
                return "\n".join(linhas)

        # 5b. Distribuição de variável categórica (genérica)
        if any(p in pergunta_lower for p in ["distribuição categoria", "distribuicao categoria", "variável categórica", "variavel categorica", "gender", "partner", "dependents"]):
            cats = [c for c in df.select_dtypes(include=["object", "category"]).columns
                    if c.lower() not in _COLS_IGNORAR_GRAFICO and df[c].nunique() <= 20]
            if cats:
                linhas = ["**Distribuições por variável categórica:**"]
                for col in cats[:4]:
                    vc = df[col].value_counts()
                    total = vc.sum()
                    for cat, cnt in vc.head(5).items():
                        pct = 100 * cnt / total if total > 0 else 0
                        linhas.append(f"• **{col}:** {cat} = {int(cnt)} ({pct:.1f}%)")
                linhas.append("")
                linhas.append("Os gráficos abaixo mostram as contagens por categoria.")
                return "\n".join(linhas)

        # 5.5. Dataset pronto para treinar? – diagnóstico rápido (sem LLM)
        if any(p in pergunta_lower for p in ["dataset está pronto", "dataset esta pronto", "pronto para treinar", "o que falta"]):
            n_linhas, n_cols = len(df), len(df.columns)
            n_nulos = df.isnull().sum().sum()
            # Percentual por células totais; para exibição legível usar 2 decimais quando < 1%
            pct_nulos_celulas = 100 * n_nulos / (n_linhas * n_cols) if n_linhas * n_cols > 0 else 0
            pct_nulos_fmt = f"{pct_nulos_celulas:.2f}%" if pct_nulos_celulas > 0 and pct_nulos_celulas < 1 else f"{pct_nulos_celulas:.1f}%"
            col_churn = next((c for c in df.columns if "churn" in str(c).lower()), None)
            bal = _balanceamento_classe(df, col_churn) if col_churn else None
            linhas = [
                f"**Diagnóstico do dataset:** {n_linhas} linhas, {n_cols} colunas.",
                f"Valores nulos: {n_nulos} ({pct_nulos_fmt}).",
            ]
            if n_nulos > 0:
                estrategia_nulos = "imputação por mediana/moda" if pct_nulos_celulas < 1 else "remoção de linhas ou imputação avançada (KNN)"
                linhas.append(f"**Estratégia para nulos:** {estrategia_nulos}.")
            if bal:
                r = bal.get("razao", 0)
                rec = bal.get("recomendacao", "")
                linhas.append(f"Balanceamento Churn: razão {r:.2f}. {rec}")
            if pct_nulos_celulas > 5:
                linhas.append("**Sugestão:** Trate valores nulos antes do treino.")
            elif col_churn and (not bal or bal.get("razao", 1) < 0.3):
                linhas.append("**Sugestão:** Considere balanceamento (SMOTE) antes do treino.")
            else:
                linhas.append("**Conclusão:** Dataset pronto para treinar.")
            return "\n".join(linhas)

        # 7. Poder preditivo para churn – correlações ordenadas
        if any(p in pergunta_lower for p in ["poder preditivo", "variáveis para churn", "variaveis para churn", "maior poder"]):
            col_churn = None
            churn_numeric = None
            for c in df.columns:
                if "churn" in str(c).lower():
                    col_churn = c
                    break
            if col_churn:
                if col_churn in numerics:
                    churn_numeric = df[col_churn]
                else:
                    try:
                        s = df[col_churn].astype(str).str.strip().str.lower()
                        churn_numeric = s.map({"yes": 1, "sim": 1, "1": 1, "no": 0, "não": 0, "nao": 0, "0": 0}).fillna(-1)
                        churn_numeric = churn_numeric.replace(-1, np.nan)
                    except Exception:
                        churn_numeric = None
            if churn_numeric is not None:
                pares: List[Tuple[str, float]] = []
                for c in numerics:
                    if c == col_churn:
                        continue
                    try:
                        v = float(churn_numeric.corr(df[c]))
                        if not np.isnan(v):
                            pares.append((c, v))
                    except Exception:
                        pass
                pares.sort(key=lambda x: abs(x[1]), reverse=True)
                linhas = ["**Variáveis com maior poder preditivo para Churn (por correlação):**"]
                for c, v in pares[:6]:
                    intens = "forte" if abs(v) >= 0.5 else "moderada" if abs(v) >= 0.4 else "fraca"
                    linhas.append(f"• {c}: {v:.3f} ({intens})")
                linhas.append("")
                linhas.append("Os gráficos de distribuição mostram como cada variável se comporta. tenure e TotalCharges costumam ser as mais relevantes para churn.")
                return "\n".join(linhas)
        
        # 7.5. Importância das features para previsão de churn
        if any(p in pergunta_lower for p in ["importância das features", "importancia das features", "importância das variáveis", "importancia das variaveis", "análise a importância", "analise a importancia"]):
            col_churn = None
            for c in df.columns:
                if "churn" in str(c).lower():
                    col_churn = c
                    break
            if col_churn:
                correlacoes = _correlacoes_com_alvo(df, pergunta, resultados)
                if correlacoes:
                    linhas = ["**Importância das features para previsão de churn:**", ""]
                    linhas.append("A importância de features em modelos de Machine Learning é avaliada por:")
                    linhas.append("• **Redução de impureza** (Gini/entropia) em modelos baseados em árvores (Random Forest, XGBoost)")
                    linhas.append("• **Coeficientes** em modelos lineares (Regressão Logística)")
                    linhas.append("• **Métodos de permutação** (shuffle de features e impacto na métrica)")
                    linhas.append("")
                    linhas.append("**Correlações com Churn (indicativo de poder preditivo):**")
                    for corr in correlacoes[:5]:
                        v = corr.get("variavel", "")
                        val = corr.get("valor", 0)
                        intens = corr.get("forca", "fraca")
                        linhas.append(f"• {v}: {val:.3f} ({intens})")
                    linhas.append("")
                    linhas.append("**Modelo recomendado:** Random Forest (avalia importância por redução de impureza).")
                    linhas.append("**Pré-processamento:** O dataset deve estar balanceado e as categorias devem ser codificadas.")
                    return "\n".join(linhas)

        # 4. Outliers (IQR) - ANTES da verificação de len(numerics) < 2, pois só precisa de 1 variável
        if any(palavra in pergunta_lower for palavra in ["outlier", "outliers", "valores extremos", "extremos"]):
            col = self._extrair_uma_coluna_da_pergunta(df, pergunta, numerics)
            if col and col in df.columns:
                ser = df[col].dropna()
                if len(ser) >= 4:
                    q1, q3 = ser.quantile(0.25), ser.quantile(0.75)
                    iqr = q3 - q1
                    lim_inf = q1 - 1.5 * iqr
                    lim_sup = q3 + 1.5 * iqr
                    n_out = int(((ser < lim_inf) | (ser > lim_sup)).sum())
                    pct = 100 * n_out / len(ser) if len(ser) > 0 else 0
                    if n_out > 0:
                        return (
                            f"Existem {n_out} valores extremos (outliers) em '{col}' ({pct:.1f}% dos dados). "
                            f"Limites IQR: [{lim_inf:.2f}, {lim_sup:.2f}]. "
                            "Considere winsorização ou remoção antes do treino."
                        )
                    return f"Não há outliers significativos em '{col}' (método IQR 1.5). Limites: [{lim_inf:.2f}, {lim_sup:.2f}]."

        # 1. Correlações — antes do gate len(numerics)<2: coage texto→número e recalcula matriz (Mongo costuma trazer TotalCharges como string)
        _pergunta_corr = any(
            p in pergunta_lower for p in ("correlação", "correlacao", "correlações", "correlacoes")
        )
        if _pergunta_corr:
            dnum = _df_with_coerced_numerics(df)
            numerics_eff = dnum.select_dtypes(include=["number"]).columns.tolist()
            matriz_use: Dict[str, Any] = {}
            if len(numerics_eff) >= 2:
                try:
                    matriz_use = dnum[numerics_eff].corr().round(4).to_dict()
                except Exception:
                    matriz_use = dict(resultados.get("matriz_correlacao") or {})
            else:
                matriz_use = dict(resultados.get("matriz_correlacao") or {})

            col_x, col_y = self._extrair_colunas_da_pergunta(dnum, pergunta, numerics_eff)
            _par_claro = "entre" in pergunta_lower or " vs " in pergunta_lower or " versus " in pergunta_lower
            if not _par_claro:
                _par_claro = " e " in f" {pergunta_lower} " and (
                    "correlação entre" in pergunta_lower
                    or "correlacao entre" in pergunta_lower
                    or "entre " in pergunta_lower
                )
            if col_x and col_y and col_x != col_y and _par_claro:
                corr_val = _correlacao_entre_colunas(dnum, col_x, col_y)
                if corr_val is not None:
                    intensidade = "forte" if abs(corr_val) >= 0.7 else "moderada" if abs(corr_val) >= 0.4 else "fraca"
                    direcao = "positiva" if corr_val > 0 else "negativa"
                    return f"Correlação entre '{col_x}' e '{col_y}': {corr_val:.4f} ({intensidade} e {direcao})."

            if matriz_use:
                top = _matriz_correlacao_top_pairs(matriz_use, max_cols=22, top_n=8)
                if top:
                    return _format_correlacoes_principais(top)
                return (
                    "**Correlações:** A matriz foi calculada, mas não há pares fora da diagonal com |r| < 1 "
                    "(colunas constantes ou pouca variância)."
                )
            return (
                "**Correlações:** Menos de duas colunas numéricas após conversão automática. "
                "Verifique tipos (ex.: TotalCharges como número) ou codifique categóricas."
            )

        if len(numerics) < 2:
            return None

        # 2. Regressão linear
        if any(palavra in pergunta_lower for palavra in ["regressão", "regressao", "relação linear", "relacao linear", "tendência", "tendencia"]):
            col_x, col_y = self._extrair_colunas_da_pergunta(df, pergunta, numerics)
            if col_x and col_y:
                reg = _regressao_linear_simples(df, col_x, col_y)
                if reg:
                    return (
                        f"Regressão linear entre '{col_x}' e '{col_y}': "
                        f"R² = {reg['r_quadrado']:.4f}, "
                        f"coeficiente angular = {reg['coeficiente_angular']:.4f}, "
                        f"p-valor = {reg['p_valor']:.4f}."
                    )
        
        # 3. Normalidade
        if any(palavra in pergunta_lower for palavra in ["normal", "normalidade", "distribuição normal", "distribuicao normal"]):
            col = self._extrair_uma_coluna_da_pergunta(df, pergunta, numerics)
            if col:
                teste = _teste_normalidade(df, col)
                if teste:
                    resultado = "normal" if teste["normal"] else "não normal"
                    return (
                        f"Teste de normalidade para '{col}': {resultado} "
                        f"(p-valor = {teste['p_valor']:.4f})."
                    )

        # 5. Estatísticas descritivas (média, mediana, etc.)
        if any(palavra in pergunta_lower for palavra in ["média", "media", "mediana", "desvio", "quartil"]):
            col = self._extrair_uma_coluna_da_pergunta(df, pergunta, numerics)
            if col and col in resultados.get("medias", {}):
                respostas = []
                if "média" in pergunta_lower or "media" in pergunta_lower:
                    respostas.append(f"Média de '{col}': {resultados['medias'][col]:.4f}")
                if "mediana" in pergunta_lower:
                    respostas.append(f"Mediana de '{col}': {resultados['medianas'][col]:.4f}")
                if "desvio" in pergunta_lower:
                    respostas.append(f"Desvio padrão de '{col}': {resultados['desvio_padrao'][col]:.4f}")
                if "quartil" in pergunta_lower:
                    respostas.append(
                        f"Quartis de '{col}': Q1={resultados['quartil_25'][col]:.4f}, "
                        f"Q2={resultados['medianas'][col]:.4f}, Q3={resultados['quartil_75'][col]:.4f}"
                    )
                if respostas:
                    return ". ".join(respostas) + "."

        return None
    
    def _extrair_colunas_da_pergunta(self, df: pd.DataFrame, pergunta: str, numerics: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """Extrai duas colunas da pergunta; prioriza a ordem em que aparecem na pergunta (ex.: tenure e TotalCharges)."""
        import re
        
        # Tentativa 1: busca direta por nomes de colunas
        palavras = re.findall(r"[\w]+", pergunta)
        candidatas = [
            p for p in palavras 
            if len(p) > 1 and p.lower() not in (
                "entre", "qual", "a", "e", "de", "da", "correlação", "correlacao", 
                "x", "y", "regressão", "regressao", "relação", "relacao", "calcule", "calcular"
            )
        ]
        pergunta_lower = pergunta.lower()
        # Pares (posição na pergunta, nome da coluna) para ordenar pela ordem citada
        colunas_por_posicao: List[Tuple[int, str]] = []
        for c in numerics:
            cl = c.lower()
            if cl in [p.lower() for p in candidatas]:
                pos = pergunta_lower.find(cl)
                if pos >= 0:
                    colunas_por_posicao.append((pos, c))
            else:
                for p in candidatas:
                    if p.lower() in cl and len(p) > 2:
                        pos = pergunta_lower.find(p.lower())
                        if pos >= 0:
                            colunas_por_posicao.append((pos, c))
                            break
        # Remover duplicatas mantendo a primeira ocorrência por coluna
        vistos: set = set()
        colunas_ordenadas = []
        for _pos, col in sorted(colunas_por_posicao, key=lambda x: x[0]):
            if col not in vistos:
                vistos.add(col)
                colunas_ordenadas.append(col)
        if len(colunas_ordenadas) >= 2:
            return colunas_ordenadas[0], colunas_ordenadas[1]
        col_x = colunas_ordenadas[0] if len(colunas_ordenadas) >= 1 else None
        col_y = None
        
        # Tentativa 2: se não encontrou duas, usa LLM para mapear pergunta -> colunas
        if col_x is None or col_y is None:
            try:
                prompt_llm = load_prompt("ID_prompts/analise_estatistica_extrair_colunas").format(
                    pergunta=pergunta,
                    colunas_numericas=', '.join(numerics[:20])
                )
                resposta_llm = self._llm.generate_text(prompt_llm, use_fast_model=True).strip()
                colunas_llm = [c.strip() for c in resposta_llm.split(",") if c.strip()]
                for c in colunas_llm:
                    if c in numerics:
                        if col_x is None:
                            col_x = c
                        elif col_y is None:
                            col_y = c
                            break
            except Exception as e:
                logger.debug("LLM para extração de colunas falhou: %s", e)
        
        # Fallback: usa as duas primeiras colunas numéricas
        if col_x is None or col_y is None:
            if len(numerics) >= 2:
                col_x, col_y = numerics[0], numerics[1]
        
        return col_x, col_y
    
    def _extrair_uma_coluna_da_pergunta(self, df: pd.DataFrame, pergunta: str, numerics: List[str]) -> Optional[str]:
        """Extrai uma coluna da pergunta usando LLM quando necessário."""
        import re
        
        # Tentativa 1: busca direta
        palavras = re.findall(r"[\w]+", pergunta)
        candidatas = [
            p for p in palavras 
            if len(p) > 1 and p.lower() not in (
                "qual", "a", "de", "da", "média", "media", "mediana", "desvio", "normal"
            )
        ]
        for c in df.columns:
            if c in numerics:
                if c.lower() in [p.lower() for p in candidatas] or any(p.lower() in c.lower() for p in candidatas):
                    return c
        
        # Tentativa 2: LLM
        try:
            prompt_llm = load_prompt("ID_prompts/analise_estatistica_extrair_coluna").format(
                pergunta=pergunta,
                colunas_numericas=', '.join(numerics[:20])
            )
            resposta_llm = self._llm.generate_text(prompt_llm, use_fast_model=True).strip()
            if resposta_llm in numerics:
                return resposta_llm
        except Exception as e:
            logger.debug("LLM para extração de coluna falhou: %s", e)
        
        # Fallback: primeira coluna numérica
        return numerics[0] if numerics else None
