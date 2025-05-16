import streamlit as st
import pandas as pd
import numpy as np
import math
import time
import json
from datetime import datetime
import odds_api_simulator as api # Mantém o simulador de dados (mantido para compatibilidade)
from PIL import Image # Para carregar o logo
import subprocess
import pymongo
from pymongo import MongoClient

# --- Identidade Visual OddsHunter ---
LOGO_PATH = "logo_oddshunter_v1.png"  # Caminho relativo para o Streamlit Cloud
COR_PRIMARIA_AZUL = "#0A2239"
COR_SECUNDARIA_VERDE = "#2A7A7B"
COR_DESTAQUE_DOURADO = "#E6A12E"
COR_TEXTO_BRANCO = "#FFFFFF"
COR_TEXTO_CINZA_CLARO = "#F0F0F0"
COR_TEXTO_CINZA_ESCURO = "#333333"

# --- MongoDB Settings ---
MONGODB_URI = "mongodb://localhost:27017/"  # Altere para a URI do seu MongoDB
MONGODB_DATABASE = "oddshunter"
MONGODB_COLLECTION = "dados_recentes"

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

# --- MongoDB Integration ---
def conectar_mongodb():
    """Estabelece conexão com o MongoDB e retorna o cliente de conexão"""
    try:
        # Configure a string de conexão conforme necessário
        client = MongoClient(MONGODB_URI)
        return client
    except Exception as e:
        st.error(f"Erro ao conectar ao MongoDB: {e}")
        return None

def obter_dados_mongodb():
    """Obtém dados da coleção definida nas configurações"""
    client = conectar_mongodb()
    if client:
        try:
            db = client[MONGODB_DATABASE]
            collection = db[MONGODB_COLLECTION]
            dados = list(collection.find())
            client.close()
            return dados
        except Exception as e:
            st.error(f"Erro ao obter dados do MongoDB: {e}")
            client.close()
    return []

def processar_oportunidades_mongodb(dados_mongodb, investimento_desejado=100):
    """Processa os dados do MongoDB e retorna oportunidades formatadas"""
    oportunidades = []
    
    for item in dados_mongodb:
        # Verifica se há odds válidas para pelo menos 2 resultados
        if not item.get('odd_1') or not item.get('odd_2'):
            continue
            
        tipo_mercado = "3-vias" if item.get('odd_3') else "2-vias"
        lucro_percentual = item.get('lucro_percentual', 0)
        
        # Converter odds de string para float
        try:
            odds_r1 = float(item.get('odd_1', '0').replace(',', '.'))
            odds_r2 = float(item.get('odd_2', '0').replace(',', '.'))
            odds_r3 = float(item.get('odd_3', '0').replace(',', '.')) if item.get('odd_3') else 0
        except (ValueError, TypeError):
            continue
            
        # Pular registros com odds inválidas
        if odds_r1 <= 1 or odds_r2 <= 1 or (tipo_mercado == "3-vias" and odds_r3 <= 1):
            continue
            
        # Calcular probabilidades implícitas
        prob_impl_r1 = calcular_probabilidade_implicita(odds_r1)
        prob_impl_r2 = calcular_probabilidade_implicita(odds_r2)
        prob_impl_r3 = calcular_probabilidade_implicita(odds_r3) if tipo_mercado == "3-vias" else 0
        
        soma_probabilidades = prob_impl_r1 + prob_impl_r2
        if tipo_mercado == "3-vias":
            soma_probabilidades += prob_impl_r3
            
        if soma_probabilidades < 1:
            retorno_garantido = investimento_desejado / soma_probabilidades
            stake1 = retorno_garantido / odds_r1
            stake2 = retorno_garantido / odds_r2
            
            if tipo_mercado == "2-vias":
                investimento_real_total = stake1 + stake2
                nomes_resultados = item.get('linha', 'Casa/Fora').split('/')
                if len(nomes_resultados) < 2:
                    nomes_resultados = ['Casa', 'Fora']  # Padrão se não tiver informação
                    
                oportunidade = {
                    "tipo_mercado": tipo_mercado,
                    "oportunidade": True,
                    "soma_probabilidades_implicitas": soma_probabilidades,
                    "lucro_percentual_garantido": lucro_percentual,
                    "detalhes_apostas": [
                        {"casa": item.get('casa_1', ''), "resultado": nomes_resultados[0], "odd": odds_r1, 
                         "stake_sugerido": stake1, "retorno_individual": stake1 * odds_r1},
                        {"casa": item.get('casa_2', ''), "resultado": nomes_resultados[1], "odd": odds_r2, 
                         "stake_sugerido": stake2, "retorno_individual": stake2 * odds_r2}
                    ],
                    "investimento_total_sugerido": investimento_real_total,
                    "retorno_garantido": retorno_garantido,
                    "id_evento": str(item.get('_id', '')),
                    "descricao_evento": item.get('evento', item.get('times', '')),
                    "esporte": item.get('esporte', ''),
                    "liga": item.get('liga', ''),
                    "timestamp": time.time(),
                    "data_hora_evento": item.get('data_hora', ''),
                    "data_extracao": item.get('data_extracao', datetime.now())
                }
                oportunidades.append(oportunidade)
            
            elif tipo_mercado == "3-vias":
                stake3 = retorno_garantido / odds_r3
                investimento_real_total = stake1 + stake2 + stake3
                nomes_resultados = item.get('linha', 'Casa/Empate/Fora').split('/')
                if len(nomes_resultados) < 3:
                    nomes_resultados = ['Casa', 'Empate', 'Fora']  # Padrão se não tiver informação
                
                oportunidade = {
                    "tipo_mercado": tipo_mercado,
                    "oportunidade": True,
                    "soma_probabilidades_implicitas": soma_probabilidades,
                    "lucro_percentual_garantido": lucro_percentual,
                    "detalhes_apostas": [
                        {"casa": item.get('casa_1', ''), "resultado": nomes_resultados[0], "odd": odds_r1, 
                         "stake_sugerido": stake1, "retorno_individual": stake1 * odds_r1},
                        {"casa": item.get('casa_2', ''), "resultado": nomes_resultados[1], "odd": odds_r2, 
                         "stake_sugerido": stake2, "retorno_individual": stake2 * odds_r2},
                        {"casa": item.get('casa_3', ''), "resultado": nomes_resultados[2], "odd": odds_r3, 
                         "stake_sugerido": stake3, "retorno_individual": stake3 * odds_r3}
                    ],
                    "investimento_total_sugerido": investimento_real_total,
                    "retorno_garantido": retorno_garantido,
                    "id_evento": str(item.get('_id', '')),
                    "descricao_evento": item.get('evento', item.get('times', '')),
                    "esporte": item.get('esporte', ''),
                    "liga": item.get('liga', ''),
                    "timestamp": time.time(),
                    "data_hora_evento": item.get('data_hora', ''),
                    "data_extracao": item.get('data_extracao', datetime.now())
                }
                oportunidades.append(oportunidade)
                
    return oportunidades

def mostrar_detalhes_oportunidade(oportunidade):
    """Mostra detalhes de uma oportunidade específica"""
    st.markdown(f"<h3 style='color:{COR_SECUNDARIA_VERDE};'>🎯 {oportunidade['descricao_evento']} ({oportunidade['esporte']} - {oportunidade['liga']})</h3>", unsafe_allow_html=True)
    
    # Informações de horário e data
    if 'data_hora_evento' in oportunidade and oportunidade['data_hora_evento']:
        st.markdown(f"**Data e Hora do Evento:** {oportunidade['data_hora_evento']}")
    
    # Informações principais
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Lucro Garantido:** <span class='lucro-destaque'>{oportunidade['lucro_percentual_garantido']:.2f}%</span>", unsafe_allow_html=True)
        st.markdown(f"**Investimento Sugerido:** R$ {oportunidade['investimento_total_sugerido']:.2f}")
    with col2:
        st.markdown(f"**Retorno Garantido:** R$ {oportunidade['retorno_garantido']:.2f}")
        st.markdown(f"**Soma Probabilidades:** {oportunidade['soma_probabilidades_implicitas']:.4f}")
    
    # Detalhes das apostas
    st.markdown("**Detalhes das Apostas Sugeridas:**")
    detalhes_df = pd.DataFrame(oportunidade['detalhes_apostas'])
    detalhes_df_display = detalhes_df[['casa', 'resultado', 'odd', 'stake_sugerido', 'retorno_individual']]
    detalhes_df_display['stake_sugerido'] = detalhes_df_display['stake_sugerido'].map(lambda x: f"R$ {x:.2f}")
    detalhes_df_display['retorno_individual'] = detalhes_df_display['retorno_individual'].map(lambda x: f"R$ {x:.2f}")
    detalhes_df_display.rename(columns={'casa': 'Casa', 'resultado': 'Apostar em', 'odd': 'Odd', 'stake_sugerido': 'Stake', 'retorno_individual': 'Retorno'}, inplace=True)
    st.table(detalhes_df_display.set_index('Casa'))
    
    # Adicionar informações de tempo de extração
    if 'data_extracao' in oportunidade and oportunidade['data_extracao']:
        st.caption(f"Dados extraídos em: {oportunidade['data_extracao']}")
    
    st.divider()

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

st.caption("Versão com Integração MongoDB - Dados de arbitragem em tempo real")

# Sidebar para configurações
st.sidebar.markdown(f"<h2 style='color:{COR_TEXTO_BRANCO};'>⚙️ Configurações</h2>", unsafe_allow_html=True)
investimento_usuario = st.sidebar.number_input("Valor Total para Investir (R$):", min_value=10.0, value=100.0, step=10.0)
auto_refresh = st.sidebar.checkbox("Atualização Automática", value=True)
refresh_interval = st.sidebar.slider("Intervalo de Atualização (s):", min_value=5, max_value=60, value=15, step=5)
limiar_lucro = st.sidebar.slider("Limiar Mínimo de Lucro (%):", min_value=0.1, max_value=10.0, value=0.5, step=0.1)

# Configurações MongoDB (colapsado por padrão)
with st.sidebar.expander("Configurações do MongoDB"):
    mongodb_uri = st.text_input("MongoDB URI:", value=MONGODB_URI)
    mongodb_db = st.text_input("MongoDB Database:", value=MONGODB_DATABASE)
    mongodb_collection = st.text_input("MongoDB Collection:", value=MONGODB_COLLECTION)
    
    if st.button("Atualizar Configurações MongoDB"):
        MONGODB_URI = mongodb_uri
        MONGODB_DATABASE = mongodb_db
        MONGODB_COLLECTION = mongodb_collection
        st.success("Configurações do MongoDB atualizadas com sucesso!")

# Botão para atualização manual
col1_main, col2_main = st.columns([3, 1])
with col1_main:
    st.markdown(f"<h3 style='color:{COR_TEXTO_BRANCO};'>Dados de Odds do MongoDB em Tempo Real</h3>", unsafe_allow_html=True)
with col2_main:
    manual_refresh = st.button("Atualizar Agora")

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = 0
if 'odds_data' not in st.session_state:
    st.session_state.odds_data = None
if 'oportunidades' not in st.session_state:
    st.session_state.oportunidades = []

current_time = time.time()
should_refresh = manual_refresh or (auto_refresh and (current_time - st.session_state.last_refresh) > refresh_interval)

if should_refresh:
    with st.spinner("Carregando dados de surebets do MongoDB..."):
        try:
            # Obter dados do MongoDB
            dados_mongodb = obter_dados_mongodb()
            if dados_mongodb:
                # Processar os dados em oportunidades
                st.session_state.oportunidades = processar_oportunidades_mongodb(dados_mongodb, investimento_usuario)
                st.session_state.last_refresh = current_time
                st.success(f"Dados atualizados com sucesso! {len(st.session_state.oportunidades)} oportunidades encontradas.")
            else:
                st.warning("Não foi possível obter dados do MongoDB ou não há dados disponíveis.")
        except Exception as e:
            st.error(f"Erro ao processar dados: {e}")
    st.caption(f"Última atualização: {datetime.fromtimestamp(current_time).strftime('%H:%M:%S')}")

st.markdown(f"<h2 style='color:{COR_TEXTO_BRANCO};'>🚨 Oportunidades de Arbitragem</h2>", unsafe_allow_html=True)
if st.session_state.oportunidades:
    oportunidades_filtradas = [op for op in st.session_state.oportunidades if op["lucro_percentual_garantido"] >= limiar_lucro]
    if oportunidades_filtradas:
        # Criar seletor de oportunidade
        opcoes_oportunidades = [f"{op['descricao_evento']} - {op['lucro_percentual_garantido']:.2f}% ({op['esporte']})" for op in oportunidades_filtradas]
        indice_selecionado = st.selectbox("Selecione uma oportunidade para ver detalhes:", 
                                      options=range(len(opcoes_oportunidades)),
                                      format_func=lambda i: opcoes_oportunidades[i])
        
        # Mostrar detalhes da oportunidade selecionada
        mostrar_detalhes_oportunidade(oportunidades_filtradas[indice_selecionado])
        
        # Opção para mostrar todas as oportunidades
        if st.checkbox("Mostrar todas as oportunidades"):
            for op in oportunidades_filtradas:
                mostrar_detalhes_oportunidade(op)
    else:
        st.info(f"Nenhuma oportunidade de arbitragem encontrada com lucro acima de {limiar_lucro}%.")
else:
    st.warning("Aguardando dados. Clique em 'Atualizar Agora' ou aguarde a atualização automática.")

st.markdown(f"<h2 style='color:{COR_TEXTO_BRANCO};'>📊 Visualização de Dados de MongoDB</h2>", unsafe_allow_html=True)

# Obter dados brutos do MongoDB para visualização
with st.expander("Dados de Oportunidades no MongoDB"):
    try:
        dados_mongodb_raw = obter_dados_mongodb()
        if dados_mongodb_raw:
            # Converter para DataFrame para visualização
            df_mongo = pd.DataFrame(dados_mongodb_raw)
            
            # Selecionar colunas relevantes para exibição
            colunas_exibir = ['esporte', 'liga', 'evento', 'data_hora', 'linha', 
                            'odd_1', 'casa_1', 'odd_2', 'casa_2', 'odd_3', 'casa_3', 
                            'lucro_garantido', 'lucro_percentual']
            
            colunas_disponiveis = [col for col in colunas_exibir if col in df_mongo.columns]
            if colunas_disponiveis:
                df_display = df_mongo[colunas_disponiveis].copy()
                
                # Filtrar por esporte
                esportes_disponiveis = sorted(df_display['esporte'].unique().tolist())
                if esportes_disponiveis:
                    esporte_filtro = st.selectbox("Filtrar por Esporte:", options=["Todos"] + esportes_disponiveis)
                    
                    if esporte_filtro != "Todos":
                        df_display = df_display[df_display['esporte'] == esporte_filtro]
                    
                    # Exibir dados
                    st.dataframe(df_display.style.highlight_max(subset=['lucro_percentual'], 
                                                            props=f'color:{COR_TEXTO_CINZA_ESCURO}; background-color:{COR_DESTAQUE_DOURADO};'),
                                use_container_width=True)
                    
                    # Mostrar estatísticas
                    st.markdown(f"**Estatísticas de Lucro por Esporte:**")
                    df_stats = df_mongo.groupby('esporte')['lucro_percentual'].agg(['mean', 'max', 'count']).reset_index()
                    df_stats.columns = ['Esporte', 'Lucro Médio (%)', 'Lucro Máximo (%)', 'Quantidade de Oportunidades']
                    df_stats['Lucro Médio (%)'] = df_stats['Lucro Médio (%)'].map(lambda x: f"{x:.2f}%")
                    df_stats['Lucro Máximo (%)'] = df_stats['Lucro Máximo (%)'].map(lambda x: f"{x:.2f}%")
                    st.table(df_stats.set_index('Esporte'))
                    
                    # Gráfico de distribuição de lucro
                    if not df_mongo.empty and 'lucro_percentual' in df_mongo.columns:
                        st.markdown("**Distribuição de Lucro Percentual:**")
                        hist_data = df_mongo['lucro_percentual'].dropna()
                        if not hist_data.empty:
                            st.bar_chart(hist_data.value_counts(bins=10).sort_index())
                else:
                    st.warning("Não há dados de esportes disponíveis.")
            else:
                st.warning("Estrutura de dados no MongoDB não corresponde ao formato esperado.")
        else:
            st.warning("Não há dados disponíveis no MongoDB.")
    except Exception as e:
        st.error(f"Erro ao processar dados do MongoDB para visualização: {e}")

st.markdown("<hr style='border: 1px solid #2A7A7B;'>", unsafe_allow_html=True)
st.caption(f"OddsHunter v2.0 - MongoDB Integration - Desenvolvido por MDC. Dados em tempo real.")

# Adicionar informações sobre o deploy permanente
st.sidebar.markdown("---")
st.sidebar.markdown(f"<h3 style='color:{COR_TEXTO_BRANCO};'>Sobre este Deploy</h3>", unsafe_allow_html=True)
st.sidebar.markdown("Esta é uma versão 2.0 do OddsHunter com integração ao MongoDB.")
st.sidebar.markdown("Dados de oportunidades de arbitragem em tempo real.")
