import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(layout='wide')

st.markdown(
    """
    <style>
    /* === CORES E ESTILO GERAL === */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    /* botões */
    .stButton>button, .stDownloadButton>button {
        background-color: #577aa6 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        transition: 0.2s;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #436182 !important;
        transform: scale(1.02);
    }

    /* sidebar */
    section[data-testid="stSidebar"] {
        background-color: #eef2f6 !important;
    }

    /* títulos */
    h1, h2, h3, h4 {
        color: #2c3e50 !important;
        font-weight: 600;
    }

    /* abas (tabs) */
    button[data-baseweb="tab"] {
        background-color: #e3e9f0 !important;
        color: #000 !important;
        border-radius: 8px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #577aa6 !important;
        color: white !important;
        font-weight: bold !important;
    }

    /* métricas */
    div[data-testid="stMetricValue"] {
        color: #577aa6 !important;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Função para formatar números
def formata_numero(valor, prefixo=''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

# Título
st.title('DASHBOARD DE VENDAS :shopping_cart:')

# Leitura dos dados
url = 'https://labdados.com/produtos'
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value=True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)

query_string = {'regiao': regiao.lower(), 'ano': ano}
response = requests.get(url, params=query_string)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

# =====================
# TABELAS DE RECEITA
# =====================
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(
    receita_estados, left_on='Local da compra', right_index=True).sort_values('Preço', ascending=False)

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False).reset_index()

# =====================
# TABELAS DE QUANTIDADE DE VENDAS
# =====================
vendas_estados = dados.groupby('Local da compra')[['Preço']].count().rename(columns={'Preço': 'Quantidade de Vendas'})
vendas_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(
    vendas_estados, left_on='Local da compra', right_index=True).sort_values('Quantidade de Vendas', ascending=False)

vendas_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].count().reset_index()
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
vendas_mensal['Mes'] = vendas_mensal['Data da Compra'].dt.month_name()

vendas_categorias = dados.groupby('Categoria do Produto')[['Preço']].count().rename(columns={'Preço': 'Quantidade de Vendas'}).sort_values('Quantidade de Vendas', ascending=False).reset_index()

# =====================
# TABELAS DE VENDEDORES
# =====================
vendedores = dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']).sort_values('sum', ascending=False)

# =====================
# GRÁFICOS DE RECEITA
# =====================
fig_mapa_receita = px.scatter_geo(receita_estados,
                                  lat='lat',
                                  lon='lon',
                                  scope='south america',
                                  size='Preço',
                                  template='seaborn',
                                  hover_name='Local da compra',
                                  hover_data={'lat': False, 'lon': False},
                                  title='Receita por estado')

fig_receita_mensal = px.line(receita_mensal,
                             x='Mes',
                             y='Preço',
                             markers=True,
                             color='Ano',
                             line_dash='Ano',
                             title='Receita Mensal')
fig_receita_mensal.update_layout(yaxis_title='Receita')

fig_receita_estados = px.bar(receita_estados.head(),
                             x='Local da compra',
                             y='Preço',
                             text_auto=True,
                             title='Top estados (receita)')
fig_receita_estados.update_layout(yaxis_title='Receita')

fig_receita_categorias = px.bar(receita_categorias,
                                x='Categoria do Produto',
                                y='Preço',
                                text_auto=True,
                                title='Receita por categoria')
fig_receita_categorias.update_layout(yaxis_title='Receita')

# =====================
# GRÁFICOS DE QUANTIDADE DE VENDAS
# =====================
fig_mapa_vendas = px.scatter_geo(vendas_estados,
                                 lat='lat',
                                 lon='lon',
                                 scope='south america',
                                 size='Quantidade de Vendas',
                                 template='seaborn',
                                 hover_name='Local da compra',
                                 hover_data={'lat': False, 'lon': False},
                                 title='Quantidade de Vendas por estado')

fig_vendas_mensal = px.line(vendas_mensal,
                            x='Mes',
                            y='Preço',
                            markers=True,
                            color='Ano',
                            line_dash='Ano',
                            title='Quantidade de Vendas Mensal')
fig_vendas_mensal.update_layout(yaxis_title='Quantidade de Vendas')

fig_vendas_estados = px.bar(vendas_estados.head(),
                            x='Local da compra',
                            y='Quantidade de Vendas',
                            text_auto=True,
                            title='Top estados (quantidade de vendas)')
fig_vendas_estados.update_layout(yaxis_title='Quantidade de Vendas')

fig_vendas_categorias = px.bar(vendas_categorias,
                               x='Categoria do Produto',
                               y='Quantidade de Vendas',
                               text_auto=True,
                               title='Quantidade de Vendas por categoria')
fig_vendas_categorias.update_layout(yaxis_title='Quantidade de Vendas')

# =====================
# VISUALIZAÇÃO STREAMLIT
# =====================
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])

# --- ABA 1: Receita ---
with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita Total', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de Vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)

# --- ABA 2: Quantidade de Vendas ---
with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Total de Vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_mapa_vendas, use_container_width=True)
        st.plotly_chart(fig_vendas_estados, use_container_width=True)
    with coluna2:
        st.metric('Receita Total', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_vendas_mensal, use_container_width=True)
        st.plotly_chart(fig_vendas_categorias, use_container_width=True)

# --- ABA 3: Vendedores ---
with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita Total', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].head(qtd_vendedores),
                                        x='sum',
                                        y=vendedores[['sum']].head(qtd_vendedores).index,
                                        text_auto=True,
                                        title=f'Top {qtd_vendedores} vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de Vendas', formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[['count']].head(qtd_vendedores),
                                       x='count',
                                       y=vendedores[['count']].head(qtd_vendedores).index,
                                       text_auto=True,
                                       title=f'Top {qtd_vendedores} vendedores (quantidade de vendas)')
        st.plotly_chart(fig_vendas_vendedores, use_container_width=True)
