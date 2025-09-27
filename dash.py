import streamlit as st
from streamlit_option_menu import option_menu
from query import connection
import pandas as pd
import plotly.express as px
from pathlib import Path
import base64

st.set_page_config(page_title="SP-AirQuality Dashboard", layout="wide")

# -------------------------------
# Função para carregar dados com cache
@st.cache_data
def load_data(query):
    return connection(query)

# -------------------------------
# Queries para cada tabela
queries = {
    "leituras": "SELECT * FROM tb_leituras",
    "qualidade": "SELECT * FROM tb_qualidade",
    "poluentes": "SELECT * FROM tb_poluentes",
    "recomendacoes": "SELECT * FROM tb_recomendacao"
}

# -------------------------------
# Função para carregar todas as tabelas
def carregar_todas_tabelas():
    data = {}
    for key, query in queries.items():
        data[key] = connection(query)
    return data

# -------------------------------
# Carregar dados inicialmente (com cache)
dfs = {key: load_data(q) for key, q in queries.items()}

# -------------------------------
# Botão para atualizar todos os dados
if st.sidebar.button("🔄 Atualizar Dados"):
    dfs = carregar_todas_tabelas()
    # st.sidebar.success("✅ Todos os dados foram atualizados!")

# -------------------------------
# Função para carregar imagens locais em HTML
def img_to_html(path, width=50, height=50):
    if not Path(path).is_file():
        return ""
    with open(path, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    ext = Path(path).suffix.lower()
    mime = {"png":"image/png","jpg":"image/jpeg","jpeg":"image/jpeg","gif":"image/gif"}.get(ext[1:], "image/png")
    return f'<img src="data:{mime};base64,{encoded}" style="width:{width}px;height:{height}px;margin-right:10px;border-radius:5px;">'

# -------------------------------
# Menu lateral
with st.sidebar:
    selected = option_menu(
        menu_title="Menu",
        options=["Página Inicial", "Leituras", "Qualidade", "Poluentes"],
        icons=["house", "wind", "bar-chart-line", "droplet"],
        menu_icon="cast",
        default_index=0
    )

# -------------------------------
# Página Inicial
if selected == "Página Inicial":
    st.title("🌬️ SP-AirQuality Dashboard")
    st.subheader("O sistema de monitoramento da qualidade do ar tem como objetivo proteger a saúde da população 👩‍👩‍👧‍👦🌱, fornecendo dados em tempo real sobre poluentes atmosféricos e condições ambientais. Com isso, busca prevenir doenças respiratórias e cardiovasculares 🫁❤️ e oferecer alertas para grupos vulneráveis 👶👵.")

    query = """
    SELECT l.idLeitura, l.data_hora, l.co2, l.umidade, l.pressao, l.temperatura,
           q.aqi, q.category, q.poluenteDominante
    FROM tb_leituras l
    LEFT JOIN tb_qualidade q ON l.idLeitura = q.idLeitura
    """
    df = load_data(query)

    # Cards
    total_leituras = len(df)

    aqi = df['aqi'].iloc[-1] if not df['aqi'].isnull().all() else 0
    co2 = df['co2'].iloc[-1] if not df['co2'].isnull().all() else 0
    temp = df['temperatura'].iloc[-1] if not df['temperatura'].isnull().all() else 0

    cards = [
        {"titulo": "Total Leituras", "descricao": total_leituras, "img": "image/card10.gif"},
        {"titulo": "AQI", "descricao": f"{aqi:.1f}", "img": "image/card11.gif"},
        {"titulo": "CO₂ (ppm)", "descricao": f"{co2:.2f}", "img": "image/card8.gif"},
        {"titulo": "Temp. (°C)", "descricao": f"{temp:.2f}", "img": "image/card3.gif"}
    ]

    st.title("👨‍💻 Análise preliminar dos dados.")

    cols = st.columns(len(cards))
    for idx, card in enumerate(cards):
        with cols[idx]:
            img_html = img_to_html(card["img"])
            st.markdown(f"""
                <div style="
                    border:1px solid #000000;
                    border-radius:10px;
                    padding:10px;
                    display:flex;
                    align-items:center;
                    background-color:#B0C4DE;">
                    {img_html}
                    <div><strong>{card['titulo']}</strong><br>{card['descricao']}</div>
                </div>
            """, unsafe_allow_html=True)
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)

# -------------------------------
# Página Leituras
elif selected == "Leituras":
    st.title("📊 Dados coletados via dispositivo")
    st.subheader("Realizar a coleta de dados da qualidade do ar por meio de um dispositivo desenvolvido por alunos e professores do SENAI 🏫🤝. O equipamento é capaz de captar informações ambientais 🌱🌍 e transmiti-las via Wi-Fi 📡 para um banco de dados centralizado 💾, permitindo o armazenamento e análise em tempo real. Dessa forma, busca-se disponibilizar informações confiáveis para apoiar a saúde da população 🫁❤️ e subsidiar ações ambientais e educativas.")
    df = dfs['leituras']  # usa o DataFrame atualizado

    # Cards principais
    cards = [
        {"titulo":"Qtd Leituras","descricao":len(df),"img":"image/card10.gif"},
        {"titulo":"CO₂ Médio","descricao":f"{df['co2'].mean():.2f}" if not df.empty else "0","img":"image/card8.gif"},
        {"titulo":"Umidade Média","descricao":f"{df['umidade'].mean():.2f}" if not df.empty else "0","img":"image/card2.gif"},
        {"titulo":"Temperatura Média","descricao":f"{df['temperatura'].mean():.2f}" if not df.empty else "0","img":"image/card3.gif"},
    ]

    cols = st.columns(len(cards))
    for idx, card in enumerate(cards):
        with cols[idx]:
            img_html = img_to_html(card["img"])
            st.markdown(f"""
                <div style="
                    border:1px solid #B0C4DE;
                    border-radius:10px;
                    padding:10px;
                    display:flex;
                    align-items:center;
                    background-color:#B0C4DE;">
                    {img_html}
                    <div><strong>{card['titulo']}</strong><br>{card['descricao']}</div>
                </div>
            """, unsafe_allow_html=True)

    if not df.empty:
        st.subheader("🔍 Análises individuais Temperatura, CO₂ e Umidade")
        col1, col2, col3 = st.columns(3)

        with col1:
            fig_temp = px.line(df, x="data_hora", y="temperatura", title="Temperatura (°C)")
            st.plotly_chart(fig_temp, use_container_width=True)

        with col2:
            fig_co2 = px.line(df, x="data_hora", y="co2", title="CO₂ (ppm)", line_shape='linear', color_discrete_sequence=['red'])
            st.plotly_chart(fig_co2, use_container_width=True)

        with col3:
            fig_umid = px.line(df, x="data_hora", y="umidade", title="Umidade (%)", line_shape='linear', color_discrete_sequence=['blue'])
            st.plotly_chart(fig_umid, use_container_width=True)

        st.subheader("🔍 Comparativo entre Temperatura, CO₂ e Umidade")
        col4, col5 = st.columns(2)

        with col4:
            fig_comp = px.line(df, x="data_hora", y=["temperatura", "co2", "umidade"],
                               labels={"value":"Medida","variable":"Variável"},
                               title="Comparativo de Leituras")
            st.plotly_chart(fig_comp, use_container_width=True)

        with col5:
            df['data'] = pd.to_datetime(df['data_hora']).dt.date
            daily_avg = df.groupby('data')[["temperatura","co2","umidade"]].mean().reset_index()
            fig_daily = px.line(daily_avg, x="data", y=["temperatura","co2","umidade"],
                                labels={"value":"Média","variable":"Variável"},
                                title="Médias diárias de Temperatura, CO₂ e Umidade")
            st.plotly_chart(fig_daily, use_container_width=True)

# -------------------------------
# Página Qualidade
# -------------------------------
elif selected == "Qualidade":
    st.title("📈 Qualidade do Ar")

    # -------------------
    # Dados
    # -------------------
    df_qualidade = dfs['qualidade'].copy()
    df_leituras = dfs['leituras'][['idLeitura', 'data_hora']].copy()
    df_recomendacoes = dfs['recomendacoes'].copy()

    # Garantir que 'data_hora' venha do df_leituras
    df_qualidade = df_qualidade.merge(df_leituras, on='idLeitura', how='left')
    df_recomendacoes = df_recomendacoes.merge(df_leituras, on='idLeitura', how='left')

    # Garantir datetime
    df_qualidade['data_hora'] = pd.to_datetime(df_qualidade['data_hora'])
    df_recomendacoes['data_hora'] = pd.to_datetime(df_recomendacoes['data_hora'])

    # -------------------
    # Função para exibir imagens em base64
    # -------------------
    from pathlib import Path
    import base64

    def img_to_html(path, width=50, height=50):
        if not Path(path).is_file():
            return ""
        with open(path, "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode()
        ext = Path(path).suffix.lower()
        mime = {"png":"image/png","jpg":"image/jpeg","jpeg":"image/jpeg","gif":"image/gif"}.get(ext[1:], "image/png")
        return f'<img src="data:{mime};base64,{encoded}" style="width:{width}px;height:{height}px;margin-right:10px;border-radius:5px;">'

    # -------------------
    # Cards principais
    # -------------------
    total_registros = len(df_qualidade)
    aqi_medio = df_qualidade['aqi'].mean() if not df_qualidade['aqi'].isnull().all() else 0

    cards = [
        {"titulo":"Qtd Registros", "descricao": total_registros, "img":"image/card10.gif"},
        {"titulo":"AQI Médio", "descricao": f"{aqi_medio:.1f}", "img":"image/card11.gif"},
    ]

    cols = st.columns(len(cards))
    for idx, card in enumerate(cards):
        with cols[idx]:
            img_html = img_to_html(card["img"])
            st.markdown(f"""
                <div style="
                    border:1px solid #B0C4DE;
                    border-radius:10px;
                    padding:10px;
                    display:flex;
                    align-items:center;
                    background-color:#B0C4DE;">
                    {img_html}
                    <div><strong>{card['titulo']}</strong><br>{card['descricao']}</div>
                </div>
            """, unsafe_allow_html=True)

    # -------------------
    # Filtros na sidebar
    # -------------------
    st.sidebar.header("🔍 Filtros")

    # Datas
    min_data = df_recomendacoes['data_hora'].min().date()
    max_data = df_recomendacoes['data_hora'].max().date()
    periodo = st.sidebar.date_input("Período", [min_data, max_data])

    # Horários
    hora_ini = st.sidebar.time_input("Hora inicial", value=pd.to_datetime("00:00:00").time())
    hora_fim = st.sidebar.time_input("Hora final", value=pd.to_datetime("23:59:59").time())

    # Públicos
    todos_publicos = [
        'athletes',
        'children',
        'elderly',
        'generalPopulation',
        'heartDiseasePopulation',
        'lungDiseasePopulation',
        'pregnantWomen'
    ]
    publico_sel = st.sidebar.multiselect(
        "Público-alvo", 
        todos_publicos, 
        default=todos_publicos
    )

    # -------------------
    # Aplicar filtros de data, hora e público
    # -------------------
    from datetime import datetime
    start_datetime = datetime.combine(periodo[0], hora_ini)
    end_datetime = datetime.combine(periodo[1], hora_fim)

    mask = (
        (df_recomendacoes['data_hora'] >= start_datetime) &
        (df_recomendacoes['data_hora'] <= end_datetime) &
        (df_recomendacoes['publico_alvo'].isin(publico_sel))
    )
    df_filtrado = df_recomendacoes.loc[mask]

    # -------------------
    # Últimas recomendações
    # -------------------
    st.subheader("✨ Últimas Recomendações")

    # Criar dicionário com a última recomendação de cada público
    ultimas_dict = {}
    for publico in publico_sel:
        df_pub = df_filtrado[df_filtrado['publico_alvo'] == publico]
        if not df_pub.empty:
            ultimas_dict[publico] = df_pub.sort_values('data_hora', ascending=False).iloc[0]
        else:
            ultimas_dict[publico] = {'data_hora': None, 'recomendacao': "Sem recomendação disponível"}

    # Exibir todas as recomendações
    for publico in publico_sel:
        row = ultimas_dict[publico]
        st.markdown(f"""
            <div style="border:1px solid #ddd; border-radius:8px; padding:8px; margin-bottom:5px; background:#f9f9f9;">
                <strong>{publico}</strong> — <em>{row['data_hora'] if row['data_hora'] else ''}</em><br>
                {row['recomendacao']}
            </div>
        """, unsafe_allow_html=True)

# -------------------------------
# Página Poluentes
elif selected == "Poluentes":
    st.title("💨 Poluentes")
    df = dfs['poluentes']

    if not df.empty:
        fig = px.bar(df, x="nome", y="valor", color="unidade", title="Concentração por Poluente")
        st.plotly_chart(fig, use_container_width=True)
