import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import random

# Configurar título e logo (deve ser a primeira chamada de Streamlit)
st.set_page_config(page_title="Plataforma Minsait", page_icon=":guardsman:", layout="wide")

# Carregar dados com cache para evitar recarregamentos desnecessários
@st.cache_data
def load_data():
    df = pd.read_csv('dataframe.csv')
    geojson_path = 'saopaulo_distritos_poligonos.geojson'  # Altere este caminho conforme necessário
    gdf_regions = gpd.read_file(geojson_path)
    return df, gdf_regions

df, gdf_regions = load_data()

st.image("https://cdn3.bonitasoft.com/sites/default/files/minsait_2.png", width=200)

# Título da aplicação
st.title("Plataforma Minsait")

# Menu de navegação
st.sidebar.title("Navegação")
option = st.sidebar.selectbox("Selecione a seção", ["Portal do Candidato", "Plataforma Administrativa"])

# Portal do Candidato
if option == "Portal do Candidato":
    st.header("Portal do Candidato")
    st.write("Insira seus dados abaixo:")

    # Formulário de entrada de dados do candidato
    nome = st.text_input("Nome")
    idade = st.number_input("Idade", min_value=18, max_value=100, step=1)
    email = st.text_input("Email")
    telefone = st.text_input("Telefone")
    cidade = st.text_input("Cidade")

    if st.button("Enviar"):
        st.success(f"Dados enviados com sucesso! Nome: {nome}, Idade: {idade}, Email: {email}, Telefone: {telefone}, Cidade: {cidade}")

# Plataforma Administrativa
elif option == "Plataforma Administrativa":
    st.header("Plataforma Administrativa")
    st.write("Dados dos candidatos cadastrados:")

    # Remover a coluna 'id' do DataFrame antes de exibi-lo
    df_display = df.drop(columns=['id'], errors='ignore')

    # Exibir dados em tabela sem a coluna de índice
    st.dataframe(df_display.reset_index(drop=True))

    # Detalhes do candidato
    candidato_selecionado = st.selectbox("Selecione um candidato", df['Nome_Completo'].unique())

    if candidato_selecionado:
        detalhes_candidato = df[df['Nome_Completo'] == candidato_selecionado]
        st.write(detalhes_candidato)

        # Verificar se o candidato selecionado possui coordenadas e score
        if 'Latitude' in detalhes_candidato.columns and 'Longitude' in detalhes_candidato.columns:
            try:
                latitude = float(detalhes_candidato['Latitude'].values[0])
                longitude = float(detalhes_candidato['Longitude'].values[0])
                score = detalhes_candidato['Score_Final'].values[0] if 'Score_Final' in detalhes_candidato.columns else 'N/A'
            except ValueError:
                st.error("Coordenadas inválidas.")
        else:
            st.error("Coordenadas não encontradas.")

        # Adicionar mapa de risco
        st.header("Mapa de Risco")

        # Adicionar uma coluna 'id' ao GeoDataFrame se não existir
        if 'id' not in gdf_regions.columns:
            gdf_regions = gdf_regions.reset_index().rename(columns={'index': 'id'})

        # Simulando áreas de tráfico, mas com cache para evitar simulações repetidas
        @st.cache_data
        def generate_area_trafico():
            return [random.randrange(0, 100) for _ in range(len(gdf_regions))]

        area_trafico = generate_area_trafico()

        # Adicionar áreas de tráfico ao GeoDataFrame
        gdf_regions['area_trafico'] = area_trafico

        # Criação do mapa com folium, centralizado em São Paulo
        m = folium.Map(location=[-23.550520, -46.633308], zoom_start=12)

        # Adicionar coroplético ao mapa
        folium.Choropleth(
            geo_data=gdf_regions,
            name="choropleth",
            data=gdf_regions,
            columns=["id", "area_trafico"],
            key_on="feature.properties.id",
            fill_color="YlOrRd",
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name="Área de Tráfico"
        ).add_to(m)

        # Adicionar marcador para o candidato selecionado
        if 'Latitude' in detalhes_candidato.columns and 'Longitude' in detalhes_candidato.columns:
            popup_text = f"{candidato_selecionado}<br>Score: {score}"
            folium.Marker(
                location=[latitude, longitude],
                popup=popup_text,
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)

            # Adicionar uma camada de pontos de interesse para garantir que o marcador seja visível
            folium.CircleMarker(
                location=(latitude, longitude),
                radius=10,
                color='blue',
                fill=True,
                fill_color='blue'
            ).add_to(m)

        # Adicionar controle de camadas
        folium.LayerControl().add_to(m)

        # Mostrar o mapa
        st_folium(m, width=700, height=500)
