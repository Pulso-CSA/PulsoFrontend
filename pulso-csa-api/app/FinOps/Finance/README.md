# Pulso Finance

App **Streamlit** para controle de **gastos**, **ganhos**, **taxas** e **lucro por planos** (incluindo tabela de Lucro e Taxas Acumuladas em USD).

## Funcionalidades

- **Lucro e Taxas (Planos)**  
  Visualização, atualização e exportação da tabela de preços, taxas Stripe e lucro (100 / 1.000 / 10.000 usuários). Tipos: MENSAL, ANUAL, MENSAL DESC., ANUAL DESC.
- **Gastos e Ganhos**  
  Cadastro de movimentos (data, tipo, categoria, descrição, valor USD, moeda, notas). Visualização, adição, remoção e exportação.
- **Resumo**  
  Totais (soma lucro 10k, total ganhos, total gastos, saldo) e resumo por tipo de plano.

## Como rodar

Na pasta do repositório (ou na pasta `Finance`):

```bash
pip install -r Finance/requirements.txt
streamlit run Finance/app_finance.py
```

Ou, a partir da pasta `Finance`:

```bash
pip install -r requirements.txt
streamlit run app_finance.py
```

Abrir no navegador no endereço indicado (geralmente `http://localhost:8501`).

## Dados

- **`data/lucro_taxas_planos.csv`** — Tabela de lucro e taxas por plano (editável pelo app).
- **`data/gastos_ganhos.csv`** — Movimentos de gastos e ganhos (editável pelo app).

Exportação disponível: **CSV**, **Excel** (se `openpyxl` estiver instalado) e **JSON**.
