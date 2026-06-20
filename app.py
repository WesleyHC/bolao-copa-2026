import pandas as pd
import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="Copa do Mundo 2026 - Bolão M02",
    page_icon="⚽️",
    layout="wide",
)

usuarios = {
    "arthur": {"senha": "arthur123", "coluna": "Chutes_Art", "nome": "Arthur"},
    "coelho": {"senha": "coelho123", "coluna": "Chutes_Cu", "nome": "Coelho"},
    "feto": {"senha": "feto123", "coluna": "Chutes_Feto", "nome": "Feto"},
    "mc": {"senha": "mc123", "coluna": "Chutes_MC", "nome": "MC"},
    "hc": {"senha": "hczadas2209", "coluna": "Chutes_HC", "nome": "HC"},
}

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:

    st.title("🔐 Login do Bolão")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):

        if (
            usuario.lower() in usuarios
            and usuarios[usuario.lower()]["senha"] == senha
        ):
            st.session_state.logado = True
            st.session_state.usuario = usuario.lower()
            st.rerun()

        else:
            st.error("Usuário ou senha incorretos.")

    st.stop()

usuario_logado = st.session_state.usuario
coluna_jogador = usuarios[usuario_logado]["coluna"]
nome_jogador = usuarios[usuario_logado]["nome"]

def sigla_para_bandeira(sigla):
    if not isinstance(sigla, str) or len(sigla) != 2:
        return sigla

    sigla = sigla.upper()
    return chr(ord(sigla[0]) + 127397) + chr(ord(sigla[1]) + 127397)


def calculo_pontuacao(resultado_real, resultado_chutado):

    if pd.isna(resultado_real) or pd.isna(resultado_chutado):
        return 0

    try:
        gol_m_real, gol_v_real = map(
            int, str(resultado_real).lower().split("x")
        )

        gol_m_chutado, gol_v_chutado = map(
            int, str(resultado_chutado).lower().split("x")
        )

    except:
        return 0

    if (
        gol_m_real == gol_m_chutado
        and gol_v_real == gol_v_chutado
    ):
        return 10

    saldo_real = gol_m_real - gol_v_real
    saldo_chutado = gol_m_chutado - gol_v_chutado

    vencedor_real = (
        1 if saldo_real > 0
        else (-1 if saldo_real < 0 else 0)
    )

    vencedor_chutado = (
        1 if saldo_chutado > 0
        else (-1 if saldo_chutado < 0 else 0)
    )

    if vencedor_real == vencedor_chutado:

        if vencedor_real == 0:
            return 4

        elif saldo_real == saldo_chutado:
            return 6

        else:
            return 4

    else:

        if (
            gol_m_real == gol_m_chutado
            or gol_v_real == gol_v_chutado
        ):
            return 0

    return 0

mapa_siglas = {
    "Alemanha": "DE",
    "Argélia": "DZ",
    "Argentina": "AR",
    "Austrália": "AU",
    "Áustria": "AT",
    "Bélgica": "BE",
    "Brasil": "BR",
    "Camarões": "CM",
    "Canadá": "CA",
    "Catar": "QA",
    "Coréia do Sul": "KR",
    "Costa Rica": "CR",
    "Costa do Marfim": "CI",
    "Croácia": "HR",
    "Dinamarca": "DK",
    "Equador": "EC",
    "Espanha": "ES",
    "Estados Unidos": "US",
    "França": "FR",
    "Gana": "GH",
    "Haiti": "HT",
    "Holanda": "NL",
    "Inglaterra": "GB",
    "Irã": "IR",
    "Iraque": "IQ",
    "Japão": "JP",
    "Jordânia": "JO",
    "Marrocos": "MA",
    "México": "MX",
    "Noruega": "NO",
    "País de Gales": "GB",
    "Panamá": "PA",
    "Polônia": "PL",
    "Portugal": "PT",
    "RD Congo": "CD",
    "Senegal": "SN",
    "Sérvia": "RS",
    "Suíça": "CH",
    "Tunísia": "TN",
    "Uruguai": "UY",
    "Itália": "IT",
    "Colômbia": "CO",
    "Chile": "CL",
    "Peru": "PE",
    "Uzbequistão": "UZ",
    "África do Sul": "ZA",
    "Arábia Saudita": "SA",
    "Bósnia e Herzegovina": "BA",
    "Cabo Verde": "CV",
    "Curação": "CW",
    "Egito": "EG",
    "Escócia": "GB",
    "EUA": "US",
    "Nova Zelândia": "NZ",
    "Paraguai": "PY",
    "Suécia": "SE",
    "Tchéquia": "CZ",
    "Turquia": "TR",
}

jogadores = {
    "Arthur": "Chutes_Art",
    "Coelho": "Chutes_Cu",
    "Feto": "Chutes_Feto",
    "MC": "Chutes_MC",
    "HC": "Chutes_HC",
}

@st.cache_resource
def conectar_planilha():

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )

    cliente = gspread.authorize(creds)

    planilha = cliente.open_by_key(
        "1HEjaWHU-Oz9gECeBQvAxWczfvtuzqD4MruZ7doiHvkw"
    )

    return planilha.sheet1

sheet = conectar_planilha()

dados = sheet.get_all_records()

df_temp = pd.DataFrame(dados)

def add_bandeira_mandante(nome):
    if pd.notna(nome):
        nome_limpo = str(nome).strip().title()
        if nome_limpo in ["Coréia Do Sul", "Coreia Do Sul"]: nome_limpo = "Coréia do Sul"
        if nome_limpo == "País De Gales": nome_limpo = "País de Gales"
        if nome_limpo == "Costa Do Marfim": nome_limpo = "Costa do Marfim"
        if nome_limpo == "Rd Congo": nome_limpo = "RD Congo"
        if nome_limpo == "África Do Sul": nome_limpo = "África do Sul"
        if nome_limpo == "Bósnia E Herzegovina": nome_limpo = "Bósnia e Herzegovina"
        
        if nome_limpo in mapa_siglas:
            sigla = mapa_siglas[nome_limpo]
            return f"{nome_limpo} {sigla_para_bandeira(sigla)}" 
    return nome

def add_bandeira_visitante(nome):
    if pd.notna(nome):
        nome_limpo = str(nome).strip().title()
        if nome_limpo in ["Coréia Do Sul", "Coreia Do Sul"]: nome_limpo = "Coréia do Sul"
        if nome_limpo == "País De Gales": nome_limpo = "País de Gales"
        if nome_limpo == "Costa Do Marfim": nome_limpo = "Costa do Marfim"
        if nome_limpo == "Rd Congo": nome_limpo = "RD Congo"
        if nome_limpo == "África Do Sul": nome_limpo = "África do Sul"
        if nome_limpo == "Bósnia E Herzegovina": nome_limpo = "Bósnia e Herzegovina"
        
        if nome_limpo in mapa_siglas:
            sigla = mapa_siglas[nome_limpo]
            return f"{sigla_para_bandeira(sigla)} {nome_limpo}" 
    return nome

df_temp["Equipe_Mandante"] = df_temp["Equipe_Mandante"].apply(add_bandeira_mandante)
df_temp["Equipe_Visitante"] = df_temp["Equipe_Visitante"].apply(add_bandeira_visitante)

st.session_state.df = df_temp

col1, col2 = st.columns([8, 1])

with col1:
    st.title("⚽ Copa do Mundo 2026 - Bolão M02")
    st.write(f"Bem-vindo, **{nome_jogador}**!")

with col2:

    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()

edited_df = df_temp .copy()

pontos = {
    "Arthur": 0,
    "Coelho": 0,
    "Feto": 0,
    "MC": 0,
    "HC": 0,
}

for nome, coluna_chute in jogadores.items():

    if (
        coluna_chute in edited_df.columns
        and "Resultado" in edited_df.columns
    ):

        pontos_por_jogo = edited_df.apply(
            lambda row: calculo_pontuacao(
                row["Resultado"],
                row[coluna_chute]
            ),
            axis=1
        )

        pontos[nome] = pontos_por_jogo.sum()

st.divider()

aba_placar, aba_palpites, aba_galera, aba_admin = st.tabs(["🏆 Placar Geral", "🎯 Meus Palpites", "👥 Palpites da Galera", "⚙️ Admin"])

with aba_placar:
    st.subheader("🏆 Classificação")
    
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Arthur", pontos["Arthur"])
    c2.metric("Coelho", pontos["Coelho"])
    c3.metric("Feto", pontos["Feto"])
    c4.metric("MC", pontos["MC"])
    c5.metric("HC", pontos["HC"])

with aba_palpites:
    st.subheader("🎯 Meus Palpites de Hoje")
    
    fuso_br = ZoneInfo("America/Sao_Paulo")
    agora_br = datetime.datetime.now(fuso_br)
    data_hoje = agora_br.strftime("%Y-%m-%d")
    
    jogos_hoje = df_temp[df_temp["Data"] == data_hoje]

    if jogos_hoje.empty:
        st.info(f"Nenhum jogo programado para hoje ({data_hoje}).")
    else:
        with st.form("form_palpites"):
            novos_chutes = {}
            
            for index, jogo in jogos_hoje.iterrows():
                st.markdown(f"### {jogo['Equipe_Mandante']} x {jogo['Equipe_Visitante']}")
                jogo_ja_comecou = False
                
                if "Horario" in jogo and pd.notna(jogo["Horario"]):
                    try:
                        string_data_hora = f"{jogo['Data']} {str(jogo['Horario']).strip()}"
                        
                        data_hora_jogo = datetime.datetime.strptime(string_data_hora, "%Y-%m-%d %H:%M")
                        
                        data_hora_jogo = data_hora_jogo.replace(tzinfo=fuso_br)
                        
                        if agora_br >= data_hora_jogo:
                            jogo_ja_comecou = True
                    except:
                        pass
                
                if jogo_ja_comecou:
                    st.caption("🔒 **Jogo já iniciado ou encerrado.**")
                else:
                    st.caption(f"⏰ Horário do jogo: {jogo['Horario']}")

                chute_atual = jogo[coluna_jogador]
                
                try:
                    if pd.notna(chute_atual):
                        g1, g2 = map(int, str(chute_atual).split("x"))
                    else:
                        g1, g2 = 0, 0
                except:
                    g1, g2 = 0, 0

                col_a, col_b = st.columns(2)
                with col_a:
                    gol_casa = st.number_input("Mandante", min_value=0, max_value=20, value=g1, key=f"casa_{index}", disabled=jogo_ja_comecou)
                with col_b:
                    gol_fora = st.number_input("Visitante", min_value=0, max_value=20, value=g2, key=f"fora_{index}", disabled=jogo_ja_comecou)

                if not jogo_ja_comecou:
                    novos_chutes[index] = f"{gol_casa}x{gol_fora}"
                
                st.divider()

            salvar = st.form_submit_button("💾 Salvar Palpites")

            if salvar:
                if novos_chutes:
                    sheet = conectar_planilha()
                    for idx, chute in novos_chutes.items():
                        linha_planilha = idx + 2
                        coluna_planilha = st.session_state.df.columns.get_loc(coluna_jogador) + 1
                        sheet.update_cell(linha_planilha, coluna_planilha, chute)

                    st.success("Palpites enviados com sucesso!")
                    st.cache_resource.clear()
                    st.rerun()
                else:
                    st.warning("Todos os jogos de hoje já começaram. Não há palpites novos para salvar.")

with aba_galera:
    st.subheader("👥 Palpites da Galera")
    st.caption("Selecione a rodada para acompanhar os palpites e as pontuações dos jogos que já começaram ou terminaram.")

    fuso_br = ZoneInfo("America/Sao_Paulo")
    agora_br = datetime.datetime.now(fuso_br)

    indices_jogos_iniciados = []
    
    for index, jogo in df_temp.iterrows():
        jogo_ja_comecou = False
        
        resultado_oficial = jogo.get("Resultado", "")
        tem_resultado = pd.notna(resultado_oficial) and str(resultado_oficial).strip() != ""
        
        if tem_resultado:
            jogo_ja_comecou = True
        elif "Horario" in jogo and pd.notna(jogo["Horario"]) and "Data" in jogo and pd.notna(jogo["Data"]):
            try:
                string_data_hora = f"{jogo['Data']} {str(jogo['Horario']).strip()}"
                data_hora_jogo = datetime.datetime.strptime(string_data_hora, "%Y-%m-%d %H:%M").replace(tzinfo=fuso_br)
                
                if agora_br >= data_hora_jogo:
                    jogo_ja_comecou = True
            except:
                pass
        
        if jogo_ja_comecou:
            indices_jogos_iniciados.append(index)

    df_iniciados = df_temp.loc[indices_jogos_iniciados]

    if df_iniciados.empty:
        st.info("🔒 Nenhum jogo começou ou foi encerrado ainda. Os palpites dos adversários serão revelados assim que as partidas iniciarem!")
    
    else:
        coluna_rodada = "Fase" if "Fase" in df_iniciados.columns else ("Fase" if "Fase" in df_iniciados.columns else None)
        
        if coluna_rodada:
            rodadas_disponiveis = sorted(df_iniciados[coluna_rodada].unique())
            rodada_selecionada = st.selectbox("📊 Filtrar por Rodada:", rodadas_disponiveis, key="seletor_rodadas")
            
            jogos_para_exibir = df_iniciados[df_iniciados[coluna_rodada] == rodada_selecionada].copy()
        else:
            st.warning("Aviso: Coluna 'Fase' não foi encontrada no Google Sheets.")
            jogos_para_exibir = df_iniciados.copy()

        def verifica_se_acabou(resultado):
            return pd.notna(resultado) and str(resultado).strip() != ""
            
        jogos_para_exibir["_encerrado"] = jogos_para_exibir["Resultado"].apply(verifica_se_acabou)
        
        jogos_para_exibir = jogos_para_exibir.sort_values(by=["_encerrado"], ascending=True)
        
        for index, jogo in jogos_para_exibir.iterrows():
            st.markdown(f"### {jogo['Equipe_Mandante']} x {jogo['Equipe_Visitante']}")
            
            resultado_oficial = jogo.get("Resultado", "")
            tem_resultado = pd.notna(resultado_oficial) and str(resultado_oficial).strip() != ""

            if tem_resultado:
                st.markdown(f"Placar oficial: **{resultado_oficial}**")
            else:
                st.caption(f"📅 Data: {jogo['Data']} | ⏰ Horário: {jogo.get('Horario', '-')} | 🟢 **Em andamento**")

            cols_profs = st.columns(5)
            
            participantes = [
                ("Arthur", "Chutes_Art"),
                ("Coelho", "Chutes_Cu"),
                ("Feto", "Chutes_Feto"),
                ("MC", "Chutes_MC"),
                ("HC", "Chutes_HC")
            ]

            for i, (nome_part, col_part) in enumerate(participantes):
                with cols_profs[i]:
                    valor_chute = jogo[col_part] if pd.notna(jogo[col_part]) and str(jogo[col_part]).strip() != "" else "-"
                    
                    if tem_resultado and valor_chute != "-":
                        pontos_ganhos = calculo_pontuacao(resultado_oficial, valor_chute)
                        cor = "normal" if pontos_ganhos > 0 else "off"
                        
                        st.metric(
                            label=nome_part, 
                            value=str(valor_chute), 
                            delta=f"{pontos_ganhos} pts", 
                            delta_color=cor
                        )
                    else:
                        st.metric(label=nome_part, value=str(valor_chute))
            
            st.divider()
            
with aba_admin:
    if usuario_logado == "hc": 
        st.subheader("⚙️ Atualizar Resultados Oficiais")
        st.warning("Área restrita. As alterações feitas aqui impactam o placar de todos os jogadores.")
        
        df_admin = df_temp[['Data', 'Equipe_Mandante', 'Equipe_Visitante', 'Resultado']].copy()
        
        df_editado_admin = st.data_editor(
            df_admin,
            disabled=["Data", "Equipe_Mandante", "Equipe_Visitante"],
            key="editor_admin"
        )
        
        if st.button("Salvar Resultados no Banco de Dados"):
            sheet = conectar_planilha()
            coluna_resultado = st.session_state.df.columns.get_loc("Resultado") + 1
            alteracoes_feitas = 0
            
            for index, row in df_editado_admin.iterrows():
                resultado_velho = df_admin.loc[index, 'Resultado']
                resultado_novo = row['Resultado']
                
                if str(resultado_velho) != str(resultado_novo):
                    linha_planilha = index + 2
                    sheet.update_cell(linha_planilha, coluna_resultado, resultado_novo)
                    alteracoes_feitas += 1
            
            if alteracoes_feitas > 0:
                st.success(f"{alteracoes_feitas} resultado(s) atualizado(s) com sucesso!")
                st.cache_resource.clear()
                st.rerun()
            else:
                st.info("Nenhuma alteração detectada para salvar.")
    else:
        st.error("Você não tem permissão para acessar esta área.")
