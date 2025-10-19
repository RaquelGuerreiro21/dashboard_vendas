import streamlit as st
import requests
import pandas as pd
import time
import os

# ========= FUNÇÕES =========
@st.cache_data
def carregar_dados_api(timeout=10, max_retries=3, backoff=2):
    url = 'https://labdados.com/produtos'
    attempt = 0
    last_exception = None
    while attempt < max_retries:
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            # validação simples: espera lista/dict
            if not data:
                raise ValueError("Resposta vazia da API")
            df = pd.DataFrame.from_dict(data)
            df['Data da Compra'] = pd.to_datetime(df['Data da Compra'], format='%d/%m/%Y')
            return df
        except Exception as e:
            last_exception = e
            attempt += 1
            # backoff exponencial simples
            time.sleep(backoff ** attempt)
    # se chegou aqui, todas as tentativas falharam
    raise last_exception


def carregar_dados(fallback_path='dados_fallback.csv'):
    """Tenta carregar da API com retries. Se falhar, tenta carregar fallback local (se existir)."""
    try:
        with st.spinner("Baixando dados da API..."):
            df = carregar_dados_api()
        return df
    except Exception as e:
        st.warning(f"Erro ao carregar os dados da API: {e}")
        # tenta fallback local
        if os.path.exists(fallback_path):
            try:
                st.info(f"Carregando fallback local: {fallback_path}")
                df = pd.read_csv(fallback_path)
                if 'Data da Compra' in df.columns:
                    df['Data da Compra'] = pd.to_datetime(df['Data da Compra'], errors='coerce', dayfirst=True)
                return df
            except Exception as e_local:
                st.error(f"Falha ao carregar fallback local: {e_local}")
                return pd.DataFrame()
        else:
            st.info("Nenhum fallback local encontrado. Você pode salvar um CSV local chamado 'dados_fallback.csv' na raiz do projeto para usar em desenvolvimento.")
            return pd.DataFrame()


@st.cache_data
def converte_csv(df):
    return df.to_csv(index=False).encode('utf-8')


def mensagem_sucesso():
    sucesso = st.success('Arquivo CSV gerado com sucesso!', icon="✅")
    time.sleep(3)
    sucesso.empty()


# ========= CONFIGURAÇÃO =========
st.title('DADOS BRUTOS :file_folder:')

# CSS PARA AJUSTAR CORES DAS TAGS E BOTÕES
st.markdown(
    """
    <style>
    /* cor das tags (multiselect, filtros, etc) */
    div[data-baseweb="tag"],
    .stMultiSelect span,
    .stMultiSelect .css-1n2onr6,
    span[data-testid="stTag"] {
        background-color: #577aa6 !important;
        color: white !important;
        border-radius: 6px !important;
    }

    /* botões */
    .stDownloadButton>button, .stButton>button {
        background-color: #577aa6 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        transition: 0.2s;
    }
    .stDownloadButton>button:hover, .stButton>button:hover {
        background-color: #436182 !important;
        transform: scale(1.02);
    }

    /* sidebar mais suave */
    section[data-testid="stSidebar"] {
        background-color: #eef2f6 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ========= CARREGAMENTO =========
dados = carregar_dados()

if dados.empty:
    st.warning("Não foi possível carregar os dados.")
    if st.button("🔄 Tentar novamente"):
        st.experimental_rerun()
    st.stop()

# ========= SELEÇÃO DE COLUNAS =========
with st.expander('Colunas'):
    colunas = st.multiselect(
        'Selecione as colunas que deseja visualizar',
        options=list(dados.columns),
        default=list(dados.columns)
    )

# ========= FILTROS =========
st.sidebar.title('Filtros')

with st.sidebar.expander('Produto'):
    produtos = st.multiselect('Selecione os produtos', dados['Produto'].unique())

with st.sidebar.expander('Categoria do Produto'):
    categorias = st.multiselect('Selecione as categorias', dados['Categoria do Produto'].unique())

with st.sidebar.expander('Vendedor'):
    vendedores = st.multiselect('Selecione os vendedores', dados['Vendedor'].unique())

with st.sidebar.expander('Local da compra'):
    locais = st.multiselect('Selecione os locais', dados['Local da compra'].unique())

with st.sidebar.expander('Tipo de pagamento'):
    pagamentos = st.multiselect('Selecione o tipo de pagamento', dados['Tipo de pagamento'].unique())

with st.sidebar.expander('Preço do produto'):
    preco = st.slider(
        'Selecione a faixa de preço',
        float(dados['Preço'].min()), float(dados['Preço'].max()),
        (float(dados['Preço'].min()), float(dados['Preço'].max()))
    )

with st.sidebar.expander('Frete'):
    frete = st.slider(
        'Selecione o valor do frete',
        float(dados['Frete'].min()), float(dados['Frete'].max()),
        (float(dados['Frete'].min()), float(dados['Frete'].max()))
    )

with st.sidebar.expander('Avaliação da compra'):
    avaliacao = st.slider(
        'Selecione a faixa de avaliação',
        int(dados['Avaliação da compra'].min()), int(dados['Avaliação da compra'].max()),
        (int(dados['Avaliação da compra'].min()), int(dados['Avaliação da compra'].max()))
    )

with st.sidebar.expander('Quantidade de parcelas'):
    parcelas = st.slider(
        'Selecione a faixa de parcelas',
        int(dados['Quantidade de parcelas'].min()), int(dados['Quantidade de parcelas'].max()),
        (int(dados['Quantidade de parcelas'].min()), int(dados['Quantidade de parcelas'].max()))
    )

with st.sidebar.expander('Data da compra'):
    data_compra = st.date_input(
        'Selecione o intervalo de datas',
        value=(dados['Data da Compra'].min(), dados['Data da Compra'].max()),
        min_value=dados['Data da Compra'].min(),
        max_value=dados['Data da Compra'].max()
    )

# ========= FILTRAGEM =========
dados_filtrados = dados.copy()

if produtos:
    dados_filtrados = dados_filtrados[dados_filtrados['Produto'].isin(produtos)]
if categorias:
    dados_filtrados = dados_filtrados[dados_filtrados['Categoria do Produto'].isin(categorias)]
if vendedores:
    dados_filtrados = dados_filtrados[dados_filtrados['Vendedor'].isin(vendedores)]
if locais:
    dados_filtrados = dados_filtrados[dados_filtrados['Local da compra'].isin(locais)]
if pagamentos:
    dados_filtrados = dados_filtrados[dados_filtrados['Tipo de pagamento'].isin(pagamentos)]

dados_filtrados = dados_filtrados[
    (dados_filtrados['Preço'].between(preco[0], preco[1])) &
    (dados_filtrados['Frete'].between(frete[0], frete[1])) &
    (dados_filtrados['Avaliação da compra'].between(avaliacao[0], avaliacao[1])) &
    (dados_filtrados['Quantidade de parcelas'].between(parcelas[0], parcelas[1]))
]

if isinstance(data_compra, tuple) and len(data_compra) == 2:
    dados_filtrados = dados_filtrados[
        (dados_filtrados['Data da Compra'] >= pd.to_datetime(data_compra[0])) &
        (dados_filtrados['Data da Compra'] <= pd.to_datetime(data_compra[1]))
    ]

# ========= EXIBIÇÃO =========
st.dataframe(dados_filtrados[colunas])
st.caption(f"{dados_filtrados.shape[0]} registros exibidos após os filtros aplicados.")
st.markdown(f"A tabela possui :blue[{dados_filtrados.shape[1]}] colunas e :blue[{dados_filtrados.shape[0]}] linhas.")

# ========= DOWNLOAD =========
st.markdown('Escreva um nome para o arquivo e clique no botão para baixar os dados filtrados em CSV.')
col1, col2 = st.columns(2)
with col1:
    nome_arquivo = st.text_input('', label_visibility='collapsed', value='dados') + '.csv'
with col2:
    st.download_button(
        'Fazer o download do CSV',
        data=converte_csv(dados_filtrados),
        file_name=nome_arquivo,
        mime='text/csv',
        on_click=mensagem_sucesso
    )
