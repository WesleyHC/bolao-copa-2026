import pandas as pd
import streamlit as st
import plotly.express as px
import datetime

st.set_page_config(
    page_title="Copa do Mundo 2026 - Bolão M02",
    page_icon="⚽️",
    layout="wide",
)

def sigla_para_bandeira(sigla):
    if not isinstance(sigla, str) or len(sigla) != 2:
        return sigla
    sigla = sigla.upper()
    bandeira = chr(ord(sigla[0]) + 127397) + chr(ord(sigla[1]) + 127397)
    return bandeira

def calculo_pontuacao(resultado_real, resultado_chutado):
    if pd.isna(resultado_real) or pd.isna(resultado_chutado):
        return 0
    try:
        gol_m_real, gol_v_real = map(int, str(resultado_real).lower().split("x"))
        gol_m_chutado, gol_v_chutado = map(int, str(resultado_chutado).lower().split("x"))
    except Exception:
        return 0
    
    if gol_m_real == gol_m_chutado and gol_v_real == gol_v_chutado:
        return 10
    
    saldo_real = gol_m_real - gol_v_real
    saldo_chutado = gol_m_chutado - gol_v_chutado

    vencedor_real = 1 if saldo_real > 0 else (-1 if saldo_real < 0 else 0)
    vencedor_chutado = 1 if saldo_chutado > 0 else (-1 if saldo_chutado < 0 else 0)

    if vencedor_real == vencedor_chutado:
        if vencedor_real == 0:
            return 4
        elif saldo_real == saldo_chutado:
            return 6
        else:
            return 4
    else:
        if gol_m_real == gol_m_chutado or gol_v_real == gol_v_chutado:
            return 0
            
    return 0

mapa_siglas = {
    "Alemanha": "DE", "Argentina": "AR", "AustrAlia": "AU", "Belgica": "BE",
    "Brasil": "BR", "Camaroes": "CM", "Canada": "CA", "Catar": "QA",
    "Coreia do Sul": "KR", "Costa Rica": "CR", "Croacia": "HR", "Dinamarca": "DK",
    "Equador": "EC", "Espanha": "ES", "Estados Unidos": "US", "França": "FR",
    "Gana": "GH", "Holanda": "NL", "Inglaterra": "GB", "Ira": "IR",
    "Japao": "JP", "Marrocos": "MA", "Mexico": "MX", "Pais de Gales": "GB", 
    "Polonia": "PL", "Portugal": "PT", "Senegal": "SN", "Servia": "RS",
    "Suiça": "CH", "Tunisia": "TN", "Uruguai": "UY", "Italia": "IT",
    "Colombia": "CO", "Chile": "CL", "Peru": "PE"
}

jogadores = {
    "Arthur": "Chutes_Art",
    "Coelho": "Chutes_Cu",
    "Feto": "Chutes_Feto",
    "MC": "Chutes_MC",
    "HC": "Chutes_HC"
}

if "df" not in st.session_state:
    df_temp = pd.read_csv("df.csv")
    
    def add_bandeira(nome):
        if pd.notna(nome) and nome in mapa_siglas:
            sigla = mapa_siglas[nome]
            return f"{nome} {sigla_para_bandeira(sigla)}"
        return nome

    df_temp["Equipe_Mandante"] = df_temp["Equipe_Mandante"].apply(add_bandeira)
    df_temp["Equipe_Visitante"] = df_temp["Equipe_Visitante"].apply(add_bandeira)
    
    st.session_state.df = df_temp

st.title("⚽️ Copa do Mundo 2026 - Bolão M02")
st.markdown("Explore as partidas da Copa.")

edited_df = st.session_state.df.copy()
pontos = {"Arthur": 0, "Coelho": 0, "Feto": 0, "MC": 0, "HC": 0}

for nome, coluna_chute in jogadores.items():
    if coluna_chute in edited_df.columns and "Resultado" in edited_df.columns:
        pontos_por_jogo = edited_df.apply(lambda row: calculo_pontuacao(row["Resultado"], row[coluna_chute]), axis=1)
        pontos[nome] = pontos_por_jogo.sum()

st.divider()
st.subheader("🏆 Placar Geral")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Arthur", pontos["Arthur"])
col2.metric("Coelho", pontos["Coelho"])
col3.metric("Feto", pontos["Feto"])
col4.metric("MC", pontos["MC"])
col5.metric("HC", pontos["HC"])
st.divider()
st.subheader("📅 Jogos de hoje")
data_hoje = datetime.date.today().strftime("%Y-%m-%d")
jogos_hoje = st.session_state.df[st.session_state.df["Data"] == data_hoje]
if jogos_hoje.empty:
    st.info(f"Nenhum jogo programado para hoje ({data_hoje}).")
else:
    for index, jogo in jogos_hoje.iterrows():
        col_casa, col_placar, col_fora = st.columns([2, 1, 2])
        
        with col_casa:
            st.markdown(f"<h3 style='text-align: right;'>{jogo['Equipe_Mandante']}</h3>", unsafe_allow_html=True)
            
        with col_placar:
            resultado = jogo['Resultado'] if pd.notna(jogo['Resultado']) else " X "
            st.markdown(f"<h2 style='text-align: center; color: #1E90FF;'>{resultado}</h2>", unsafe_allow_html=True)
        with col_fora:
            st.markdown(f"<h3 style='text-align: left;'>{jogo['Equipe_Visitante']}</h3>", unsafe_allow_html=True)
        st.divider()