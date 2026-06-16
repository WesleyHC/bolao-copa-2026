import pandas as pd
import streamlit as st
import datetime

st.set_page_config(
    page_title="Copa do Mundo 2026 - Bolão M02",
    page_icon="⚽️",
    layout="wide",
)

# =========================
# LOGIN
# =========================

usuarios = {
    "arthur": {"senha": "arthur123", "coluna": "Chutes_Art", "nome": "Arthur"},
    "coelho": {"senha": "coelho123", "coluna": "Chutes_Cu", "nome": "Coelho"},
    "feto": {"senha": "feto123", "coluna": "Chutes_Feto", "nome": "Feto"},
    "mc": {"senha": "mc123", "coluna": "Chutes_MC", "nome": "MC"},
    "hc": {"senha": "hc123", "coluna": "Chutes_HC", "nome": "HC"},
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
            return 2

    return 0


# =========================
# BANDEIRAS
# =========================

mapa_siglas = {
    "Alemanha": "DE",
    "Argentina": "AR",
    "AustrAlia": "AU",
    "Belgica": "BE",
    "Brasil": "BR",
    "Camaroes": "CM",
    "Canada": "CA",
    "Catar": "QA",
    "Coreia do Sul": "KR",
    "Costa Rica": "CR",
    "Croacia": "HR",
    "Dinamarca": "DK",
    "Equador": "EC",
    "Espanha": "ES",
    "Estados Unidos": "US",
    "França": "FR",
    "Gana": "GH",
    "Holanda": "NL",
    "Inglaterra": "GB",
    "Ira": "IR",
    "Japao": "JP",
    "Marrocos": "MA",
    "Mexico": "MX",
    "Pais de Gales": "GB",
    "Polonia": "PL",
    "Portugal": "PT",
    "Senegal": "SN",
    "Servia": "RS",
    "Suiça": "CH",
    "Tunisia": "TN",
    "Uruguai": "UY",
    "Italia": "IT",
    "Colombia": "CO",
    "Chile": "CL",
    "Peru": "PE",
}

jogadores = {
    "Arthur": "Chutes_Art",
    "Coelho": "Chutes_Cu",
    "Feto": "Chutes_Feto",
    "MC": "Chutes_MC",
    "HC": "Chutes_HC",
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

col1, col2 = st.columns([8, 1])

with col1:
    st.title("⚽ Copa do Mundo 2026 - Bolão M02")
    st.write(f"Bem-vindo, **{nome_jogador}**!")

with col2:

    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()

edited_df = st.session_state.df.copy()

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

st.subheader("🏆 Placar Geral")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Arthur", pontos["Arthur"])
c2.metric("Coelho", pontos["Coelho"])
c3.metric("Feto", pontos["Feto"])
c4.metric("MC", pontos["MC"])
c5.metric("HC", pontos["HC"])

st.divider()
st.subheader("🎯 Meus Palpites de Hoje")

data_hoje = datetime.date.today().strftime("%Y-%m-%d")

jogos_hoje = st.session_state.df[
    st.session_state.df["Data"] == data_hoje
]

if jogos_hoje.empty:

    st.info(
        f"Nenhum jogo programado para hoje ({data_hoje})."
    )

else:

    with st.form("form_palpites"):

        novos_chutes = {}

        for index, jogo in jogos_hoje.iterrows():

            st.markdown(
                f"### {jogo['Equipe_Mandante']} x {jogo['Equipe_Visitante']}"
            )

            chute_atual = jogo[coluna_jogador]

            try:

                if pd.notna(chute_atual):
                    g1, g2 = map(
                        int,
                        str(chute_atual).split("x")
                    )
                else:
                    g1, g2 = 0, 0

            except:
                g1, g2 = 0, 0

            col_a, col_b = st.columns(2)

            with col_a:

                gol_casa = st.number_input(
                    "Mandante",
                    min_value=0,
                    max_value=20,
                    value=g1,
                    key=f"casa_{index}"
                )

            with col_b:

                gol_fora = st.number_input(
                    "Visitante",
                    min_value=0,
                    max_value=20,
                    value=g2,
                    key=f"fora_{index}"
                )

            novos_chutes[index] = f"{gol_casa}x{gol_fora}"

            st.divider()

        salvar = st.form_submit_button(
            "💾 Salvar Palpites"
        )

        if salvar:

            for idx, chute in novos_chutes.items():
                st.session_state.df.loc[
                    idx,
                    coluna_jogador
                ] = chute

            st.session_state.df.to_csv(
                "df.csv",
                index=False
            )

            st.success(
                "Palpites salvos com sucesso!"
            )

            st.rerun()