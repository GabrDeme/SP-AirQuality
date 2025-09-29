import streamlit as st
from streamlit_option_menu import option_menu
from query import connection
import pandas as pd
import plotly.express as px
from pathlib import Path
import base64
import datetime as dt

# -------------------------------
st.set_page_config(page_title="SP-AirQuality Dashboard", layout="wide")

# -------------------------------
# Função para carregar dados com cache
@st.cache_data
def load_data(query):
    return connection(query)

# -------------------------------
# Queries
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
# Carregar dados inicialmente
dfs = {key: load_data(q) for key, q in queries.items()}

# Botão para atualizar todos os dados
if st.sidebar.button("🔄 Atualizar Dados"):
    dfs = carregar_todas_tabelas()

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
# Menu lateral (uma única vez)
with st.sidebar:
    selected = option_menu(
        menu_title="Menu",
        options=["Página Inicial", "Leituras", "Qualidade", "Hospitais", "Acompanhamento"],
        icons=["house", "wind", "bar-chart-line", "hospital","activity"],
        menu_icon="cast",
        default_index=0,
        key="menu_lateral"
    )

# -------------------------------
# Página Inicial
if selected == "Página Inicial":
    st.title("🌬️ SP-AirQuality Dashboard")
    st.subheader(
        "O sistema de monitoramento da qualidade do ar tem como objetivo proteger a saúde da população 👩‍👩‍👧‍👦🌱, fornecendo dados em tempo real sobre poluentes atmosféricos e condições ambientais. "
        "Com isso, busca prevenir doenças respiratórias e cardiovasculares 🫁❤️ e oferecer alertas para grupos vulneráveis 👶👵."
    )

    query = """
    SELECT l.idLeitura, l.data_hora, l.co2, l.umidade, l.pressao, l.temperatura, q.aqi, q.category, q.poluenteDominante
    FROM tb_leituras l
    LEFT JOIN tb_qualidade q ON l.idLeitura = q.idLeitura
    """
    df = load_data(query)
    df['data_hora'] = pd.to_datetime(df['data_hora'])
    
    if not df.empty:
        ultimo = df.sort_values('data_hora', ascending=True).iloc[-1]
        total_leituras = len(df)
        aqi = ultimo['aqi'] if not pd.isna(ultimo['aqi']) else 0
        co2 = ultimo['co2'] if not pd.isna(ultimo['co2']) else 0
        temp = ultimo['temperatura'] if not pd.isna(ultimo['temperatura']) else 0
    else:
        total_leituras = aqi = co2 = temp = 0

    cards = [
        {"titulo": "Total Leituras", "descricao": total_leituras, "img": "image/card10.gif"},
        {"titulo": "AQI", "descricao": f"{aqi:.1f}", "img": "image/card11.gif"},
        {"titulo": "CO₂ (ppm)", "descricao": f"{co2:.2f}", "img": "image/card8.gif"},
        {"titulo": "Temp. (°C)", "descricao": f"{temp:.2f}", "img": "image/card3.gif"}
    ]

    cols = st.columns(len(cards))
    for idx, card in enumerate(cards):
        with cols[idx]:
            img_html = img_to_html(card["img"])
            st.markdown(f"""
            <div style=" border:1px solid #000000; border-radius:10px; padding:10px; display:flex; align-items:center; background-color:#B0C4DE;">
                {img_html}
                <div><strong>{card['titulo']}</strong><br>{card['descricao']}</div>
            </div>
            """, unsafe_allow_html=True)

# -------------------------------
# Página Leituras
elif selected == "Leituras":
    st.title("📊 Dados coletados via dispositivo")
    st.subheader(
        "Realizar a coleta de dados da qualidade do ar por meio de um dispositivo desenvolvido por alunos e professores do SENAI 🏫🤝. "
        "O equipamento capta informações ambientais 🌱🌍 e envia via Wi-Fi 📡 para um banco de dados centralizado 💾, permitindo análise em tempo real."
    )

    # --- Carregar dados ---
    df = dfs['leituras'].copy()
    df['data_hora'] = pd.to_datetime(df['data_hora'])

    # --- Últimos valores ---
    if not df.empty:
        ultimo = df.sort_values('data_hora').iloc[-1]
        qtd_leituras = len(df)
        co2 = ultimo['co2'] if not pd.isna(ultimo['co2']) else 0
        umidade = ultimo['umidade'] if not pd.isna(ultimo['umidade']) else 0
        temp = ultimo['temperatura'] if not pd.isna(ultimo['temperatura']) else 0
    else:
        qtd_leituras = co2 = umidade = temp = 0

    # --- Cards ---
    cards = [
        {"titulo": "Qtd Leituras", "descricao": qtd_leituras, "img": "image/card10.gif"},
        {"titulo": "CO₂ Atual", "descricao": f"{co2:.2f}", "img": "image/card8.gif"},
        {"titulo": "Umidade Atual", "descricao": f"{umidade:.2f}", "img": "image/card2.gif"},
        {"titulo": "Temperatura Atual", "descricao": f"{temp:.2f}", "img": "image/card3.gif"},
    ]

    cols = st.columns(len(cards))
    for idx, card in enumerate(cards):
        with cols[idx]:
            img_html = img_to_html(card["img"])
            st.markdown(f"""
            <div style="border:1px solid #B0C4DE; border-radius:10px; padding:10px; display:flex; align-items:center; background-color:#B0C4DE;">
                {img_html}
                <div><strong>{card['titulo']}</strong><br>{card['descricao']}</div>
            </div>
            """, unsafe_allow_html=True)

    # --- Filtros na sidebar ---
    st.sidebar.header("🔍 Filtros")
    min_data = df['data_hora'].dt.date.min()
    max_data = df['data_hora'].dt.date.max()
    selected_range = st.sidebar.date_input("Período", [min_data, max_data], min_value=min_data, max_value=max_data)
    
    start_date, end_date = (selected_range[0], selected_range[1]) if len(selected_range) == 2 else (selected_range[0], selected_range[0])
    
    start_time, end_time = st.sidebar.slider(
        "Faixa de horário",
        value=(dt.time(0,0), dt.time(23,59)),
        format="HH:mm"
    )

    # --- Filtra leituras ---
    mask = (
        (df['data_hora'].dt.date >= start_date) &
        (df['data_hora'].dt.date <= end_date) &
        (df['data_hora'].dt.time >= start_time) &
        (df['data_hora'].dt.time <= end_time)
    )
    df_filtered = df[mask].copy()

    # Formata data_hora para exibir nos gráficos
    if not df_filtered.empty:
        df_filtered['data_hora_str'] = df_filtered['data_hora'].dt.strftime('%d/%m/%Y %H:%M')

    # --- Gráficos individuais ---
    st.subheader("🔍 Análises individuais")
    col1, col2, col3 = st.columns(3)

    with col1:
        if not df_filtered.empty:
            fig_temp = px.line(df_filtered, x="data_hora_str", y="temperatura", title="Temperatura (°C)")
            st.plotly_chart(fig_temp, use_container_width=True)
        else:
            st.info("Nenhum dado de temperatura disponível para o período selecionado.")

    with col2:
        if not df_filtered.empty:
            fig_co2 = px.line(df_filtered, x="data_hora_str", y="co2", title="CO₂ (ppm)", color_discrete_sequence=['red'])
            st.plotly_chart(fig_co2, use_container_width=True)
        else:
            st.info("Nenhum dado de CO₂ disponível para o período selecionado.")

    with col3:
        if not df_filtered.empty:
            fig_umid = px.line(df_filtered, x="data_hora_str", y="umidade", title="Umidade (%)", color_discrete_sequence=['blue'])
            st.plotly_chart(fig_umid, use_container_width=True)
        else:
            st.info("Nenhum dado de umidade disponível para o período selecionado.")

    # --- Gráficos comparativos e poluentes ---
    st.subheader("🔍 Comparativo de Variáveis e Poluentes")
    col4, col5 = st.columns(2)

    with col4:
        if not df_filtered.empty:
            fig_comp = px.line(
                df_filtered,
                x="data_hora_str",
                y=["temperatura", "co2", "umidade"],
                labels={"value":"Medida","variable":"Variável"},
                title="Comparativo de Leituras"
            )
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("Nenhum dado disponível para o comparativo de variáveis no período selecionado.")

    with col5:
        df_poluentes = dfs["poluentes"].copy()
        df_leituras = dfs["leituras"][["idLeitura","data_hora"]].copy()
        df_poluentes = df_poluentes.merge(df_leituras, on="idLeitura", how="left")
        df_poluentes['data_hora'] = pd.to_datetime(df_poluentes['data_hora'])

        mask_pol = (
            (df_poluentes['data_hora'].dt.date >= start_date) &
            (df_poluentes['data_hora'].dt.date <= end_date) &
            (df_poluentes['data_hora'].dt.time >= start_time) &
            (df_poluentes['data_hora'].dt.time <= end_time)
        )
        df_poluentes_filtered = df_poluentes[mask_pol]

        if not df_poluentes_filtered.empty:
            fig_pol = px.bar(
                df_poluentes_filtered,
                y="nome",
                x="valor",
                color="unidade",
                orientation="h",
                title="Concentração por Poluente"
            )
            st.plotly_chart(fig_pol, use_container_width=True)
        else:
            st.info("Nenhum dado de poluentes disponível para o período selecionado.")

# -------------------------------
# Página Qualidade
elif selected == "Qualidade":
    st.title("📈 Qualidade do Ar")

    df_qualidade = dfs['qualidade'].copy()
    df_leituras = dfs['leituras'][['idLeitura','data_hora']].copy()
    df_recomendacoes = dfs['recomendacoes'].copy()

    # Merge para trazer timestamp das leituras
    df_qualidade = df_qualidade.merge(df_leituras, on='idLeitura', how='left')
    df_recomendacoes = df_recomendacoes.merge(df_leituras, on='idLeitura', how='left')

    df_qualidade['data_hora'] = pd.to_datetime(df_qualidade['data_hora'])
    df_recomendacoes['data_hora'] = pd.to_datetime(df_recomendacoes['data_hora'])

    # Últimos valores
    if not df_qualidade.empty:
        ultimo = df_qualidade.sort_values('data_hora').iloc[-1]
        qtd_registros = len(df_qualidade)
        aqi = ultimo['aqi'] if not pd.isna(ultimo['aqi']) else 0
        co2 = ultimo['co2'] if 'co2' in ultimo and not pd.isna(ultimo['co2']) else 0
        temp = ultimo['temperatura'] if 'temperatura' in ultimo and not pd.isna(ultimo['temperatura']) else 0
    else:
        qtd_registros = aqi = co2 = temp = 0

    # Cards
    cards = [
        {"titulo":"Qtd Registros", "descricao": qtd_registros, "img":"image/card10.gif"},
        {"titulo":"AQI Atual", "descricao": f"{aqi:.1f}", "img":"image/card11.gif"},
        {"titulo":"CO₂ Atual", "descricao": f"{co2:.2f}", "img":"image/card8.gif"},
        {"titulo":"Temperatura Atual", "descricao": f"{temp:.2f}", "img":"image/card3.gif"}
    ]

    cols = st.columns(len(cards))
    for idx, card in enumerate(cards):
        with cols[idx]:
            img_html = img_to_html(card["img"])
            st.markdown(f"""
            <div style="border:1px solid #B0C4DE; border-radius:10px; padding:10px; display:flex; align-items:center; background-color:#B0C4DE;">
                {img_html}
                <div><strong>{card['titulo']}</strong><br>{card['descricao']}</div>
            </div>
            """, unsafe_allow_html=True)

    # --- Filtros de período na sidebar ---
    st.sidebar.header("🔍 Filtros")
    min_data = df_recomendacoes['data_hora'].min().date()
    max_data = df_recomendacoes['data_hora'].max().date()
    periodo = st.sidebar.date_input("Período", [min_data, max_data])
    start_date, end_date = periodo if len(periodo)==2 else (periodo[0], periodo[0])

    start_time, end_time = st.sidebar.slider(
        "Faixa de horário",
        value=(dt.time(0,0), dt.time(23,59)),
        format="HH:mm"
    )

    start_datetime = dt.datetime.combine(start_date, start_time)
    end_datetime = dt.datetime.combine(end_date, end_time)

    # Filtra recomendações
    mask = ((df_recomendacoes['data_hora'] >= start_datetime) & 
            (df_recomendacoes['data_hora'] <= end_datetime))
    df_filtrado = df_recomendacoes.loc[mask].copy()

    # Formata data_hora para exibição
    if not df_filtrado.empty:
        df_filtrado['data_hora_str'] = df_filtrado['data_hora'].dt.strftime('%d/%m/%Y %H:%M')

    st.subheader("✨ Últimas Recomendações")

    if not df_filtrado.empty:
        # Obtém os últimos registros por público
        ultimas_dict = {}
        for publico in df_filtrado['publico_alvo'].unique():
            df_pub = df_filtrado[df_filtrado['publico_alvo'] == publico]
            ultimas_dict[publico] = df_pub.sort_values('data_hora', ascending=False).iloc[0]

        for publico, row in ultimas_dict.items():
            st.markdown(f"""
            <div style="border:1px solid #ddd; border-radius:8px; padding:8px; margin-bottom:5px; background:#f9f9f9;">
                <strong>{publico}</strong> — <em>{row['data_hora_str']}</em><br>
                {row['recomendacao']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhuma recomendação disponível para o período selecionado.")

# -------------------------------
# Aba Hospitais
elif selected == "Hospitais":
    st.title("🏥 Hospitais Próximos")
    st.subheader("Digite seu CEP para encontrar os hospitais mais próximos")

    # Campo para digitar o CEP
    cep = st.text_input("CEP:", placeholder="00000-000")

    # Dados fictícios de hospitais
    hospital_data = pd.DataFrame({
        'Nome': ['Hospital A', 'Hospital B', 'Hospital C'],
        'CEP': ['01001-000', '01002-000', '01003-000'],
        'Latitude': [-23.55052, -23.5629, -23.5645],
        'Longitude': [-46.633308, -46.6544, -46.6522]
    })

    if st.button("Buscar hospitais"):
        if cep:
            # Filtra hospitais pelo CEP exato ou próximo
            hospitais_proximos = hospital_data[hospital_data['CEP'].str.startswith(cep[:5])]

            if not hospitais_proximos.empty:
                st.markdown("### Hospitais encontrados:")
                st.dataframe(hospitais_proximos[['Nome', 'CEP']])

                # Mostra no mapa
                st.subheader("Mapa dos Hospitais Próximos")
                st.map(hospitais_proximos.rename(columns={'Latitude':'lat', 'Longitude':'lon'}))
            else:
                st.warning("Nenhum hospital encontrado próximo ao CEP informado.")
        else:
            st.error("Por favor, informe um CEP válido.")

# -------------------------------
# Aba Acompanhamento
elif selected == "Acompanhamento":
    st.title("📧 Acompanhamento de Notícias")
    st.subheader("Receba alertas e informações sobre a qualidade do ar diretamente no seu e-mail.")

    email = st.text_input("Digite seu e-mail:", placeholder="exemplo@empresa.com")
    if st.button("Inscrever"):
        if email:
            st.success(f"E-mail '{email}' registrado com sucesso! ✅")
        else:
            st.error("Por favor, insira um e-mail válido.")