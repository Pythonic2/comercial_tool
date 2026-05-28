import os
from datetime import date
from decimal import Decimal

import django
import pandas as pd
import streamlit as st


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from comercial.models import Cliente, Evento, Orcamento, Produto, Servico  # noqa: E402


st.set_page_config(page_title="Dashboard Dona do Chopp", page_icon="DC", layout="wide")


@st.cache_data(ttl=60)
def load_data():
    orcamentos_rows = []
    for orcamento in Orcamento.objects.select_related("cliente").prefetch_related("itens_produto", "itens_servico"):
        orcamentos_rows.append(
            {
                "id": orcamento.id,
                "cliente": orcamento.cliente.nome_completo,
                "status": orcamento.get_status_display(),
                "status_codigo": orcamento.status,
                "forma_pagamento": orcamento.get_forma_pagamento_display(),
                "valor_total": float(orcamento.valor_total),
                "desconto": float(orcamento.desconto or Decimal("0.00")),
                "criado_em": orcamento.criado_em.date(),
            }
        )

    eventos_rows = []
    for evento in Evento.objects.select_related("cliente", "contrato"):
        eventos_rows.append(
            {
                "id": evento.id,
                "data": evento.data,
                "cliente": evento.cliente.nome_completo,
                "tipo": evento.tipo_evento,
                "status": evento.get_status_display(),
                "status_codigo": evento.status,
                "valor_total": float(evento.valor_total),
                "profissional": "Sim" if evento.profissional else "Nao",
                "bomba": evento.get_bomba_opcao_display() if evento.bomba_opcao else "Nao definido",
            }
        )

    produtos_rows = list(
        Produto.objects.select_related("marca").values(
            "nome",
            "marca__nome",
            "valor",
            "estoque_quantidade",
            "disponivel",
            "litros",
        )
    )

    return pd.DataFrame(orcamentos_rows), pd.DataFrame(eventos_rows), pd.DataFrame(produtos_rows)


def filter_by_period(df, column, periodo):
    if df.empty or periodo == "Todos":
        return df

    today = date.today()
    values = pd.to_datetime(df[column])
    if periodo == "Mes atual":
        mask = (values.dt.year == today.year) & (values.dt.month == today.month)
    elif periodo == "Semestre atual":
        start_month = 1 if today.month <= 6 else 7
        end_month = 6 if today.month <= 6 else 12
        mask = (values.dt.year == today.year) & values.dt.month.between(start_month, end_month)
    else:
        mask = values.dt.year == today.year
    return df.loc[mask]


def money(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


orcamentos_df, eventos_df, produtos_df = load_data()

st.title("Dashboard comercial")
st.caption("Dona do Chopp: orcamentos, contratos e eventos com dados ficticios de demonstracao.")

with st.sidebar:
    st.header("Filtros")
    periodo = st.selectbox("Periodo", ["Mes atual", "Semestre atual", "Ano atual", "Todos"])
    status_evento = st.selectbox("Status do evento", ["Todos", "Pendente", "Completo", "Cancelado"])

orcamentos_filtrados = filter_by_period(orcamentos_df, "criado_em", periodo)
eventos_filtrados = filter_by_period(eventos_df, "data", periodo)
if status_evento != "Todos" and not eventos_filtrados.empty:
    eventos_filtrados = eventos_filtrados[eventos_filtrados["status"] == status_evento]

executados = orcamentos_filtrados[orcamentos_filtrados["status_codigo"] == "executado"] if not orcamentos_filtrados.empty else pd.DataFrame()
pendentes = (
    orcamentos_filtrados[~orcamentos_filtrados["status_codigo"].isin(["executado", "cancelado"])]
    if not orcamentos_filtrados.empty
    else pd.DataFrame()
)

metric_1, metric_2, metric_3, metric_4, metric_5 = st.columns(5)
metric_1.metric("Vendido executado", money(executados["valor_total"].sum()) if not executados.empty else "R$ 0,00")
metric_2.metric("Orcamentos executados", len(executados))
metric_3.metric("Orcamentos pendentes", len(pendentes))
metric_4.metric("Eventos completos", int((eventos_filtrados["status_codigo"] == "completo").sum()) if not eventos_filtrados.empty else 0)
metric_5.metric("Clientes", Cliente.objects.count())

tabs = st.tabs(["Pendencias", "Eventos", "Produtos", "Resumo"])

with tabs[0]:
    st.subheader("Contratos/orcamentos ainda nao executados")
    if pendentes.empty:
        st.success("Sem pendencias no filtro atual.")
    else:
        st.dataframe(
            pendentes[["cliente", "status", "forma_pagamento", "valor_total", "criado_em"]].sort_values("criado_em", ascending=False),
            width="stretch",
            hide_index=True,
        )

with tabs[1]:
    st.subheader("Agenda de eventos")
    if eventos_filtrados.empty:
        st.info("Nenhum evento encontrado.")
    else:
        st.dataframe(
            eventos_filtrados[["data", "cliente", "tipo", "status", "valor_total", "profissional", "bomba"]].sort_values("data"),
            width="stretch",
            hide_index=True,
        )

with tabs[2]:
    st.subheader("Estoque e produtos")
    if produtos_df.empty:
        st.info("Sem produtos cadastrados.")
    else:
        produtos_view = produtos_df.rename(
            columns={
                "marca__nome": "marca",
                "estoque_quantidade": "estoque",
                "disponivel": "disponivel",
            }
        )
        st.dataframe(produtos_view, width="stretch", hide_index=True)

with tabs[3]:
    st.subheader("Resumo geral da base")
    total_eventos = Evento.objects.count()
    total_orcamentos = Orcamento.objects.count()
    total_produtos = Produto.objects.count()
    total_servicos = Servico.objects.count()
    resumo = pd.DataFrame(
        [
            {"Indicador": "Clientes cadastrados", "Total": Cliente.objects.count()},
            {"Indicador": "Produtos cadastrados", "Total": total_produtos},
            {"Indicador": "Servicos cadastrados", "Total": total_servicos},
            {"Indicador": "Orcamentos cadastrados", "Total": total_orcamentos},
            {"Indicador": "Eventos cadastrados", "Total": total_eventos},
        ]
    )
    st.dataframe(resumo, width="stretch", hide_index=True)

st.divider()
st.header("Visualizacoes graficas")

chart_col, status_col = st.columns([2, 1])

with chart_col:
    st.subheader("Receita executada por data")
    if executados.empty:
        st.info("Sem orcamentos executados no periodo selecionado.")
    else:
        receita = executados.groupby("criado_em", as_index=False)["valor_total"].sum()
        st.bar_chart(receita, x="criado_em", y="valor_total")

with status_col:
    st.subheader("Eventos por status")
    if eventos_filtrados.empty:
        st.info("Sem eventos no periodo selecionado.")
    else:
        eventos_status = eventos_filtrados["status"].value_counts().rename_axis("status").reset_index(name="total")
        st.bar_chart(eventos_status, x="status", y="total")

orcamento_col, pagamento_col = st.columns(2)

with orcamento_col:
    st.subheader("Orcamentos por status")
    if orcamentos_filtrados.empty:
        st.info("Sem orcamentos no periodo selecionado.")
    else:
        orcamento_status = orcamentos_filtrados["status"].value_counts().rename_axis("status").reset_index(name="total")
        st.bar_chart(orcamento_status, x="status", y="total")

with pagamento_col:
    st.subheader("Receita por forma de pagamento")
    if orcamentos_filtrados.empty:
        st.info("Sem valores para comparar.")
    else:
        pagamento = orcamentos_filtrados.groupby("forma_pagamento", as_index=False)["valor_total"].sum()
        st.bar_chart(pagamento, x="forma_pagamento", y="valor_total")

estoque_col, agenda_col = st.columns(2)

with estoque_col:
    st.subheader("Estoque por produto")
    if produtos_df.empty:
        st.info("Sem produtos cadastrados.")
    else:
        estoque = produtos_df.rename(columns={"estoque_quantidade": "estoque"}).sort_values("estoque", ascending=False)
        st.bar_chart(estoque, x="nome", y="estoque")

with agenda_col:
    st.subheader("Valor dos eventos por data")
    if eventos_filtrados.empty:
        st.info("Sem eventos no periodo selecionado.")
    else:
        eventos_valor = eventos_filtrados.groupby("data", as_index=False)["valor_total"].sum()
        st.line_chart(eventos_valor, x="data", y="valor_total")
