# -*- coding: utf-8 -*-
"""
Pulso Finance — Controle de receita (planos), custo de operação e lucro.
Receita = sempre pelo plano do usuário. Gastos = custo de operação (controle total).
"""
from pathlib import Path
import streamlit as st
import pandas as pd
from datetime import datetime

# ─── Configuração ─────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).resolve().parent / "data"
PLANOS_CSV = DATA_DIR / "lucro_taxas_planos.csv"
GASTOS_CSV = DATA_DIR / "gastos_ganhos.csv"

DATA_DIR.mkdir(parents=True, exist_ok=True)
for f in (PLANOS_CSV, GASTOS_CSV):
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)

CATEGORIA_RECEITA_PLANO = "receita_plano"
CATEGORIAS_GASTO = ["infra", "taxa", "marketing", "folha", "outros"]
RECORRENCIA_OPCOES = ["único", "mensal", "anual", "personalizado"]

st.set_page_config(
    page_title="Pulso Finance",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS: layout geral ─────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { max-width: 1600px; margin: 0 auto; padding: 0 1.5rem; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    
    .hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        color: #f1f5f9;
        padding: 1.5rem 1.75rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        border: 1px solid #334155;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }
    .hero h1 { margin: 0; font-size: 1.6rem; font-weight: 700; }
    .hero p { margin: 0.35rem 0 0 0; opacity: 0.9; font-size: 0.95rem; }
    
    .card-metric {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 1rem;
        transition: box-shadow 0.2s;
    }
    .card-metric:hover { box-shadow: 0 6px 16px rgba(0,0,0,0.1); }
    .card-metric .label { font-size: 0.8rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 0.35rem; }
    .card-metric .value { font-size: 1.6rem; font-weight: 700; color: #0f172a; }
    .card-metric.receita .value { color: #059669; }
    .card-metric.gasto .value { color: #dc2626; }
    .card-metric.saldo .value { color: #0369a1; }
    
    .section-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    }
    .section-box h3 { margin: 0 0 0.75rem 0; font-size: 1.1rem; color: #334155; }
    
    .filtros-bar {
        background: #f1f5f9;
        padding: 1rem 1.25rem;
        border-radius: 12px;
        margin-bottom: 1.25rem;
        border: 1px solid #e2e8f0;
    }
    div[data-testid="stExpander"] { border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 0.5rem; }
    .stButton > button { border-radius: 8px; font-weight: 500; }
    .sidebar .sidebar-content { background: #fafafa; }
</style>
""", unsafe_allow_html=True)

# ─── Helpers ──────────────────────────────────────────────────────────────
def load_planos() -> pd.DataFrame:
    if not PLANOS_CSV.exists():
        return pd.DataFrame(columns=[
            "tipo_plano", "preco_unit_usd", "taxa_stripe_unit_usd",
            "taxa_stripe_total_10k_usd", "lucro_100_usd", "lucro_1000_usd", "lucro_10000_usd"
        ])
    df = pd.read_csv(PLANOS_CSV)
    if "tipo_plano" in df.columns:
        df["tipo_plano"] = df["tipo_plano"].astype(str).str.strip()
    return df


def save_planos(df: pd.DataFrame) -> None:
    df.to_csv(PLANOS_CSV, index=False, encoding="utf-8")


def load_gastos() -> pd.DataFrame:
    base_cols = [
        "data", "tipo", "categoria", "descricao", "valor_usd", "moeda", "notas",
        "plano_tipo", "plano_preco", "num_usuarios",
        "recorrencia", "recorrencia_intervalo", "recorrencia_unidade",
    ]
    if not GASTOS_CSV.exists():
        return pd.DataFrame(columns=base_cols)
    df = pd.read_csv(GASTOS_CSV)
    for col in ["recorrencia", "recorrencia_intervalo", "recorrencia_unidade"]:
        if col not in df.columns:
            df[col] = "" if col == "recorrencia" else None
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
    return df


def save_gastos(df: pd.DataFrame) -> None:
    df = df.copy()
    if "data" in df.columns and pd.api.types.is_datetime64_any_dtype(df["data"]):
        df["data"] = df["data"].dt.strftime("%Y-%m-%d")
    df.to_csv(GASTOS_CSV, index=False, encoding="utf-8")


def get_cotacao_brl() -> float:
    if "cotacao_usd_brl" not in st.session_state:
        st.session_state["cotacao_usd_brl"] = 5.85
    return st.session_state["cotacao_usd_brl"]


def format_currency_usd(val):
    if pd.isna(val):
        return ""
    try:
        v = float(val)
        return f"$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return str(val)


def format_currency_brl(val, cotacao: float = 1.0):
    if pd.isna(val):
        return ""
    try:
        v = float(val) * cotacao
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return str(val)


def format_currency(val, em_brl: bool, cotacao: float = 1.0):
    return format_currency_brl(val, cotacao) if em_brl else format_currency_usd(val)


def valor_mensal_equivalente(row: pd.Series) -> float:
    """Para gastos recorrentes, retorna o valor equivalente por mês (USD)."""
    val = float(row.get("valor_usd", 0) or 0)
    rec = str(row.get("recorrencia", "") or "").strip().lower()
    if rec == "mensal":
        return val
    if rec == "anual":
        return val / 12.0
    if rec == "personalizado":
        intervalo = row.get("recorrencia_intervalo")
        unidade = str(row.get("recorrencia_unidade", "") or "").strip().lower()
        try:
            n = float(intervalo)
            if n <= 0:
                return val
            if unidade == "meses":
                return val / n
            if unidade == "dias":
                return val * (30.0 / n)  # ~30 dias por mês
            return val
        except (TypeError, ValueError):
            return val
    return 0.0  # único: não conta como mensal recorrente


# ─── Sidebar ───────────────────────────────────────────────────────────────
def render_sidebar():
    st.sidebar.markdown("### 💰 Pulso Finance")
    st.sidebar.caption("Receita por plano · Custo de operação · Controle total")
    st.sidebar.divider()
    cotacao = st.sidebar.number_input(
        "Cotação USD → BRL (R$ por US$ 1)",
        min_value=0.01,
        value=get_cotacao_brl(),
        step=0.01,
        format="%.2f",
        key="sidebar_cotacao",
    )
    st.session_state["cotacao_usd_brl"] = cotacao
    st.sidebar.divider()
    page = st.sidebar.radio(
        "Navegação",
        [
            "📊 Dashboard",
            "📈 Receita (plano do usuário)",
            "🛠️ Custo de operação",
            "📋 Tabela de planos",
        ],
        index=0,
    )
    return page


# ─── Página: Dashboard ────────────────────────────────────────────────────
def page_dashboard():
    cotacao = get_cotacao_brl()
    em_brl = st.session_state.get("exibir_brl_dash", False)
    fmt = lambda x: format_currency(x, em_brl, cotacao)

    st.markdown(
        '<div class="hero"><h1>📊 Dashboard</h1><p>Visão geral: receita (planos), custo de operação e saldo.</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="filtros-bar">', unsafe_allow_html=True)
    if st.button("🇧🇷 Ver em R$" if not em_brl else "🇺🇸 Ver em USD", key="toggle_brl_dash"):
        st.session_state["exibir_brl_dash"] = not em_brl
        st.rerun()
    if em_brl:
        st.caption(f"Cotação: 1 USD = R$ {cotacao:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.markdown("</div>", unsafe_allow_html=True)

    gastos_df = load_gastos()
    receita_total = 0.0
    custo_total = 0.0
    if not gastos_df.empty and "valor_usd" in gastos_df.columns and "tipo" in gastos_df.columns:
        receita_total = gastos_df[gastos_df["tipo"] == "ganho"]["valor_usd"].sum()
        custo_total = gastos_df[gastos_df["tipo"] == "gasto"]["valor_usd"].sum()
    saldo = receita_total - custo_total
    custo_pct = (custo_total / receita_total * 100) if receita_total else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="card-metric receita"><div class="label">Receita total (planos)</div><div class="value">{fmt(receita_total)}</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="card-metric gasto"><div class="label">Custo de operação</div><div class="value">{fmt(custo_total)}</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="card-metric saldo"><div class="label">Saldo</div><div class="value">{fmt(saldo)}</div></div>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f'<div class="card-metric"><div class="label">Custo % da receita</div><div class="value">{custo_pct:.1f}%</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.subheader("Resumo por categoria (gastos)")
    if not gastos_df.empty and gastos_df[gastos_df["tipo"] == "gasto"].shape[0] > 0:
        g = gastos_df[gastos_df["tipo"] == "gasto"]
        resumo_cat = g.groupby("categoria", dropna=False)["valor_usd"].sum().reset_index()
        resumo_cat.columns = ["Categoria", "Total (USD)"]
        resumo_cat["Total (USD)"] = resumo_cat["Total (USD)"].apply(lambda x: format_currency_usd(x))
        st.dataframe(resumo_cat, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum gasto cadastrado ainda. Use **Custo de operação** para adicionar.")


# ─── Página: Receita (plano do usuário) ───────────────────────────────────
def page_receita_planos():
    planos = load_planos()
    gastos_df = load_gastos()
    cotacao = get_cotacao_brl()
    em_brl = st.session_state.get("exibir_brl_receita", False)

    st.markdown(
        '<div class="hero"><h1>📈 Receita (plano do usuário)</h1><p>Registre a receita vinculada ao plano do usuário — sempre ganho, já líquido de taxas.</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="filtros-bar">', unsafe_allow_html=True)
    if st.button("🇧🇷 Ver em R$" if not em_brl else "🇺🇸 Ver em USD", key="toggle_brl_receita"):
        st.session_state["exibir_brl_receita"] = not em_brl
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.markdown("#### ➕ Adicionar receita de plano")
    st.caption("Selecione o plano (preço) e a quantidade de usuários. O valor é o lucro líquido (após taxas Stripe).")

    if planos.empty:
        st.warning("Cadastre planos na **Tabela de planos** antes de adicionar receita.")
    else:
        # Opções: cada linha do planos = uma opção
        planos["_opcao"] = planos["tipo_plano"] + " — $ " + planos["preco_unit_usd"].astype(str)
        opcoes = planos["_opcao"].tolist()
        idx_sel = st.selectbox("Plano do usuário (tipo + preço)", range(len(opcoes)), format_func=lambda i: opcoes[i], key="sel_plano_receita")
        row_plano = planos.iloc[idx_sel]

        escala = st.radio("Escala de usuários", ["100", "1.000", "10.000", "Outro (informar)"], horizontal=True, key="escala_usuarios")
        if escala == "Outro (informar)":
            num_usuarios = st.number_input("Número de usuários", min_value=1, value=50, step=1, key="num_usuarios_custom")
            # Interpolação: lucro por usuário ≈ lucro_100/100
            lucro_unit = float(row_plano["lucro_100_usd"]) / 100.0
            valor_receita = lucro_unit * num_usuarios
        else:
            num_usuarios = int(escala.replace(".", ""))
            col_lucro = f"lucro_{num_usuarios}_usd" if num_usuarios != 10000 else "lucro_10000_usd"
            col_lucro = "lucro_100_usd" if num_usuarios == 100 else ("lucro_1000_usd" if num_usuarios == 1000 else "lucro_10000_usd")
            valor_receita = float(row_plano[col_lucro])

        descricao = f"{row_plano['tipo_plano']} $ {row_plano['preco_unit_usd']} — {num_usuarios} usuários"
        st.write("**Valor (lucro líquido):**", format_currency(valor_receita, em_brl, cotacao))

        if st.button("Adicionar como receita (ganho)", type="primary", key="btn_add_receita_plano"):
            novo = pd.DataFrame([{
                "data": datetime.now().date().isoformat(),
                "tipo": "ganho",
                "categoria": CATEGORIA_RECEITA_PLANO,
                "descricao": descricao,
                "valor_usd": round(valor_receita, 2),
                "moeda": "USD",
                "notas": "",
                "plano_tipo": row_plano["tipo_plano"],
                "plano_preco": row_plano["preco_unit_usd"],
                "num_usuarios": num_usuarios,
            }])
            # Garantir colunas no df existente
            for col in ["plano_tipo", "plano_preco", "num_usuarios"]:
                if col not in gastos_df.columns:
                    gastos_df[col] = None
            df = pd.concat([load_gastos(), novo], ignore_index=True)
            save_gastos(df)
            st.success("Receita adicionada.")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Histórico de receitas (planos)")
    rec = gastos_df[(gastos_df["tipo"] == "ganho") & (gastos_df["categoria"] == CATEGORIA_RECEITA_PLANO)] if not gastos_df.empty else pd.DataFrame()
    if rec.empty:
        st.caption("Nenhuma receita de plano registrada.")
    else:
        cols_show = ["data", "descricao", "valor_usd"]
        if "num_usuarios" in rec.columns:
            cols_show.append("num_usuarios")
        rec_show = rec[[c for c in cols_show if c in rec.columns]].copy()
        rec_show = rec_show.rename(columns={"valor_usd": "valor"})
        if em_brl and "valor" in rec_show.columns:
            rec_show["valor"] = rec_show["valor"] * cotacao
        st.dataframe(
            rec_show.style.format({"valor": (lambda x: format_currency_brl(x, 1.0) if em_brl else format_currency_usd(x))}, na_rep=""),
            use_container_width=True,
            hide_index=True,
        )
        st.download_button("📥 Exportar CSV (receitas)", data=rec.to_csv(index=False).encode("utf-8-sig"), file_name=f"receitas_planos_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", key="dl_receitas")


# ─── Página: Custo de operação ─────────────────────────────────────────────
def page_custo_operacao():
    gastos_df = load_gastos()
    cotacao = get_cotacao_brl()
    em_brl = st.session_state.get("exibir_brl_custo", False)
    fmt = lambda x: format_currency_brl(x, cotacao) if em_brl else format_currency_usd(x)

    st.markdown(
        '<div class="hero"><h1>🛠️ Custo de operação</h1><p>Controle total dos gastos: infra, taxas, marketing, folha e outros. Recorrência: mensal, anual ou personalizada.</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="filtros-bar">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
    with c1:
        if st.button("🇧🇷 Ver em R$" if not em_brl else "🇺🇸 Ver em USD", key="toggle_brl_custo"):
            st.session_state["exibir_brl_custo"] = not em_brl
            st.rerun()
    with c2:
        filtro_cat = st.multiselect("Categoria", options=CATEGORIAS_GASTO, default=CATEGORIAS_GASTO, key="filtro_cat_custo")
    with c3:
        so_marketing = st.checkbox("📢 Só marketing", value=False, key="filtro_so_marketing")
    with c4:
        if not gastos_df.empty and gastos_df[gastos_df["tipo"] == "gasto"].shape[0] > 0:
            g = gastos_df[gastos_df["tipo"] == "gasto"]
            min_d, max_d = g["data"].min(), g["data"].max()
            if pd.notna(min_d) and pd.notna(max_d):
                periodo = st.date_input("Período", value=(min_d.date(), max_d.date()), key="filtro_data_custo")
                data_inicio = periodo[0] if isinstance(periodo, tuple) and len(periodo) >= 1 else None
                data_fim = periodo[1] if isinstance(periodo, tuple) and len(periodo) == 2 else data_inicio
            else:
                data_inicio = data_fim = None
        else:
            data_inicio = data_fim = None
    st.markdown("</div>", unsafe_allow_html=True)

    gastos_only = gastos_df[gastos_df["tipo"] == "gasto"].copy() if not gastos_df.empty else pd.DataFrame()
    if not gastos_only.empty:
        if so_marketing:
            gastos_only = gastos_only[gastos_only["categoria"] == "marketing"]
        elif filtro_cat:
            gastos_only = gastos_only[gastos_only["categoria"].isin(filtro_cat)]
    if data_inicio and data_fim and "data" in gastos_only.columns:
        gastos_only = gastos_only[(gastos_only["data"].dt.date >= data_inicio) & (gastos_only["data"].dt.date <= data_fim)]

    # ─── Métricas úteis de gastos ─────────────────────────────────────────
    st.subheader("📊 Métricas de gastos")
    if not gastos_df.empty and gastos_df[gastos_df["tipo"] == "gasto"].shape[0] > 0:
        g_all = gastos_df[gastos_df["tipo"] == "gasto"].copy()
        total_geral = g_all["valor_usd"].sum()
        g_all["_mensal"] = g_all.apply(valor_mensal_equivalente, axis=1)
        custo_mensal_recorrente = g_all["_mensal"].sum()
        total_recorrente_anual = custo_mensal_recorrente * 12
        unicos = g_all[~g_all["recorrencia"].fillna("").str.lower().isin(["mensal", "anual", "personalizado"])]
        total_unico = unicos["valor_usd"].sum()
        marketing_df = g_all[g_all["categoria"] == "marketing"]
        total_marketing = marketing_df["valor_usd"].sum()
        pct_marketing = (total_marketing / total_geral * 100) if total_geral else 0

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("Total gastos (período)", fmt(total_geral))
        with m2:
            st.metric("Custo mensal (recorrentes)", fmt(custo_mensal_recorrente))
        with m3:
            st.metric("Recorrentes (equiv. anual)", fmt(total_recorrente_anual))
        with m4:
            st.metric("Gastos únicos", fmt(total_unico))
        with m5:
            st.metric("Marketing (total)", fmt(total_marketing))
        st.caption(f"Marketing representa **{pct_marketing:.1f}%** do total de gastos.")
    else:
        st.info("Adicione gastos para ver métricas.")
    st.markdown("---")

    # ─── Atalhos: Adicionar gasto de infra / Marketing ─────────────────────
    st.subheader("Adicionar gasto")
    default_cat = st.session_state.get("gasto_default_categoria", None)
    bt_infra, bt_marketing, bt_outro = st.columns(3)
    with bt_infra:
        if st.button("🖥️ Gasto de **infra** (recorrente?)", use_container_width=True, key="btn_shortcut_infra"):
            st.session_state["gasto_default_categoria"] = "infra"
            st.rerun()
    with bt_marketing:
        if st.button("📢 Gasto de **marketing**", use_container_width=True, key="btn_shortcut_marketing"):
            st.session_state["gasto_default_categoria"] = "marketing"
            st.rerun()
    with bt_outro:
        if st.button("📝 Outro gasto", use_container_width=True, key="btn_shortcut_outro"):
            st.session_state["gasto_default_categoria"] = None
            st.rerun()

    with st.form("form_gasto"):
        idx_cat = CATEGORIAS_GASTO.index(default_cat) if default_cat in CATEGORIAS_GASTO else 0
        col_a, col_b = st.columns(2)
        with col_a:
            data_g = st.date_input("Data", value=datetime.now().date(), key="gasto_data")
            categoria_g = st.selectbox("Categoria", options=CATEGORIAS_GASTO, index=idx_cat, key="gasto_categoria")
            valor_g = st.number_input("Valor (USD)", min_value=0.0, value=0.0, step=0.01, key="gasto_valor")
            recorrencia_g = st.selectbox("Recorrência", options=RECORRENCIA_OPCOES, key="gasto_recorrencia")
            if recorrencia_g == "personalizado":
                rec_a, rec_b = st.columns(2)
                with rec_a:
                    rec_intervalo = st.number_input("A cada (número)", min_value=1, value=1, step=1, key="gasto_rec_intervalo")
                with rec_b:
                    rec_unidade = st.selectbox("Unidade", options=["meses", "dias"], key="gasto_rec_unidade")
            else:
                rec_intervalo, rec_unidade = None, None
        with col_b:
            descricao_g = st.text_input("Descrição", value="", key="gasto_descricao", placeholder="Ex: AWS, Stripe, Google Ads...")
            notas_g = st.text_area("Notas", value="", key="gasto_notas", placeholder="Opcional")
        if st.form_submit_button("Salvar gasto"):
            rec_str = str(recorrencia_g).strip().lower() if recorrencia_g else "único"
            if rec_str not in ["mensal", "anual", "personalizado"]:
                rec_str = "único"
            row = {
                "data": data_g.isoformat(), "tipo": "gasto", "categoria": categoria_g, "descricao": descricao_g,
                "valor_usd": valor_g, "moeda": "USD", "notas": notas_g,
                "plano_tipo": None, "plano_preco": None, "num_usuarios": None,
                "recorrencia": rec_str, "recorrencia_intervalo": rec_intervalo if rec_str == "personalizado" else None,
                "recorrencia_unidade": rec_unidade if rec_str == "personalizado" else None,
            }
            novo = pd.DataFrame([row])
            df = pd.concat([load_gastos(), novo], ignore_index=True)
            save_gastos(df)
            st.session_state["gasto_default_categoria"] = None
            st.success("Gasto adicionado.")
            st.rerun()
    if default_cat:
        st.session_state["gasto_default_categoria"] = None

    st.subheader("Lista de gastos")
    if gastos_only.empty:
        st.info("Nenhum gasto cadastrado. Use os botões acima (infra, marketing ou outro) e o formulário.")
    else:
        cols_show = ["data", "categoria", "descricao", "valor_usd"]
        show = gastos_only[[c for c in cols_show if c in gastos_only.columns]].copy()
        if "recorrencia" in gastos_only.columns:
            def _rec_label(r):
                rec = str(r.get("recorrencia", "") or "").strip().lower() or "único"
                if rec not in ("mensal", "anual", "personalizado"):
                    return "único"
                if rec == "personalizado":
                    i = r.get("recorrencia_intervalo")
                    u = str(r.get("recorrencia_unidade") or "")
                    if pd.notna(i) and u:
                        return f"a cada {int(i)} {u}"
                return rec
            show["Recorrência"] = gastos_only.apply(_rec_label, axis=1)
        if em_brl and "valor_usd" in show.columns:
            show["valor_usd"] = show["valor_usd"] * cotacao
        st.dataframe(
            show.style.format({"valor_usd": (lambda x: format_currency_brl(x, 1.0) if em_brl else format_currency_usd(x))}, na_rep=""),
            use_container_width=True,
            hide_index=True,
            height=350,
        )
        st.download_button("📥 Exportar CSV (gastos)", data=gastos_only.to_csv(index=False).encode("utf-8-sig"), file_name=f"custo_operacao_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", key="dl_custo")
    with st.expander("🗑️ Remover gasto por índice (na tabela completa)"):
        full = load_gastos()
        gastos_idx = full[full["tipo"] == "gasto"].index.tolist()
        if gastos_idx:
            idx_rm = st.selectbox("Índice da linha", options=gastos_idx, format_func=lambda i: f"{i} — {full.loc[i, 'data']} {full.loc[i, 'descricao']} ({full.loc[i, 'valor_usd']} USD)", key="idx_rm_gasto")
            if st.button("Remover", key="btn_rm_gasto"):
                df = full.drop(index=idx_rm).reset_index(drop=True)
                save_gastos(df)
                st.success("Gasto removido.")
                st.rerun()
        else:
            st.caption("Nenhum gasto para remover.")


# ─── Página: Tabela de planos ──────────────────────────────────────────────
def page_tabela_planos():
    df = load_planos()
    cotacao = get_cotacao_brl()
    em_brl = st.session_state.get("exibir_brl_planos", False)

    st.markdown(
        '<div class="hero"><h1>📋 Tabela de planos</h1><p>Referência de preços, taxas Stripe e lucro líquido por escala de usuários.</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="filtros-bar">', unsafe_allow_html=True)
    if st.button("🇧🇷 Ver em R$" if not em_brl else "🇺🇸 Ver em USD", key="toggle_brl_planos"):
        st.session_state["exibir_brl_planos"] = not em_brl
        st.rerun()
    tipos = sorted(df["tipo_plano"].dropna().unique().tolist()) if not df.empty else []
    filtro_tipo = st.multiselect("Filtrar plano", options=tipos, default=tipos, key="filtro_tipo_planos")
    st.markdown("</div>", unsafe_allow_html=True)

    if df.empty:
        st.info("Nenhum plano cadastrado. Use os expanders abaixo para adicionar ou importar CSV.")
        df = pd.DataFrame(columns=["tipo_plano", "preco_unit_usd", "taxa_stripe_unit_usd", "taxa_stripe_total_10k_usd", "lucro_100_usd", "lucro_1000_usd", "lucro_10000_usd"])

    df_filtrado = df[df["tipo_plano"].isin(filtro_tipo)] if filtro_tipo else df
    display_cols = {
        "tipo_plano": "Plano",
        "preco_unit_usd": "Preço Unit.",
        "taxa_stripe_unit_usd": "Taxa Stripe (Unit.)",
        "taxa_stripe_total_10k_usd": "Taxa Total (10k)",
        "lucro_100_usd": "Lucro (100 usuários)",
        "lucro_1000_usd": "Lucro (1.000 usuários)",
        "lucro_10000_usd": "Lucro (10.000 usuários)",
    }
    df_display = df_filtrado.rename(columns=display_cols)
    col_numericas = [display_cols[k] for k in display_cols if k != "tipo_plano"]
    format_dict = {col: (lambda x, cot=cotacao, brl=em_brl: format_currency(x, brl, cot)) for col in col_numericas}
    st.dataframe(df_display.style.format(format_dict, na_rep=""), use_container_width=True, height=380, hide_index=True)

    e1, e2, e3 = st.columns(3)
    with e1:
        with st.expander("➕ Adicionar plano"):
            t = st.selectbox("Tipo", ["MENSAL", "ANUAL", "MENSAL DESC.", "ANUAL DESC."], key="new_tipo")
            preco = st.number_input("Preço unit. (USD)", min_value=0.0, value=29.99, step=0.01, key="new_preco")
            taxa_u = st.number_input("Taxa Stripe unit. (USD)", min_value=0.0, value=2.20, step=0.01, key="new_taxa_u")
            taxa_10k = st.number_input("Taxa total 10k (USD)", min_value=0.0, value=22000.0, step=100.0, key="new_taxa_10k")
            l100 = st.number_input("Lucro 100 usuários (USD)", value=779.0, step=1.0, key="new_l100")
            l1k = st.number_input("Lucro 1.000 (USD)", value=7790.0, step=10.0, key="new_l1k")
            l10k = st.number_input("Lucro 10.000 (USD)", value=77900.0, step=100.0, key="new_l10k")
            if st.button("Adicionar", key="btn_add_plano"):
                row = pd.DataFrame([{"tipo_plano": t, "preco_unit_usd": preco, "taxa_stripe_unit_usd": taxa_u, "taxa_stripe_total_10k_usd": taxa_10k, "lucro_100_usd": l100, "lucro_1000_usd": l1k, "lucro_10000_usd": l10k}])
                save_planos(pd.concat([load_planos(), row], ignore_index=True))
                st.success("Plano adicionado.")
                st.rerun()
    with e2:
        with st.expander("🗑️ Remover plano"):
            idx = st.number_input("Índice", min_value=0, max_value=max(len(df) - 1, 0), value=0, key="del_idx_plano")
            if st.button("Remover", key="btn_del_plano"):
                save_planos(load_planos().drop(index=idx).reset_index(drop=True))
                st.success("Removido.")
                st.rerun()
    with e3:
        with st.expander("📤 Importar CSV"):
            up = st.file_uploader("CSV", type=["csv"], key="up_planos")
            if up:
                try:
                    new_df = pd.read_csv(up)
                    replace = st.checkbox("Substituir todos", value=False, key="replace_planos")
                    if st.button("Importar", key="btn_import_planos"):
                        save_planos(new_df if replace else pd.concat([load_planos(), new_df], ignore_index=True))
                        st.success("Importado.")
                        st.rerun()
                except Exception as e:
                    st.error(str(e))


# ─── Main ──────────────────────────────────────────────────────────────────
def main():
    page = render_sidebar()
    if page == "📊 Dashboard":
        page_dashboard()
    elif page == "📈 Receita (plano do usuário)":
        page_receita_planos()
    elif page == "🛠️ Custo de operação":
        page_custo_operacao()
    else:
        page_tabela_planos()


if __name__ == "__main__":
    main()
