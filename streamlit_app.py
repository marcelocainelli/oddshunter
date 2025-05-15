import streamlit as st
import pandas as pd
import numpy as np
import math
import time
import json
from datetime import datetime
import odds_api_simulator as api # Mantém o simulador de dados
from PIL import Image # Para carregar o logo

# --- Identidade Visual OddsHunter ---
LOGO_PATH = "logo_oddshunter_v1.png"  # Caminho relativo para o Streamlit Cloud
COR_PRIMARIA_AZUL = "#0A2239"
COR_SECUNDARIA_VERDE = "#2A7A7B"
COR_DESTAQUE_DOURADO = "#E6A12E"
COR_TEXTO_BRANCO = "#FFFFFF"
COR_TEXTO_CINZA_CLARO = "#F0F0F0"
COR_TEXTO_CINZA_ESCURO = "#333333"

# Funções do arbitrage_calculator.py integradas aqui para o protótipo
def calcular_probabilidade_implicita(odds):
    if odds <= 0:
        return float('inf')
    return 1 / odds

def verificar_arbitragem_2_vias(odds_r1_casaA, nome_casaA, nome_r1, odds_r2_casaB, nome_casaB, nome_r2, investimento_total=100):
    prob_impl_r1 = calcular_probabilidade_implicita(odds_r1_casaA)
    prob_impl_r2 = calcular_probabilidade_implicita(odds_r2_casaB)
    soma_probabilidades = prob_impl_r1 + prob_impl_r2

    if soma_probabilidades < 1:
        lucro_percentual = (1 - soma_probabilidades) * 100
        retorno_garantido = investimento_total / soma_probabilidades
        stake1 = retorno_garantido / odds_r1_casaA
        stake2 = retorno_garantido / odds_r2_casaB
        investimento_real_total = stake1 + stake2

        return {
            "tipo_mercado": "2-vias",
            "oportunidade": True,
            "soma_probabilidades_implicitas": soma_probabilidades,
            "lucro_percentual_garantido": lucro_percentual,
            "detalhes_apostas": [
                {"casa": nome_casaA, "resultado": nome_r1, "odd": odds_r1_casaA, "stake_sugerido": stake1, "retorno_individual": stake1 * odds_r1_casaA},
                {"casa": nome_casaB, "resultado": nome_r2, "odd": odds_r2_casaB, "stake_sugerido": stake2, "retorno_individual": stake2 * odds_r2_casaB}
            ],
            "investimento_total_sugerido": investimento_real_total,
            "retorno_garantido": retorno_garantido
        }
    return None

def verificar_arbitragem_3_vias(odds_r1_casaA, nome_casaA, nome_r1, odds_r2_casaB, nome_casaB, nome_r2, odds_r3_casaC, nome_casaC, nome_r3, investimento_total=100):
    prob_impl_r1 = calcular_probabilidade_implicita(odds_r1_casaA)
    prob_impl_r2 = calcular_probabilidade_implicita(odds_r2_casaB)
    prob_impl_r3 = calcular_probabilidade_implicita(odds_r3_casaC)
    soma_probabilidades = prob_impl_r1 + prob_impl_r2 + prob_impl_r3

    if soma_probabilidades < 1:
        lucro_percentual = (1 - soma_probabilidades) * 100
        retorno_garantido = investimento_total / soma_probabilidades
        stake1 = retorno_garantido / odds_r1_casaA
        stake2 = retorno_garantido / odds_r2_casaB
        stake3 = retorno_garantido / odds_r3_casaC
        investimento_real_total = stake1 + stake2 + stake3

        return {
            "tipo_mercado": "3-vias",
            "oportunidade": True,
            "soma_probabilidades_implicitas": soma_probabilidades,
            "lucro_percentual_garantido": lucro_percentual,
            "detalhes_apostas": [
                {"casa": nome_casaA, "resultado": nome_r1, "odd": odds_r1_casaA, "stake_sugerido": stake1, "retorno_individual": stake1 * odds_r1_casaA},
                {"casa": nome_casaB, "resultado": nome_r2, "odd": odds_r2_casaB, "stake_sugerido": stake2, "retorno_individual": stake2 * odds_r2_casaB},
                {"casa": nome_casaC, "resultado": nome_r3, "odd": odds_r3_casaC, "stake_sugerido": stake3, "retorno_individual": stake3 * odds_r3_casaC}
            ],
            "investimento_total_sugerido": investimento_real_total,
            "retorno_garantido": retorno_garantido
        }
    return None

def encontrar_oportunidades_arbitragem_reais(dados_odds_api, investimento_desejado):
    oportunidades = []
    for evento_data in dados_odds_api:
        id_evento = evento_data["id_evento"]
        descricao_evento = evento_data["descricao_evento"]
        esporte = evento_data["esporte"]
        liga = evento_data["liga"]
        if not evento_data["odds_por_casa"]: continue
        primeiro_conjunto_odds = evento_data["odds_por_casa"][0]["odds"]
        resultados_possiveis = list(primeiro_conjunto_odds.keys())
        tipo_mercado = "3-vias" if len(resultados_possiveis) == 3 else "2-vias"
        melhores_odds = {}
        casas_melhores_odds = {}
        for resultado in resultados_possiveis:
            melhor_odd = 0
            casa_melhor_odd = None
            for casa_odds in evento_data["odds_por_casa"]:
                if resultado in casa_odds["odds"] and casa_odds["odds"][resultado] > melhor_odd:
                    melhor_odd = casa_odds["odds"][resultado]
                    casa_melhor_odd = casa_odds["nome_casa"]
            if melhor_odd > 0:
                melhores_odds[resultado] = melhor_odd
                casas_melhores_odds[resultado] = casa_melhor_odd
        if len(melhores_odds) != len(resultados_possiveis): continue
        if tipo_mercado == "2-vias" and len(resultados_possiveis) == 2:
            r1, r2 = resultados_possiveis
            oportunidade = verificar_arbitragem_2_vias(
                melhores_odds[r1], casas_melhores_odds[r1], r1,
                melhores_odds[r2], casas_melhores_odds[r2], r2,
                investimento_total=investimento_desejado)
            if oportunidade:
                oportunidade.update({"id_evento": id_evento, "descricao_evento": descricao_evento, "esporte": esporte, "liga": liga, "timestamp": time.time()})
                oportunidades.append(oportunidade)
        elif tipo_mercado == "3-vias" and len(resultados_possiveis) == 3:
            r1, r2, r3 = resultados_possiveis
            oportunidade = verificar_arbitragem_3_vias(
                melhores_odds[r1], casas_melhores_odds[r1], r1,
                melhores_odds[r2], casas_melhores_odds[r2], r2,
                melhores_odds[r3], casas_melhores_odds[r3], r3,
                investimento_total=investimento_desejado)
            if oportunidade:
                oportunidade.update({"id_evento": id_evento, "descricao_evento": descricao_evento, "esporte": esporte, "liga": liga, "timestamp": time.time()})
                oportunidades.append(oportunidade)
    return oportunidades

# Configuração da página
st.set_page_config(layout="wide", page_title="OddsHunter - Monitoramento de Odds e Arbitragem")

# Aplicar CSS customizado para cores e fontes (básico)
# Idealmente, usaríamos um config.toml para temas mais completos, mas para uma demo rápida:
st.markdown(f"""
<style>
    .stApp {{
        background-color: {COR_PRIMARIA_AZUL};
        color: {COR_TEXTO_CINZA_CLARO};
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {COR_TEXTO_BRANCO}; 
    }}
    .stButton>button {{
        background-color: {COR_SECUNDARIA_VERDE};
        color: {COR_TEXTO_BRANCO};
        border-radius: 5px;
        border: none;
    }}
    .stButton>button:hover {{
        background-color: {COR_DESTAQUE_DOURADO};
        color: {COR_PRIMARIA_AZUL};
    }}
    .stMarkdown {{ color: {COR_TEXTO_CINZA_CLARO}; }}
    .stDataFrame {{ color: {COR_TEXTO_CINZA_ESCURO}; }}
    .stTable {{ color: {COR_TEXTO_CINZA_ESCURO}; }}
    /* Para destacar o lucro com a cor de destaque */
    .lucro-destaque {{
        color: {COR_DESTAQUE_DOURADO};
        font-weight: bold;
    }}
</style>
""", unsafe_allow_html=True)

# Logo e Título
col_logo1, col_logo2 = st.columns([1, 5])
with col_logo1:
    try:
        logo_image = Image.open(LOGO_PATH)
        st.image(logo_image, width=100)
    except FileNotFoundError:
        st.error("Logo não encontrado.")
with col_logo2:
    st.markdown(f"<h1 style='color:{COR_TEXTO_BRANCO};'>OddsHunter</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{COR_SECUNDARIA_VERDE}; font-size: 1.1em;'>Monitoramento Inteligente de Odds e Arbitragem</p>", unsafe_allow_html=True)

st.caption("Versão com Dados Simulados de API - Demonstração de Integração com Identidade Visual")

# Sidebar para configurações
st.sidebar.markdown(f"<h2 style='color:{COR_TEXTO_BRANCO};'>⚙️ Configurações</h2>", unsafe_allow_html=True)
investimento_usuario = st.sidebar.number_input("Valor Total para Investir (R$):", min_value=10.0, value=100.0, step=10.0)
auto_refresh = st.sidebar.checkbox("Atualização Automática", value=True)
refresh_interval = st.sidebar.slider("Intervalo de Atualização (s):", min_value=5, max_value=60, value=15, step=5)
limiar_lucro = st.sidebar.slider("Limiar Mínimo de Lucro (%):", min_value=0.1, max_value=10.0, value=0.5, step=0.1)

# Botão para atualização manual
col1_main, col2_main = st.columns([3, 1])
with col1_main:
    st.markdown(f"<h3 style='color:{COR_TEXTO_BRANCO};'>Dados de Odds em Tempo Real (Simulados)</h3>", unsafe_allow_html=True)
with col2_main:
    manual_refresh = st.button("Atualizar Agora")

if 'last_refresh' not in st.session_state: st.session_state.last_refresh = 0
if 'odds_data' not in st.session_state: st.session_state.odds_data = None
if 'oportunidades' not in st.session_state: st.session_state.oportunidades = []

current_time = time.time()
should_refresh = manual_refresh or (auto_refresh and (current_time - st.session_state.last_refresh) > refresh_interval)

if should_refresh:
    with st.spinner("Buscando dados de odds..."):
        odds_data = api.fetch_live_odds_simulated()
        st.session_state.odds_data = odds_data
        oportunidades = encontrar_oportunidades_arbitragem_reais(odds_data, investimento_usuario)
        st.session_state.oportunidades = oportunidades
        st.session_state.last_refresh = current_time
    st.caption(f"Última atualização: {datetime.fromtimestamp(current_time).strftime('%H:%M:%S')}")

st.markdown(f"<h2 style='color:{COR_TEXTO_BRANCO};'>🚨 Oportunidades de Arbitragem</h2>", unsafe_allow_html=True)
if st.session_state.oportunidades:
    oportunidades_filtradas = [op for op in st.session_state.oportunidades if op["lucro_percentual_garantido"] >= limiar_lucro]
    if oportunidades_filtradas:
        for op in oportunidades_filtradas:
            with st.container():
                st.markdown(f"<h3 style='color:{COR_SECUNDARIA_VERDE};'>🎯 {op['descricao_evento']} ({op['esporte']} - {op['liga']})</h3>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Lucro Garantido:** <span class='lucro-destaque'>{op['lucro_percentual_garantido']:.2f}%</span>", unsafe_allow_html=True)
                    st.markdown(f"**Investimento Sugerido:** R$ {op['investimento_total_sugerido']:.2f}")
                with col2:
                    st.markdown(f"**Retorno Garantido:** R$ {op['retorno_garantido']:.2f}")
                    st.markdown(f"**Soma Probabilidades:** {op['soma_probabilidades_implicitas']:.4f}")
                st.markdown("**Detalhes das Apostas Sugeridas:**")
                detalhes_df = pd.DataFrame(op['detalhes_apostas'])
                detalhes_df_display = detalhes_df[['casa', 'resultado', 'odd', 'stake_sugerido', 'retorno_individual']]
                detalhes_df_display['stake_sugerido'] = detalhes_df_display['stake_sugerido'].map(lambda x: f"R$ {x:.2f}")
                detalhes_df_display['retorno_individual'] = detalhes_df_display['retorno_individual'].map(lambda x: f"R$ {x:.2f}")
                detalhes_df_display.rename(columns={'casa': 'Casa', 'resultado': 'Apostar em', 'odd': 'Odd', 'stake_sugerido': 'Stake', 'retorno_individual': 'Retorno'}, inplace=True)
                st.table(detalhes_df_display.set_index('Casa'))
                st.divider()
    else:
        st.info(f"Nenhuma oportunidade de arbitragem encontrada com lucro acima de {limiar_lucro}%.")
else:
    if st.session_state.odds_data: st.info("Nenhuma oportunidade de arbitragem encontrada nos dados atuais.")
    else: st.warning("Aguardando dados. Clique em 'Atualizar Agora' ou aguarde a atualização automática.")

st.markdown(f"<h2 style='color:{COR_TEXTO_BRANCO};'>📊 Visualização de Odds por Evento</h2>", unsafe_allow_html=True)
if st.session_state.odds_data:
    eventos_por_esporte = {e["esporte"]: [] for e in st.session_state.odds_data}
    for evento in st.session_state.odds_data: eventos_por_esporte[evento["esporte"]].append(evento)
    esportes_disponiveis = list(eventos_por_esporte.keys())
    selected_esporte = st.selectbox("Selecione o Esporte:", options=esportes_disponiveis)
    if selected_esporte:
        eventos_do_esporte = eventos_por_esporte[selected_esporte]
        nomes_eventos = [e["descricao_evento"] for e in eventos_do_esporte]
        selected_evento_nome = st.selectbox("Selecione o Evento:", options=nomes_eventos)
        if selected_evento_nome:
            evento_selecionado = next((e for e in eventos_do_esporte if e["descricao_evento"] == selected_evento_nome), None)
            if evento_selecionado:
                st.markdown(f"<h3 style='color:{COR_SECUNDARIA_VERDE};'>Odds para: {evento_selecionado['descricao_evento']} ({evento_selecionado['liga']})</h3>", unsafe_allow_html=True)
                odds_data_vis = []
                for casa_odds in evento_selecionado["odds_por_casa"]:
                    for resultado, odd in casa_odds["odds"].items():
                        odds_data_vis.append({"Casa de Aposta": casa_odds["nome_casa"], "Resultado": resultado, "Odd": odd})
                if odds_data_vis:
                    df_odds = pd.DataFrame(odds_data_vis)
                    df_pivot = df_odds.pivot(index="Resultado", columns="Casa de Aposta", values="Odd")
                    st.dataframe(df_pivot.style.highlight_max(axis=1, props=f'color:{COR_TEXTO_CINZA_ESCURO}; background-color:{COR_DESTAQUE_DOURADO};'))
                    st.markdown("**Comparativo de Odds:**")
                    resultados_options = df_pivot.index.tolist()
                    selected_resultado_grafico = st.selectbox("Resultado para comparar:", options=resultados_options, key=f"graf_{evento_selecionado['id_evento']}")
                    if selected_resultado_grafico:
                        df_grafico = df_odds[df_odds["Resultado"] == selected_resultado_grafico][["Casa de Aposta", "Odd"]]
                        st.bar_chart(df_grafico.set_index("Casa de Aposta"))
                else: st.warning("Não há dados de odds para este evento.")
else: st.warning("Aguardando dados. Clique em 'Atualizar Agora' ou aguarde a atualização automática.")

st.markdown("<hr style='border: 1px solid #2A7A7B;'>", unsafe_allow_html=True)
st.caption(f"OddsHunter v1.1 (Branded) - Desenvolvido por Manus AI. Identidade Visual aplicada.")

# Adicionar informações sobre o deploy permanente
st.sidebar.markdown("---")
st.sidebar.markdown(f"<h3 style='color:{COR_TEXTO_BRANCO};'>Sobre este Deploy</h3>", unsafe_allow_html=True)
st.sidebar.markdown("Esta é uma versão permanente do OddsHunter hospedada no Streamlit Community Cloud.")
st.sidebar.markdown("O código fonte está disponível no GitHub.")
