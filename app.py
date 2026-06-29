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

termos_matamata = ["16", "oitava", "quarta", "semi", "final", "3º", "terceiro"]

def is_matamata(fase_val):
    if pd.isna(fase_val):
        return False
    fase_str = str(fase_val).lower()
    return any(termo in fase_str for termo in termos_matamata)

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
    if pd.isna(nome):
        return nome
    nome_limpo = normalizar_nome(nome)
    if nome_limpo in mapa_siglas:
        bandeira = sigla_para_bandeira(mapa_siglas[nome_limpo])
        return f"{nome_limpo} {bandeira}" if posicao == "mandante" else f"{bandeira} {nome_limpo}"
    return nome

def parse_placar(placar_str):
    """Extrai gols e vencedor dos pênaltis de uma string como '1x1-m'."""
    if pd.isna(placar_str): return None, None, None
    s = str(placar_str).strip().lower()
    if not s: return None, None, None
    
    penaltis = None
    if "-" in s:
        partes = s.split("-")
        s = partes[0]
        penaltis = partes[1].strip() # 'm' ou 'v'
        
    try:
        g1, g2 = map(int, s.split("x"))
        return g1, g2, penaltis
    except Exception:
        return None, None, None

def formatar_chute_tela(chute_str):
    """Transforma '1x1-m' em '1x1 (M)' para exibir bonitinho na tela."""
    if not pd.notna(chute_str) or str(chute_str).strip() == "": return "-"
    s = str(chute_str).upper()
    if "-M" in s: return s.replace("-M", " (M)")
    if "-V" in s: return s.replace("-V", " (V)")
    return s

def calculo_pontuacao(resultado_real, resultado_chutado) -> int:
    g1_r, g2_r, pen_r = parse_placar(resultado_real)
    g1_c, g2_c, pen_c = parse_placar(resultado_chutado)

    if g1_r is None or g1_c is None:
        return 0

    pontos = 0
    # Acerto de placar exato
    if g1_r == g1_c and g2_r == g2_c:
        pontos = 10
    else:
        saldo_real    = g1_r - g2_r
        saldo_chutado = g1_c - g2_c

        vencedor_real    = 1 if saldo_real > 0 else (-1 if saldo_real < 0 else 0)
        vencedor_chutado = 1 if saldo_chutado > 0 else (-1 if saldo_chutado < 0 else 0)

        if vencedor_real == vencedor_chutado:
            if vencedor_real == 0:          # empate certo
                pontos = 4
            elif saldo_real == saldo_chutado:  # saldo de gols certo
                pontos = 6
            else:                           # só vencedor certo
                pontos = 4

    # Bônus de pênaltis (+3 pontos) se for empate e acertar quem passa
    if pen_r is not None and pen_r == pen_c:
        pontos += 3

    return pontos

def tem_resultado(resultado) -> bool:
    return pd.notna(resultado) and str(resultado).strip() != ""

# ── Conexão com a planilha ─────────────────────────────────────────────────────
@st.cache_resource(ttl=3600)
def conectar_planilha():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds  = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    cliente  = gspread.authorize(creds)
    planilha = cliente.open_by_key("1HEjaWHU-Oz9gECeBQvAxWczfvtuzqD4MruZ7doiHvkw")
    return planilha.sheet1

# ── Carregamento dos dados ─────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def carregar_dados(_sheet):
    dados = _sheet.get_all_records()
    df = pd.DataFrame(dados)
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
pontos_geral = {nome: 0 for nome in jogadores}
pontos_grupos = {nome: 0 for nome in jogadores}
pontos_matamata = {nome: 0 for nome in jogadores}

for nome, col_chute in jogadores.items():
    if col_chute in df_temp.columns and "Resultado" in df_temp.columns:
        for index, row in df_temp.iterrows():
            pts = calculo_pontuacao(row["Resultado"], row[col_chute])
            pontos_geral[nome] += pts
            if "Fase" in df_temp.columns and is_matamata(row["Fase"]):
                pontos_matamata[nome] += pts
            else:
                pontos_grupos[nome] += pts

st.divider()

# ── Abas ───────────────────────────────────────────────────────────────────────
aba_placar, aba_palpites, aba_galera, aba_estatisticas, aba_admin = st.tabs(
    ["🏆 Placar Geral", "🎯 Meus Palpites", "👥 Palpites da Galera", "📊 Estatísticas", "⚙️ Admin"]
)

# ────────────────────────────────────────────────────────────────────────────────
with aba_placar:
    st.subheader("🏆 Placar Geral")
    ranking_geral = sorted(pontos_geral.items(), key=lambda x: x[1], reverse=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    for i, (nome, pts) in enumerate(ranking_geral):
        [c1, c2, c3, c4, c5][i].metric(f"{i+1}º - {nome}", f"{pts} pts")

    st.divider()

    st.subheader("⚽ Placar da Fase de Grupos")
    ranking_grupos = sorted(pontos_grupos.items(), key=lambda x: x[1], reverse=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    for i, (nome, pts) in enumerate(ranking_grupos):
        [c1, c2, c3, c4, c5][i].metric(f"{i+1}º - {nome}", f"{pts} pts")

    st.divider()

    st.subheader("🔥 Placar do Mata-Mata")
    ranking_mata = sorted(pontos_matamata.items(), key=lambda x: x[1], reverse=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    for i, (nome, pts) in enumerate(ranking_mata):
        [c1, c2, c3, c4, c5][i].metric(f"{i+1}º - {nome}", f"{pts} pts")

# ────────────────────────────────────────────────────────────────────────────────
with aba_palpites:
    st.subheader("🎯 Meus Palpites")
    st.info("""
    **🚨 REGRAS IMPORTANTES PARA PALPITAR:**
    * ⏳ **Aguarde a confirmação:** Ao clicar em salvar, não feche o app.
    * 🔒 **Horário limite:** A edição é bloqueada no exato minuto em que o jogo começa.
    * 🏆 **Pênaltis (Mata-Mata):** Se você palpitar EMPATE em jogos de mata-mata, deverá escolher quem avança nos pênaltis (+3 pontos extras).
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
        coluna_planilha = st.session_state.df.columns.get_loc(coluna_jogador) + 1

        with st.form("form_palpites"):
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
                    if pd.notna(chute_atual) and str(chute_atual).strip() != "":
                        partes_chute = str(chute_atual).lower().split("-")
                        g1, g2 = map(int, partes_chute[0].split("x"))
                        pen_atual = partes_chute[1] if len(partes_chute) > 1 else None
                    else:
                        g1, g2, pen_atual = 0, 0, None
                except Exception:
                    g1, g2, pen_atual = 0, 0, None

                col_a, col_b = st.columns(2)
                with col_a:
                    gol_casa = st.number_input("Mandante", min_value=0, max_value=20, value=g1, key=f"casa_{index}", disabled=jogo_ja_comecou)
                with col_b:
                    gol_fora = st.number_input("Visitante", min_value=0, max_value=20, value=g2, key=f"fora_{index}", disabled=jogo_ja_comecou)

                penalti_sufixo = ""
                # Se for mata-mata e o palpite for de empate, abre seleção de pênaltis
                if gol_casa == gol_fora and is_matamata(jogo.get("Fase", "")):
                    idx_padrao = 1 if pen_atual == "v" else 0
                    vencedor_penaltis = st.radio(
                        "🔥 Desempate: Quem avança nos pênaltis?",
                        options=["Mandante", "Visitante"],
                        index=idx_padrao,
                        key=f"pen_{index}",
                        horizontal=True,
                        disabled=jogo_ja_comecou
                    )
                    penalti_sufixo = "-m" if vencedor_penaltis == "Mandante" else "-v"

                if not jogo_ja_comecou:
                    novos_chutes[index] = {
                        "chute":   f"{gol_casa}x{gol_fora}{penalti_sufixo}",
                        "row_num": int(jogo["_row_num"]),
                    }

                st.divider()

            salvar = st.form_submit_button("💾 Salvar Palpites")

            if salvar:
                if novos_chutes:
                    with st.status("⏳ Salvando palpites...", expanded=True) as status:
                        celulas_para_atualizar = []
                        for idx, dados_chute in novos_chutes.items():
                            celulas_para_atualizar.append(
                                gspread.Cell(
                                    row=dados_chute["row_num"],
                                    col=coluna_planilha,
                                    value=dados_chute["chute"],
                                )
                            )
                        try:
                            sheet.update_cells(celulas_para_atualizar)
                            status.update(label="✅ Palpites confirmados!", state="complete", expanded=False)
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            status.update(label="❌ Erro ao salvar!", state="error", expanded=True)
                            st.error("Não foi possível salvar.")
                            st.exception(e)
                else:
                    st.warning("Não há palpites novos para salvar.")

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
                st.markdown(f"Placar oficial: **{formatar_chute_tela(resultado_oficial)}**")
            else:
                st.caption(f"📅 Data: {jogo['Data']} | ⏰ Horário: {jogo.get('Horario', '-')} | 🟢 **Em andamento**")

            cols_profs = st.columns(5)
            for i, (nome_part, col_part) in enumerate(participantes):
                with cols_profs[i]:
                    chute_bruto = jogo[col_part]
                    valor_chute_formatado = formatar_chute_tela(chute_bruto)
                    
                    if jogo_encerrado and valor_chute_formatado != "-":
                        pontos_ganhos = calculo_pontuacao(resultado_oficial, chute_bruto)
                        cor = "normal" if pontos_ganhos > 0 else "off"
                        st.metric(
                            label=nome_part,
                            value=valor_chute_formatado,
                            delta=f"{pontos_ganhos} pts",
                            delta_color=cor,
                        )
                    else:
                        st.metric(label=nome_part, value=valor_chute_formatado)

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
                "Acertos Pênaltis (+3)": 0
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

            g1_r, g2_r, pen_r = parse_placar(resultado)
            eh_empate_real = (g1_r is not None and g1_r == g2_r)

            for nome, col in jogadores.items():
                chute = row.get(col, "")
                pts   = calculo_pontuacao(resultado, chute)
                historico_pontos[nome].append(historico_pontos[nome][-1] + pts)

                # Avalia apenas a parte base (sem bônus) para a estatística
                g1_c, g2_c, pen_c = parse_placar(chute)
                pts_base = pts - (3 if (pen_r is not None and pen_r == pen_c) else 0)

                if pts_base == 10:
                    stats_jogadores[nome]["Cravadas (10)"] += 1
                elif pts_base == 6:
                    stats_jogadores[nome]["Saldos (6)"] += 1
                elif pts_base == 4:
                    key = "Empates (4)" if eh_empate_real else "Vencedores (4)"
                    stats_jogadores[nome][key] += 1
                else:
                    stats_jogadores[nome]["Zerados (0)"] += 1
                
                if pen_r is not None and pen_r == pen_c:
                    stats_jogadores[nome]["Acertos Pênaltis (+3)"] += 1

        st.markdown("### 📈 Corrida dos Pontos")
        df_grafico = pd.DataFrame(historico_pontos, index=labels_grafico)
        st.line_chart(df_grafico)
        st.divider()

        st.markdown("### 🏅 Raio-X dos Acertos")
        df_stats = pd.DataFrame(stats_jogadores).T
        df_stats["Pontos Totais"] = [historico_pontos[nome][-1] for nome in jogadores]
        df_stats = df_stats[["Pontos Totais", "Cravadas (10)", "Saldos (6)", "Vencedores (4)", "Empates (4)", "Acertos Pênaltis (+3)", "Zerados (0)"]]
        df_stats = df_stats.sort_values(by=["Pontos Totais", "Cravadas (10)"], ascending=[False, False])
        st.dataframe(df_stats, use_container_width=True)

# ────────────────────────────────────────────────────────────────────────────────
with aba_admin:
    if usuario_logado == "hc":
        st.subheader("⚙️ Atualizar Resultados Oficiais")
        st.info("📌 **DICA PARA MATA-MATA:** Se o jogo terminou empatado e foi para os pênaltis, adicione `-m` (vitória do Mandante) ou `-v` (vitória do Visitante) ao resultado final. Exemplo: `1x1-m` ou `2x2-v`.")

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
                    linha_planilha = int(df_temp.loc[index, "_row_num"])
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
