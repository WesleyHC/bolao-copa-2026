import pandas as pd
import streamlit as st
import datetime
import time
import gspread
from google.oauth2.service_account import Credentials
from zoneinfo import ZoneInfo
import extra_streamlit_components as stx

st.set_page_config(
    page_title="Copa do Mundo 2026 - Bolão M02",
    page_icon="⚽️",
    layout="wide",
)

fuso_br = ZoneInfo("America/Sao_Paulo")

usuarios = {
    "arthur": {"senha": "arthur123", "coluna": "Chutes_Art",  "nome": "Arthur"},
    "coelho": {"senha": "coelho123", "coluna": "Chutes_Cu",   "nome": "Coelho"},
    "feto":   {"senha": "feto123",   "coluna": "Chutes_Feto", "nome": "Feto"},
    "mc":     {"senha": "mc123",     "coluna": "Chutes_MC",   "nome": "MC"},
    "hc":     {"senha": "hczadas2209","coluna": "Chutes_HC",  "nome": "HC"},
}

jogadores = {
    "Arthur": "Chutes_Art",
    "Coelho": "Chutes_Cu",
    "Feto":   "Chutes_Feto",
    "MC":     "Chutes_MC",
    "HC":     "Chutes_HC",
}

# ── Cookies ────────────────────────────────────────────────────────────────────
cookie_manager = stx.CookieManager(key="gerenciador_de_cookies_fixo")

if "logado" not in st.session_state:
    st.session_state.logado = False

todos_cookies = cookie_manager.get_all()
usuario_salvo = cookie_manager.get(cookie="usuario_bolao")

if usuario_salvo and not st.session_state.logado:
    if usuario_salvo in usuarios:
        st.session_state.logado = True
        st.session_state.usuario = usuario_salvo
        st.rerun()

# ── Login ──────────────────────────────────────────────────────────────────────
if not st.session_state.logado:
    st.title("🔐 Login do Bolão")
    usuario = st.text_input("Usuário")
    senha   = st.text_input("Senha", type="password")
    manter_login = st.checkbox("Manter conectado")

    if st.button("Entrar"):
        if usuario.lower() in usuarios and usuarios[usuario.lower()]["senha"] == senha:
            st.session_state.logado  = True
            st.session_state.usuario = usuario.lower()
            if manter_login:
                cookie_manager.set(
                    "usuario_bolao", usuario.lower(),
                    key="salvar_cookie", max_age=2592000
                )
                st.success("✅ Login efetuado com sucesso! Salvando conexão...")
                time.sleep(1.5)
                st.rerun()
            else:
                st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
    st.stop()

usuario_logado  = st.session_state.usuario
coluna_jogador  = usuarios[usuario_logado]["coluna"]
nome_jogador    = usuarios[usuario_logado]["nome"]

# ── Helpers ────────────────────────────────────────────────────────────────────
mapa_siglas = {
    "Alemanha": "DE", "Argélia": "DZ", "Argentina": "AR", "Austrália": "AU",
    "Áustria": "AT", "Bélgica": "BE", "Brasil": "BR", "Camarões": "CM",
    "Canadá": "CA", "Catar": "QA", "Coréia do Sul": "KR", "Costa Rica": "CR",
    "Costa do Marfim": "CI", "Croácia": "HR", "Dinamarca": "DK", "Equador": "EC",
    "Espanha": "ES", "Estados Unidos": "US", "França": "FR", "Gana": "GH",
    "Haiti": "HT", "Holanda": "NL", "Inglaterra": "GB", "Irã": "IR",
    "Iraque": "IQ", "Japão": "JP", "Jordânia": "JO", "Marrocos": "MA",
    "México": "MX", "Noruega": "NO", "País de Gales": "GB", "Panamá": "PA",
    "Polônia": "PL", "Portugal": "PT", "RD Congo": "CD", "Senegal": "SN",
    "Sérvia": "RS", "Suíça": "CH", "Tunísia": "TN", "Uruguai": "UY",
    "Itália": "IT", "Colômbia": "CO", "Chile": "CL", "Peru": "PE",
    "Uzbequistão": "UZ", "África do Sul": "ZA", "Arábia Saudita": "SA",
    "Bósnia e Herzegovina": "BA", "Cabo Verde": "CV", "Curação": "CW",
    "Egito": "EG", "Escócia": "GB", "EUA": "US", "Eua": "US",
    "Nova Zelândia": "NZ", "Paraguai": "PY", "Suécia": "SE",
    "Tchéquia": "CZ", "Turquia": "TR",
}

_SUBSTITUICOES_NOME = {
    "Coréia Do Sul":      "Coréia do Sul",
    "Coreia Do Sul":      "Coréia do Sul",
    "País De Gales":      "País de Gales",
    "Costa Do Marfim":    "Costa do Marfim",
    "Rd Congo":           "RD Congo",
    "África Do Sul":      "África do Sul",
    "Bósnia E Herzegovina": "Bósnia e Herzegovina",
}

def normalizar_nome(nome: str) -> str:
    nome_limpo = str(nome).strip().title()
    nome_limpo = _SUBSTITUICOES_NOME.get(nome_limpo, nome_limpo)
    if nome_limpo.upper() == "EUA":
        nome_limpo = "EUA"
    return nome_limpo

def sigla_para_bandeira(sigla: str) -> str:
    if not isinstance(sigla, str) or len(sigla) != 2:
        return sigla
    sigla = sigla.upper()
    return chr(ord(sigla[0]) + 127397) + chr(ord(sigla[1]) + 127397)

def add_bandeira(nome, posicao: str = "mandante") -> str:
    """Retorna nome da equipe com emoji de bandeira.
    posicao='mandante'  → 'Brasil 🇧🇷'
    posicao='visitante' → '🇧🇷 Brasil'
    """
    if pd.isna(nome):
        return nome
    nome_limpo = normalizar_nome(nome)
    if nome_limpo in mapa_siglas:
        bandeira = sigla_para_bandeira(mapa_siglas[nome_limpo])
        return f"{nome_limpo} {bandeira}" if posicao == "mandante" else f"{bandeira} {nome_limpo}"
    return nome

def calculo_pontuacao(resultado_real, resultado_chutado) -> int:
    if pd.isna(resultado_real) or pd.isna(resultado_chutado):
        return 0
    try:
        gol_m_real,    gol_v_real    = map(int, str(resultado_real).lower().split("x"))
        gol_m_chutado, gol_v_chutado = map(int, str(resultado_chutado).lower().split("x"))
    except Exception:
        return 0

    if gol_m_real == gol_m_chutado and gol_v_real == gol_v_chutado:
        return 10

    saldo_real    = gol_m_real    - gol_v_real
    saldo_chutado = gol_m_chutado - gol_v_chutado

    vencedor_real    = 1 if saldo_real    > 0 else (-1 if saldo_real    < 0 else 0)
    vencedor_chutado = 1 if saldo_chutado > 0 else (-1 if saldo_chutado < 0 else 0)

    if vencedor_real == vencedor_chutado:
        if vencedor_real == 0:          # empate certo
            return 4
        elif saldo_real == saldo_chutado:  # saldo de gols certo
            return 6
        else:                           # só vencedor certo
            return 4
    return 0

def tem_resultado(resultado) -> bool:
    return pd.notna(resultado) and str(resultado).strip() != ""

# ── Conexão com a planilha ─────────────────────────────────────────────────────
@st.cache_resource
def conectar_planilha():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds  = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    cliente  = gspread.authorize(creds)
    planilha = cliente.open_by_key("1HEjaWHU-Oz9gECeBQvAxWczfvtuzqD4MruZ7doiHvkw")
    return planilha.sheet1

# ── Carregamento dos dados (com TTL curto para manter dados frescos) ───────────
@st.cache_data(ttl=60)
def carregar_dados(_sheet):
    """Carrega os registros e adiciona _row_num = linha real na planilha.
    Isso garante que o salvamento sempre aponte para a linha correta,
    independente de filtragens ou reordenações no DataFrame.
    """
    dados = _sheet.get_all_records()
    df = pd.DataFrame(dados)
    # Linha 1 = cabeçalho → dados começam na linha 2
    df["_row_num"] = range(2, len(df) + 2)
    return df

sheet   = conectar_planilha()
df_temp = carregar_dados(sheet)

df_temp["Equipe_Mandante"]  = df_temp["Equipe_Mandante"].apply(lambda x: add_bandeira(x, "mandante"))
df_temp["Equipe_Visitante"] = df_temp["Equipe_Visitante"].apply(lambda x: add_bandeira(x, "visitante"))

st.session_state.df = df_temp

# ── Cabeçalho ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns([8, 1])
with col1:
    st.title("⚽ Copa do Mundo 2026 - Bolão M02")
    st.write(f"Bem-vindo, **{nome_jogador}**!")
with col2:
    if st.button("Sair"):
        st.session_state.logado = False
        cookie_manager.delete("usuario_bolao", key="cookie_delete")
        st.warning("Desconectando...")
        time.sleep(1)
        st.rerun()

# ── Pontuação geral ────────────────────────────────────────────────────────────
pontos = {nome: 0 for nome in jogadores}
for nome, col_chute in jogadores.items():
    if col_chute in df_temp.columns and "Resultado" in df_temp.columns:
        pontos[nome] = df_temp.apply(
            lambda row: calculo_pontuacao(row["Resultado"], row[col_chute]), axis=1
        ).sum()

st.divider()

# ── Abas ───────────────────────────────────────────────────────────────────────
aba_placar, aba_palpites, aba_galera, aba_estatisticas, aba_admin = st.tabs(
    ["🏆 Placar Geral", "🎯 Meus Palpites", "👥 Palpites da Galera", "📊 Estatísticas", "⚙️ Admin"]
)

# ────────────────────────────────────────────────────────────────────────────────
with aba_placar:
    st.subheader("🏆 Classificação")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Arthur", pontos["Arthur"])
    c2.metric("Coelho", pontos["Coelho"])
    c3.metric("Feto",   pontos["Feto"])
    c4.metric("MC",     pontos["MC"])
    c5.metric("HC",     pontos["HC"])

# ────────────────────────────────────────────────────────────────────────────────
with aba_palpites:
    st.subheader("🎯 Meus Palpites")
    st.info("""
    **🚨 REGRAS IMPORTANTES PARA PALPITAR:**
    * ⏳ **Aguarde a confirmação:** Ao clicar em salvar, não feche o app ou mude de tela! Espere a caixinha terminar de carregar e mostrar o aviso verde de sucesso.
    * 🔒 **Horário limite:** Você pode mudar seu palpite quantas vezes quiser, mas a edição é bloqueada no exato minuto em que o jogo começa.
    * 🔄 **Atualize a página:** Se você deixou o site aberto em segundo plano no celular por muito tempo, atualize a página antes de salvar para evitar erros de conexão.
    * 🌙 **Virada do dia:** O nosso calendário vira o dia oficial do bolão sempre à 1h da manhã.
    """)

    agora_br_real      = datetime.datetime.now(fuso_br)
    agora_virtual      = agora_br_real - datetime.timedelta(hours=1)
    data_hoje_virtual  = agora_virtual.strftime("%Y-%m-%d")
    data_amanha_virtual = (agora_virtual + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    filtro_dia = st.radio(
        "📅 Filtrar jogos por data:",
        options=["Hoje", "Amanhã", "Ambos"],
        horizontal=True,
    )

    if filtro_dia == "Hoje":
        datas_filtro = [data_hoje_virtual]
    elif filtro_dia == "Amanhã":
        datas_filtro = [data_amanha_virtual]
    else:
        datas_filtro = [data_hoje_virtual, data_amanha_virtual]

    jogos_ativos = df_temp[df_temp["Data"].isin(datas_filtro)]

    if jogos_ativos.empty:
        st.info("Nenhum jogo programado para a seleção atual.")
    else:
        # Calcula a coluna na planilha UMA VEZ, fora do loop.
        # _row_num está no final do DataFrame, então não desloca as colunas anteriores.
        coluna_planilha = st.session_state.df.columns.get_loc(coluna_jogador) + 1

        with st.form("form_palpites"):
            # novos_chutes: { df_index → { "chute": "2x1", "row_num": 5 } }
            novos_chutes = {}

            for index, jogo in jogos_ativos.iterrows():
                st.markdown(f"### {jogo['Equipe_Mandante']} x {jogo['Equipe_Visitante']}")
                jogo_ja_comecou = False

                if "Horario" in jogo and pd.notna(jogo["Horario"]):
                    try:
                        string_data_hora = f"{jogo['Data']} {str(jogo['Horario']).strip()}"
                        data_hora_jogo   = datetime.datetime.strptime(
                            string_data_hora, "%Y-%m-%d %H:%M"
                        ).replace(tzinfo=fuso_br)
                        if agora_br_real >= data_hora_jogo:
                            jogo_ja_comecou = True
                    except Exception:
                        pass

                if jogo_ja_comecou:
                    st.caption("🔒 **Jogo já iniciado ou encerrado.**")
                else:
                    try:
                        data_string = str(jogo["Data"])
                        data_curta  = f"{data_string[-2:]}/{data_string[-5:-3]}"
                    except Exception:
                        data_curta = jogo["Data"]
                    st.caption(f"📅 Data: {data_curta} | ⏰ Horário: {jogo['Horario']}")

                chute_atual = jogo[coluna_jogador]
                try:
                    g1, g2 = map(int, str(chute_atual).split("x")) if pd.notna(chute_atual) else (0, 0)
                except Exception:
                    g1, g2 = 0, 0

                col_a, col_b = st.columns(2)
                with col_a:
                    gol_casa = st.number_input(
                        "Mandante", min_value=0, max_value=20, value=g1,
                        key=f"casa_{index}", disabled=jogo_ja_comecou
                    )
                with col_b:
                    gol_fora = st.number_input(
                        "Visitante", min_value=0, max_value=20, value=g2,
                        key=f"fora_{index}", disabled=jogo_ja_comecou
                    )

                if not jogo_ja_comecou:
                    novos_chutes[index] = {
                        "chute":   f"{gol_casa}x{gol_fora}",
                        "row_num": int(jogo["_row_num"]),  # ← linha real na planilha
                    }

                st.divider()

            salvar = st.form_submit_button("💾 Salvar Palpites")

            if salvar:
                if novos_chutes:
                    with st.status("⏳ Salvando de forma segura...", expanded=True) as status:
                        st.write("Empacotando seus palpites...")

                        celulas_para_atualizar = []
                        st.write("Enviando para o banco de dados...")

                        for idx, dados_chute in novos_chutes.items():
                            celulas_para_atualizar.append(
                                gspread.Cell(
                                    row=dados_chute["row_num"],  # ← linha real, não idx + 2
                                    col=coluna_planilha,
                                    value=dados_chute["chute"],
                                )
                            )

                        sheet.update_cells(celulas_para_atualizar)

                        time.sleep(1)
                        status.update(label="✅ Palpites confirmados com sucesso!", state="complete", expanded=False)
                        
                        st.cache_data.clear()
                        st.rerun()
                else:
                    st.warning("Todos os jogos filtrados já começaram. Não há palpites novos para salvar.")

# ────────────────────────────────────────────────────────────────────────────────
with aba_galera:
    st.subheader("👥 Palpites da Galera")

    agora_br = datetime.datetime.now(fuso_br)
    indices_jogos_iniciados = []

    for index, jogo in df_temp.iterrows():
        resultado_oficial = jogo.get("Resultado", "")
        jogo_ja_comecou   = tem_resultado(resultado_oficial)

        if not jogo_ja_comecou:
            try:
                string_data_hora = f"{jogo['Data']} {str(jogo['Horario']).strip()}"
                data_hora_jogo   = datetime.datetime.strptime(
                    string_data_hora, "%Y-%m-%d %H:%M"
                ).replace(tzinfo=fuso_br)
                if agora_br >= data_hora_jogo:
                    jogo_ja_comecou = True
            except Exception:
                pass

        if jogo_ja_comecou:
            indices_jogos_iniciados.append(index)

    df_iniciados = df_temp.loc[indices_jogos_iniciados]

    if df_iniciados.empty:
        st.info("🔒 Nenhum jogo começou ou foi encerrado ainda.")
    else:
        coluna_rodada = "Fase" if "Fase" in df_iniciados.columns else None

        if coluna_rodada:
            rodadas_disponiveis = sorted(df_iniciados[coluna_rodada].unique())
            rodada_selecionada  = st.selectbox(
                "📊 Filtrar por Rodada:", rodadas_disponiveis, key="seletor_rodadas"
            )
            jogos_para_exibir = df_iniciados[df_iniciados[coluna_rodada] == rodada_selecionada].copy()
        else:
            jogos_para_exibir = df_iniciados.copy()

        jogos_para_exibir["_encerrado"] = jogos_para_exibir["Resultado"].apply(tem_resultado)
        jogos_para_exibir = jogos_para_exibir.sort_values(by=["_encerrado"], ascending=True)

        participantes = [
            ("Arthur", "Chutes_Art"),
            ("Coelho", "Chutes_Cu"),
            ("Feto",   "Chutes_Feto"),
            ("MC",     "Chutes_MC"),
            ("HC",     "Chutes_HC"),
        ]

        for index, jogo in jogos_para_exibir.iterrows():
            st.markdown(f"### {jogo['Equipe_Mandante']} x {jogo['Equipe_Visitante']}")

            resultado_oficial = jogo.get("Resultado", "")
            jogo_encerrado    = tem_resultado(resultado_oficial)

            if jogo_encerrado:
                st.markdown(f"Placar oficial: **{resultado_oficial}**")
            else:
                st.caption(
                    f"📅 Data: {jogo['Data']} | ⏰ Horário: {jogo.get('Horario', '-')} | 🟢 **Em andamento**"
                )

            cols_profs = st.columns(5)
            for i, (nome_part, col_part) in enumerate(participantes):
                with cols_profs[i]:
                    valor_chute = (
                        jogo[col_part]
                        if pd.notna(jogo[col_part]) and str(jogo[col_part]).strip() != ""
                        else "-"
                    )
                    if jogo_encerrado and valor_chute != "-":
                        pontos_ganhos = calculo_pontuacao(resultado_oficial, valor_chute)
                        cor = "normal" if pontos_ganhos > 0 else "off"
                        st.metric(
                            label=nome_part,
                            value=str(valor_chute),
                            delta=f"{pontos_ganhos} pts",
                            delta_color=cor,
                        )
                    else:
                        st.metric(label=nome_part, value=str(valor_chute))

            st.divider()

# ────────────────────────────────────────────────────────────────────────────────
with aba_estatisticas:
    st.subheader("📊 Estatísticas e Desempenho")

    df_encerrados = df_temp[df_temp["Resultado"].apply(tem_resultado)].copy()

    if df_encerrados.empty:
        st.info("Ainda não há jogos encerrados.")
    else:
        horarios = df_encerrados.get("Horario", pd.Series(["00:00"] * len(df_encerrados)))
        horarios = horarios.fillna("00:00").astype(str)
        df_encerrados["_data_hora_str"] = df_encerrados["Data"].astype(str) + " " + horarios
        df_encerrados["_datetime"]      = pd.to_datetime(df_encerrados["_data_hora_str"], errors="coerce")
        df_encerrados = df_encerrados.sort_values(by=["_datetime"], ascending=True)

        historico_pontos = {nome: [0] for nome in jogadores}
        labels_grafico   = ["Jogo 000 (Início)"]
        stats_jogadores  = {
            nome: {
                "Cravadas (10)": 0, "Saldos (6)": 0,
                "Vencedores (4)": 0, "Empates (4)": 0, "Zerados (0)": 0,
            }
            for nome in jogadores
        }

        for contador_jogo, (_, row) in enumerate(df_encerrados.iterrows(), start=1):
            resultado = row["Resultado"]
            try:
                data_string = str(row["Data"])
                data_curta  = f"{data_string[-2:]}/{data_string[-5:-3]}"
            except Exception:
                data_curta = "Data?"
            labels_grafico.append(f"Jogo {contador_jogo:03d} ({data_curta})")

            try:
                g1_r, g2_r    = map(int, str(resultado).lower().split("x"))
                eh_empate_real = (g1_r == g2_r)
            except Exception:
                eh_empate_real = False

            for nome, col in jogadores.items():
                chute = row.get(col, "")
                pts   = calculo_pontuacao(resultado, chute)
                historico_pontos[nome].append(historico_pontos[nome][-1] + pts)

                if pts == 10:
                    stats_jogadores[nome]["Cravadas (10)"] += 1
                elif pts == 6:
                    stats_jogadores[nome]["Saldos (6)"] += 1
                elif pts == 4:
                    key = "Empates (4)" if eh_empate_real else "Vencedores (4)"
                    stats_jogadores[nome][key] += 1
                else:
                    stats_jogadores[nome]["Zerados (0)"] += 1

        st.markdown("### 📈 Corrida dos Pontos")
        df_grafico       = pd.DataFrame(historico_pontos, index=labels_grafico)
        st.line_chart(df_grafico)
        st.divider()

        st.markdown("### 🏅 Raio-X dos Acertos")
        df_stats = pd.DataFrame(stats_jogadores).T
        df_stats["Pontos Totais"] = [historico_pontos[nome][-1] for nome in jogadores]
        df_stats = df_stats[["Pontos Totais", "Cravadas (10)", "Saldos (6)", "Vencedores (4)", "Empates (4)", "Zerados (0)"]]
        df_stats = df_stats.sort_values(by=["Pontos Totais", "Cravadas (10)"], ascending=[False, False])
        st.dataframe(df_stats, use_container_width=True)

# ────────────────────────────────────────────────────────────────────────────────
with aba_admin:
    if usuario_logado == "hc":
        st.subheader("⚙️ Atualizar Resultados Oficiais")

        df_admin = df_temp[["Data", "Equipe_Mandante", "Equipe_Visitante", "Resultado"]].copy()

        df_editado_admin = st.data_editor(
            df_admin,
            disabled=["Data", "Equipe_Mandante", "Equipe_Visitante"],
            key="editor_admin",
        )

        if st.button("Salvar Resultados no Banco de Dados"):
            coluna_resultado = st.session_state.df.columns.get_loc("Resultado") + 1
            alteracoes_feitas = 0

            for index, row in df_editado_admin.iterrows():
                resultado_velho = df_admin.loc[index, "Resultado"]
                resultado_novo  = row["Resultado"]

                if str(resultado_velho) != str(resultado_novo):
                    linha_planilha = int(df_temp.loc[index, "_row_num"])  # ← linha real
                    sheet.update_cell(linha_planilha, coluna_resultado, resultado_novo)
                    alteracoes_feitas += 1

            if alteracoes_feitas > 0:
                st.success(f"{alteracoes_feitas} resultado(s) atualizado(s) com sucesso!")
                st.cache_data.clear()
                st.rerun()
            else:
                st.info("Nenhuma alteração detectada para salvar.")
    else:
        st.error("Você não tem permissão para acessar esta área.")
